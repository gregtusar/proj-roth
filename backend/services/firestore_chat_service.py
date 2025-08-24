"""
Google Firestore-based chat session service for GCP-native NoSQL persistence
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from google.cloud import firestore
from google.cloud.firestore_v1 import AsyncClient
import asyncio
import os

from models.chat_session import ChatSession, ChatMessage as Message


class FirestoreChatService:
    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore connection"""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        
        try:
            # Initialize BOTH sync and async clients
            # Sync client is more reliable and we'll use it as primary
            self.sync_client = firestore.Client(project=self.project_id)
            
            # Also try to create async client for future use
            try:
                self.client = firestore.AsyncClient(project=self.project_id)
                self.has_async = True
            except Exception as e:
                print(f"AsyncClient initialization failed ({e}), will use sync client only")
                self.client = None
                self.has_async = False
            
            # Use sync client as primary (more reliable)
            self.is_async = False  # Default to sync for reliability
            
            # Collection references - use sync by default
            self.sessions_collection = self.sync_client.collection('chat_sessions')
            self.messages_collection = self.sync_client.collection('chat_messages')
            
            self.connected = True
            print(f"Firestore chat service initialized for project: {self.project_id} (primary=sync, async_available={self.has_async})")
        except Exception as e:
            print(f"Warning: Could not connect to Firestore: {e}")
            self.connected = False
            self.client = None
            self.sync_client = None
    
    async def create_session(
        self,
        user_id: str,
        user_email: str,
        session_name: Optional[str] = None,
        first_message: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        if not self.connected:
            raise RuntimeError("Firestore is not connected")
            
        session_id = str(uuid.uuid4())
        
        # Use first message as session name if not provided
        if not session_name and first_message:
            session_name = first_message[:50] + "..." if len(first_message) > 50 else first_message
        elif not session_name:
            session_name = f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        session_data = {
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
        
        # Create document with session_id as document ID
        # Use sync client for reliability
        try:
            # Always use sync client for session creation (most reliable)
            self.sync_client.collection('chat_sessions').document(session_id).set(session_data)
            print(f"Successfully created session: {session_id}")
        except Exception as e:
            print(f"Error creating session in Firestore: {e}")
            raise
        
        return ChatSession(**session_data)
    
    async def get_user_sessions(
        self, 
        user_id: str,
        limit: int = 100
    ) -> List[ChatSession]:
        """Get all sessions for a user, ordered by most recent"""
        # Use sync client with asyncio.to_thread for async compatibility
        def _get_sessions():
            query = (
                self.sync_client.collection('chat_sessions')
                .where(filter=firestore.FieldFilter("user_id", "==", user_id))
                .where(filter=firestore.FieldFilter("is_active", "==", True))
                .order_by("updated_at", direction=firestore.Query.DESCENDING)
                .limit(limit)
            )
            
            sessions = []
            for doc in query.stream():
                session_data = doc.to_dict()
                sessions.append(ChatSession(**session_data))
            
            return sessions
        
        # Run sync operation in thread pool
        return await asyncio.to_thread(_get_sessions)
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[ChatSession]:
        """Get a specific session"""
        def _get_session():
            doc_ref = self.sync_client.collection('chat_sessions').document(session_id)
            doc = doc_ref.get()
            
            if doc.exists:
                session_data = doc.to_dict()
                # Verify ownership
                if session_data.get("user_id") == user_id and session_data.get("is_active"):
                    return ChatSession(**session_data)
            
            return None
        
        # Run sync operation in thread pool
        return await asyncio.to_thread(_get_session)
    
    async def update_session_name(
        self,
        session_id: str,
        user_id: str,
        new_name: str
    ) -> bool:
        """Update session name"""
        doc_ref = self.sessions_collection.document(session_id)
        
        # First verify ownership
        doc = await doc_ref.get()
        if not doc.exists:
            return False
            
        session_data = doc.to_dict()
        if session_data.get("user_id") != user_id:
            return False
        
        # Update the session
        await doc_ref.update({
            "session_name": new_name,
            "updated_at": datetime.utcnow()
        })
        
        return True
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Soft delete a session"""
        doc_ref = self.sessions_collection.document(session_id)
        
        # First verify ownership
        doc = await doc_ref.get()
        if not doc.exists:
            return False
            
        session_data = doc.to_dict()
        if session_data.get("user_id") != user_id:
            return False
        
        # Soft delete
        await doc_ref.update({
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        return True
    
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
        
        message_data = {
            "message_id": message_id,
            "session_id": session_id,
            "user_id": user_id,
            "message_type": message_type,
            "message_text": message_text,
            "timestamp": datetime.utcnow(),
            "sequence_number": sequence_number,
            "metadata": {}
        }
        
        def _add_message():
            # Create message document
            self.sync_client.collection('chat_messages').document(message_id).set(message_data)
            
            # Update session activity using a transaction
            session_ref = self.sync_client.collection('chat_sessions').document(session_id)
            
            @firestore.transactional
            def update_session(transaction):
                session_doc = session_ref.get(transaction=transaction)
                if session_doc.exists:
                    current_count = session_doc.to_dict().get("message_count", 0)
                    transaction.update(session_ref, {
                        "updated_at": datetime.utcnow(),
                        "message_count": current_count + 1
                    })
            
            transaction = self.sync_client.transaction()
            update_session(transaction)
        
        # Run sync operation in thread pool
        await asyncio.to_thread(_add_message)
        
        return Message(**message_data)
    
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
        
        def _get_messages():
            # Get messages
            query = self.sync_client.collection('chat_messages').where(
                filter=firestore.FieldFilter("session_id", "==", session_id)
            )
            
            messages = []
            for doc in query.stream():
                message_data = doc.to_dict()
                messages.append(Message(**message_data))
            
            # Sort by sequence number in memory to avoid index requirement
            messages.sort(key=lambda m: m.sequence_number)
            
            return messages
        
        # Run sync operation in thread pool
        messages = await asyncio.to_thread(_get_messages)
        
        return {
            "session": session,
            "messages": messages
        }
    
    async def _get_next_sequence_number(self, session_id: str) -> int:
        """Get the next sequence number for a session"""
        def _get_max_sequence():
            # Get all messages for this session and find the highest sequence number
            # This avoids the need for a composite index
            query = self.sync_client.collection('chat_messages').where(
                filter=firestore.FieldFilter("session_id", "==", session_id)
            )
            
            max_sequence = -1
            for doc in query.stream():
                msg_data = doc.to_dict()
                if msg_data.get("sequence_number", 0) > max_sequence:
                    max_sequence = msg_data["sequence_number"]
            
            return max_sequence + 1
        
        # Run sync operation in thread pool
        return await asyncio.to_thread(_get_max_sequence)
    
    async def search_sessions(
        self,
        user_id: str,
        query_text: str,
        limit: int = 20
    ) -> List[ChatSession]:
        """Search user's sessions by name"""
        # Note: Firestore doesn't support full-text search natively
        # For better search, consider using Algolia or Elasticsearch
        # This implementation does a simple prefix search on session names
        
        query = (
            self.sessions_collection
            .where(filter=firestore.FieldFilter("user_id", "==", user_id))
            .where(filter=firestore.FieldFilter("is_active", "==", True))
            .order_by("session_name")
            .start_at([query_text])
            .end_at([query_text + "\uf8ff"])  # Unicode character to match prefixes
            .limit(limit)
        )
        
        sessions = []
        async for doc in query.stream():
            session_data = doc.to_dict()
            sessions.append(ChatSession(**session_data))
        
        return sessions
    
    async def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's chat sessions"""
        # Get all active sessions for the user
        query = (
            self.sessions_collection
            .where(filter=firestore.FieldFilter("user_id", "==", user_id))
            .where(filter=firestore.FieldFilter("is_active", "==", True))
        )
        
        total_sessions = 0
        total_messages = 0
        
        async for doc in query.stream():
            session_data = doc.to_dict()
            total_sessions += 1
            total_messages += session_data.get("message_count", 0)
        
        avg_messages = total_messages / total_sessions if total_sessions > 0 else 0
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "avg_messages_per_session": avg_messages
        }
    
    async def cleanup_old_sessions(self, user_id: str, days: int = 30):
        """Clean up old inactive sessions"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = (
            self.sessions_collection
            .where(filter=firestore.FieldFilter("user_id", "==", user_id))
            .where(filter=firestore.FieldFilter("is_active", "==", False))
            .where(filter=firestore.FieldFilter("updated_at", "<", cutoff_date))
        )
        
        batch = self.client.batch()
        count = 0
        
        async for doc in query.stream():
            batch.delete(doc.reference)
            count += 1
            
            # Commit batch every 500 documents
            if count % 500 == 0:
                await batch.commit()
                batch = self.client.batch()
        
        # Commit remaining
        if count % 500 != 0:
            await batch.commit()
        
        return count


# Singleton instance
_firestore_service = None

def get_firestore_chat_service() -> FirestoreChatService:
    """Get or create the Firestore chat service singleton"""
    global _firestore_service
    if _firestore_service is None:
        _firestore_service = FirestoreChatService()
    return _firestore_service