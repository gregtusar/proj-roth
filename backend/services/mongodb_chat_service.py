"""
MongoDB-based chat session service for better performance and reliability
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError
import os

from models.chat_session import ChatSession, ChatMessage as Message


class MongoDBChatService:
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize MongoDB connection"""
        # Use provided connection string or environment variable or default to local
        self.connection_string = connection_string or os.getenv(
            "MONGODB_URI", 
            "mongodb://localhost:27017/nj_voter_chat"
        )
        
        try:
            # Initialize connection with a short timeout for local development
            self.client = AsyncIOMotorClient(
                self.connection_string,
                serverSelectionTimeoutMS=2000  # 2 second timeout
            )
            self.db = self.client.nj_voter_chat
            self.sessions_collection = self.db.chat_sessions
            self.messages_collection = self.db.chat_messages
            
            # Create indexes for better performance
            self._create_indexes()
            self.connected = True
            print("MongoDB chat service initialized successfully")
        except Exception as e:
            print(f"Warning: Could not connect to MongoDB: {e}")
            print("Chat persistence will fall back to BigQuery")
            self.connected = False
            self.client = None
    
    def _create_indexes(self):
        """Create database indexes for optimal performance"""
        # Sessions indexes
        self.sessions_collection.create_index("user_id")
        self.sessions_collection.create_index("session_id", unique=True)
        self.sessions_collection.create_index([("user_id", 1), ("updated_at", DESCENDING)])
        
        # Messages indexes  
        self.messages_collection.create_index("session_id")
        self.messages_collection.create_index("message_id", unique=True)
        self.messages_collection.create_index([("session_id", 1), ("sequence_number", 1)])
    
    async def create_session(
        self,
        user_id: str,
        user_email: str,
        session_name: Optional[str] = None,
        first_message: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        if not self.connected:
            raise RuntimeError("MongoDB is not connected")
        session_id = str(uuid.uuid4())
        
        # Use first message as session name if not provided
        if not session_name and first_message:
            session_name = first_message[:50] + "..." if len(first_message) > 50 else first_message
        elif not session_name:
            session_name = f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        session_doc = {
            "session_id": session_id,
            "user_id": user_id,
            "user_email": user_email,
            "session_name": session_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "message_count": 0,
            "metadata": {}
        }
        
        try:
            await self.sessions_collection.insert_one(session_doc)
        except DuplicateKeyError:
            # Unlikely but handle duplicate session_id
            return await self.create_session(user_id, user_email, session_name, first_message)
        
        return ChatSession(**session_doc)
    
    async def get_user_sessions(
        self, 
        user_id: str,
        limit: int = 100
    ) -> List[ChatSession]:
        """Get all sessions for a user, ordered by most recent"""
        cursor = self.sessions_collection.find(
            {"user_id": user_id, "is_active": True}
        ).sort("updated_at", DESCENDING).limit(limit)
        
        sessions = []
        async for doc in cursor:
            sessions.append(ChatSession(**doc))
        
        return sessions
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific session"""
        doc = await self.sessions_collection.find_one({
            "session_id": session_id,
            "user_id": user_id,
            "is_active": True
        })
        
        if doc:
            return ChatSession(**doc)
        return None
    
    async def update_session_name(
        self,
        session_id: str,
        user_id: str,
        new_name: str
    ) -> bool:
        """Update session name"""
        result = await self.sessions_collection.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "session_name": new_name,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Soft delete a session"""
        result = await self.sessions_collection.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "is_active": False,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return result.modified_count > 0
    
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        message_type: str,
        message_text: str,
        sequence_number: Optional[int] = None
    ) -> Message:
        """Add a message to a session"""
        # Get next sequence number if not provided
        if sequence_number is None:
            sequence_number = await self._get_next_sequence_number(session_id)
        
        message_id = str(uuid.uuid4())
        
        message_doc = {
            "message_id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "message_type": message_type,
            "message_text": message_text,
            "timestamp": datetime.utcnow(),
            "sequence_number": sequence_number,
            "metadata": {}
        }
        
        # Insert message
        await self.messages_collection.insert_one(message_doc)
        
        # Update session activity and message count
        await self.sessions_collection.update_one(
            {"session_id": session_id},
            {
                "$set": {"updated_at": datetime.utcnow()},
                "$inc": {"message_count": 1}
            }
        )
        
        return Message(**message_doc)
    
    async def get_session_messages(
        self,
        session_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """Get all messages for a session"""
        # Verify session ownership
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session {session_id} not found or access denied")
        
        # Get messages
        cursor = self.messages_collection.find(
            {"session_id": session_id}
        ).sort("sequence_number", 1)
        
        messages = []
        async for doc in cursor:
            messages.append(Message(**doc))
        
        return {
            "session": session,
            "messages": messages
        }
    
    async def _get_next_sequence_number(self, session_id: str) -> int:
        """Get the next sequence number for a session"""
        # Find the highest sequence number
        doc = await self.messages_collection.find_one(
            {"session_id": session_id},
            sort=[("sequence_number", DESCENDING)]
        )
        
        if doc:
            return doc["sequence_number"] + 1
        return 0
    
    async def search_sessions(
        self,
        user_id: str,
        query: str,
        limit: int = 20
    ) -> List[ChatSession]:
        """Search user's sessions by name or content"""
        # Search in session names
        cursor = self.sessions_collection.find(
            {
                "user_id": user_id,
                "is_active": True,
                "$or": [
                    {"session_name": {"$regex": query, "$options": "i"}},
                    # Could also search in messages if needed
                ]
            }
        ).sort("updated_at", DESCENDING).limit(limit)
        
        sessions = []
        async for doc in cursor:
            sessions.append(ChatSession(**doc))
        
        return sessions
    
    async def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's chat sessions"""
        pipeline = [
            {"$match": {"user_id": user_id, "is_active": True}},
            {
                "$group": {
                    "_id": None,
                    "total_sessions": {"$sum": 1},
                    "total_messages": {"$sum": "$message_count"},
                    "avg_messages_per_session": {"$avg": "$message_count"}
                }
            }
        ]
        
        cursor = self.sessions_collection.aggregate(pipeline)
        stats = await cursor.to_list(1)
        
        if stats:
            return stats[0]
        return {
            "total_sessions": 0,
            "total_messages": 0,
            "avg_messages_per_session": 0
        }


# Singleton instance
_mongodb_service = None

def get_mongodb_chat_service() -> MongoDBChatService:
    """Get or create the MongoDB chat service singleton"""
    global _mongodb_service
    if _mongodb_service is None:
        _mongodb_service = MongoDBChatService()
    return _mongodb_service