"""
Request context management using contextvars instead of environment variables.
This provides thread-safe context passing between layers.
"""
from contextvars import ContextVar
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging

# Create context variables for request-scoped data
_request_context: ContextVar[Optional['RequestContext']] = ContextVar('request_context', default=None)
_user_context: ContextVar[Optional['UserContext']] = ContextVar('user_context', default=None)

logger = logging.getLogger(__name__)


@dataclass
class UserContext:
    """User-specific context information"""
    user_id: str
    user_email: str
    custom_prompt: Optional[str] = None
    preferences: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}


@dataclass
class SessionContext:
    """Session-specific context information"""
    session_id: str
    model_id: str
    client_type: str = "react"
    verbose_mode: bool = False
    
    def get_adk_session_id(self) -> str:
        """Generate ADK session ID from chat session ID"""
        return f"adk_{self.session_id}"


@dataclass
class RequestContext:
    """Complete request context combining user and session info"""
    user: UserContext
    session: SessionContext
    request_id: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "user_id": self.user.user_id,
            "user_email": self.user.user_email,
            "session_id": self.session.session_id,
            "model_id": self.session.model_id,
            "client_type": self.session.client_type
        }


class RequestContextManager:
    """
    Context manager for handling request context.
    Replaces environment variable usage with thread-safe context vars.
    """
    
    def __init__(self, request_context: RequestContext):
        self.request_context = request_context
        self.token = None
        self.user_token = None
    
    def __enter__(self):
        """Set the context when entering"""
        self.token = _request_context.set(self.request_context)
        self.user_token = _user_context.set(self.request_context.user)
        
        logger.debug(f"Request context set: {self.request_context.to_dict()}")
        return self.request_context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Reset the context when exiting"""
        if self.token:
            _request_context.reset(self.token)
        if self.user_token:
            _user_context.reset(self.user_token)
        
        logger.debug(f"Request context cleared for: {self.request_context.request_id}")


def get_current_request_context() -> Optional[RequestContext]:
    """Get the current request context"""
    return _request_context.get()


def get_current_user_context() -> Optional[UserContext]:
    """Get the current user context"""
    return _user_context.get()


def get_current_session_context() -> Optional[SessionContext]:
    """Get the current session context"""
    req_ctx = get_current_request_context()
    return req_ctx.session if req_ctx else None


def set_request_context(
    user_id: str,
    user_email: str,
    session_id: str,
    model_id: str,
    request_id: str,
    custom_prompt: Optional[str] = None,
    client_type: str = "react",
    verbose_mode: bool = False
) -> RequestContextManager:
    """
    Create and return a request context manager.
    
    Usage:
        with set_request_context(user_id, user_email, session_id, model_id, request_id) as ctx:
            # Your code here - context is available to all called functions
            pass
    """
    from datetime import datetime
    
    user_ctx = UserContext(
        user_id=user_id,
        user_email=user_email,
        custom_prompt=custom_prompt
    )
    
    session_ctx = SessionContext(
        session_id=session_id,
        model_id=model_id,
        client_type=client_type,
        verbose_mode=verbose_mode
    )
    
    request_ctx = RequestContext(
        user=user_ctx,
        session=session_ctx,
        request_id=request_id,
        timestamp=datetime.utcnow().isoformat()
    )
    
    return RequestContextManager(request_ctx)


# Backward compatibility functions for gradual migration
def get_context_value(key: str, default: Any = None) -> Any:
    """
    Get a value from the current context (backward compatibility).
    Maps old environment variable names to context values.
    """
    ctx = get_current_request_context()
    if not ctx:
        return default
    
    mapping = {
        "VOTER_LIST_USER_ID": ctx.user.user_id,
        "VOTER_LIST_USER_EMAIL": ctx.user.user_email,
        "USER_CUSTOM_PROMPT": ctx.user.custom_prompt,
        "CHAT_SESSION_ID": ctx.session.session_id,
        "ADK_MODEL": ctx.session.model_id,
        "CLIENT_TYPE": ctx.session.client_type
    }
    
    return mapping.get(key, default)


def migrate_from_environ(environ: Dict[str, str]) -> Optional[RequestContext]:
    """
    Create a RequestContext from environment variables (for migration).
    This helps during the transition from env vars to context vars.
    """
    import uuid
    from datetime import datetime
    
    user_id = environ.get("VOTER_LIST_USER_ID")
    if not user_id:
        return None
    
    user_ctx = UserContext(
        user_id=user_id,
        user_email=environ.get("VOTER_LIST_USER_EMAIL", "user@example.com"),
        custom_prompt=environ.get("USER_CUSTOM_PROMPT")
    )
    
    session_ctx = SessionContext(
        session_id=environ.get("CHAT_SESSION_ID", ""),
        model_id=environ.get("ADK_MODEL", "gemini-2.0-flash-exp"),
        client_type=environ.get("CLIENT_TYPE", "react"),
        verbose_mode=environ.get("VERBOSE_MODE", "").lower() == "true"
    )
    
    return RequestContext(
        user=user_ctx,
        session=session_ctx,
        request_id=str(uuid.uuid4()),
        timestamp=datetime.utcnow().isoformat()
    )