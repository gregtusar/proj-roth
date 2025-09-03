"""
Unified session management system for consistent session ID handling across all layers
"""
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import hashlib
import json


class UnifiedSession:
    """
    Single source of truth for session IDs across the application.
    Manages the relationship between chat sessions, ADK sessions, and WebSocket connections.
    """
    
    def __init__(self, chat_session_id: str, user_id: str, model_id: Optional[str] = None):
        """
        Initialize a unified session.
        
        Args:
            chat_session_id: The primary chat session ID (from Firestore)
            user_id: The user ID who owns this session
            model_id: The LLM model being used (can change during session)
        """
        self.chat_id = chat_session_id
        self.user_id = user_id
        self.model_id = model_id or "gemini-2.0-flash-exp"
        self.created_at = datetime.utcnow()
        self.last_accessed = datetime.utcnow()
        
        # Generate derived IDs consistently
        self.adk_id = f"adk_{chat_session_id}"
        self._websocket_sids = set()  # Can have multiple WebSocket connections
        
    def get_adk_session_id(self) -> str:
        """Get the ADK session ID for this chat session"""
        return self.adk_id
    
    def get_agent_cache_key(self) -> str:
        """
        Generate a unique cache key for the agent instance.
        This key ensures proper agent instance management per user/session/model combination.
        """
        # Include user_id to prevent cross-user cache pollution
        # Include model_id to handle model switching
        # Include date to allow daily cache refresh
        key_parts = [
            self.user_id,
            self.chat_id,
            self.model_id,
            self.created_at.date().isoformat()
        ]
        return ":".join(key_parts)
    
    def get_short_cache_key(self) -> Tuple[str, str]:
        """
        Get a tuple-based cache key for backward compatibility.
        Returns (session_id, model_id) tuple.
        """
        return (self.chat_id, self.model_id)
    
    def add_websocket_connection(self, sid: str):
        """Register a WebSocket connection with this session"""
        self._websocket_sids.add(sid)
        self.last_accessed = datetime.utcnow()
    
    def remove_websocket_connection(self, sid: str):
        """Remove a WebSocket connection from this session"""
        self._websocket_sids.discard(sid)
    
    def has_active_connections(self) -> bool:
        """Check if this session has any active WebSocket connections"""
        return len(self._websocket_sids) > 0
    
    def update_model(self, new_model_id: str) -> str:
        """
        Update the model for this session and return the new cache key.
        This invalidates the old agent cache.
        """
        old_cache_key = self.get_agent_cache_key()
        self.model_id = new_model_id
        self.last_accessed = datetime.utcnow()
        new_cache_key = self.get_agent_cache_key()
        return new_cache_key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization"""
        return {
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "model_id": self.model_id,
            "adk_id": self.adk_id,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "active_connections": len(self._websocket_sids),
            "websocket_sids": list(self._websocket_sids)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedSession":
        """Create a UnifiedSession from a dictionary"""
        session = cls(
            chat_session_id=data["chat_id"],
            user_id=data["user_id"],
            model_id=data.get("model_id")
        )
        if "created_at" in data:
            session.created_at = datetime.fromisoformat(data["created_at"])
        if "last_accessed" in data:
            session.last_accessed = datetime.fromisoformat(data["last_accessed"])
        if "websocket_sids" in data:
            session._websocket_sids = set(data["websocket_sids"])
        return session


class SessionManager:
    """
    Centralized session manager to handle all session operations.
    This replaces the scattered session handling throughout the codebase.
    """
    
    def __init__(self):
        # In-memory session store (could be replaced with Redis for scaling)
        self._sessions: Dict[str, UnifiedSession] = {}
        # Reverse lookup from WebSocket SID to session
        self._sid_to_session: Dict[str, str] = {}
        # User to sessions mapping for quick lookup
        self._user_sessions: Dict[str, set] = {}
    
    def create_session(self, chat_session_id: str, user_id: str, model_id: Optional[str] = None) -> UnifiedSession:
        """Create and register a new unified session"""
        session = UnifiedSession(chat_session_id, user_id, model_id)
        self._sessions[chat_session_id] = session
        
        # Update user sessions index
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = set()
        self._user_sessions[user_id].add(chat_session_id)
        
        return session
    
    def get_session(self, chat_session_id: str) -> Optional[UnifiedSession]:
        """Get a session by chat session ID"""
        session = self._sessions.get(chat_session_id)
        if session:
            session.last_accessed = datetime.utcnow()
        return session
    
    def get_session_by_websocket(self, sid: str) -> Optional[UnifiedSession]:
        """Get a session by WebSocket SID"""
        chat_id = self._sid_to_session.get(sid)
        if chat_id:
            return self.get_session(chat_id)
        return None
    
    def register_websocket(self, chat_session_id: str, sid: str):
        """Register a WebSocket connection with a session"""
        session = self.get_session(chat_session_id)
        if session:
            session.add_websocket_connection(sid)
            self._sid_to_session[sid] = chat_session_id
    
    def unregister_websocket(self, sid: str):
        """Remove a WebSocket connection"""
        chat_id = self._sid_to_session.pop(sid, None)
        if chat_id:
            session = self.get_session(chat_id)
            if session:
                session.remove_websocket_connection(sid)
    
    def update_session_model(self, chat_session_id: str, new_model_id: str) -> Optional[str]:
        """
        Update the model for a session and return the new cache key.
        Returns None if session doesn't exist.
        """
        session = self.get_session(chat_session_id)
        if session:
            return session.update_model(new_model_id)
        return None
    
    def get_user_sessions(self, user_id: str) -> list[UnifiedSession]:
        """Get all sessions for a user"""
        session_ids = self._user_sessions.get(user_id, set())
        sessions = []
        for sid in session_ids:
            session = self.get_session(sid)
            if session:
                sessions.append(session)
        return sorted(sessions, key=lambda s: s.last_accessed, reverse=True)
    
    def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Remove sessions that haven't been accessed in the specified time"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        sessions_to_remove = []
        
        for chat_id, session in self._sessions.items():
            if session.last_accessed < cutoff_time and not session.has_active_connections():
                sessions_to_remove.append(chat_id)
        
        for chat_id in sessions_to_remove:
            session = self._sessions.pop(chat_id, None)
            if session:
                # Clean up user index
                if session.user_id in self._user_sessions:
                    self._user_sessions[session.user_id].discard(chat_id)
        
        return len(sessions_to_remove)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about current sessions"""
        total_sessions = len(self._sessions)
        active_sessions = sum(1 for s in self._sessions.values() if s.has_active_connections())
        total_users = len(self._user_sessions)
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "total_users": total_users,
            "websocket_connections": len(self._sid_to_session),
            "sessions_per_user": {
                user_id: len(sessions) 
                for user_id, sessions in self._user_sessions.items()
            }
        }


# Global session manager instance
_session_manager = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


# Import timedelta for cleanup
from datetime import timedelta