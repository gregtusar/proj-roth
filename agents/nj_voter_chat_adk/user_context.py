"""
User context management for session integration
"""
import os
from typing import Dict, Optional

class UserContext:
    def __init__(self):
        self._context = {}
    
    def set_user_context(self, user_id: str, user_email: str, session_id: Optional[str] = None):
        """Set user context for the current request"""
        self._context = {
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id
        }
        
        os.environ["VOTER_LIST_USER_ID"] = user_id
        os.environ["VOTER_LIST_USER_EMAIL"] = user_email
        if session_id:
            os.environ["CHAT_SESSION_ID"] = session_id
    
    def get_user_context(self) -> Dict[str, str]:
        """Get current user context"""
        return {
            "user_id": self._context.get("user_id", os.environ.get("VOTER_LIST_USER_ID", "default_user")),
            "user_email": self._context.get("user_email", os.environ.get("VOTER_LIST_USER_EMAIL", "user@example.com")),
            "session_id": self._context.get("session_id", os.environ.get("CHAT_SESSION_ID"))
        }
    
    def clear_context(self):
        """Clear user context"""
        self._context = {}
        for key in ["VOTER_LIST_USER_ID", "VOTER_LIST_USER_EMAIL", "CHAT_SESSION_ID"]:
            if key in os.environ:
                del os.environ[key]

# Global instance
user_context = UserContext()
