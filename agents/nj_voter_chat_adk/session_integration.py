"""
Integration layer between ADK agent and backend session services
"""
import os
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

class SessionIntegration:
    def __init__(self):
        self.backend_url = os.getenv("BACKEND_URL", "http://localhost:8080")
        self.session_service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the appropriate session service"""
        try:
            import sys
            sys.path.append("../../backend")
            
            from core.config import settings
            
            if settings.USE_FIRESTORE_FOR_CHAT:
                from services.firestore_chat_service import get_firestore_chat_service
                self.session_service = get_firestore_chat_service()
                print("Using Firestore for agent session persistence")
            else:
                from services.chat_session_service import get_chat_session_service
                self.session_service = get_chat_session_service()
                print("Using BigQuery for agent session persistence")
        except Exception as e:
            print(f"Failed to initialize session service: {e}")
            self.session_service = None
    
    async def create_or_get_session(self, user_id: str, user_email: str, session_id: Optional[str] = None) -> str:
        """Create a new session or get existing one"""
        if not self.session_service:
            return f"memory_session_{int(datetime.now().timestamp())}"
        
        try:
            if session_id:
                session = await self.session_service.get_session(session_id, user_id)
                if session:
                    return session_id
            
            session = await self.session_service.create_session(
                user_id=user_id,
                user_email=user_email,
                session_name=f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            return session.session_id
        except Exception as e:
            print(f"Error managing session: {e}")
            return f"fallback_session_{int(datetime.now().timestamp())}"
    
    async def add_message(self, session_id: str, user_id: str, message_type: str, message_text: str):
        """Add a message to the session"""
        if not self.session_service:
            return
        
        try:
            await self.session_service.add_message(
                session_id=session_id,
                user_id=user_id,
                message_type=message_type,
                message_text=message_text
            )
        except Exception as e:
            print(f"Error adding message to session: {e}")
    
    async def get_session_history(self, session_id: str, user_id: str) -> list:
        """Get session message history"""
        if not self.session_service:
            return []
        
        try:
            messages = await self.session_service.get_session_messages(session_id, user_id)
            # Convert messages to the expected format
            history = []
            for msg in messages.messages:
                history.append({"role": msg.message_type, "content": msg.message_text})
            return history
        except Exception as e:
            print(f"Error getting session history: {e}")
            return []
