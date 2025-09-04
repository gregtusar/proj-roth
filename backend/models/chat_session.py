from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatSession(BaseModel):
    session_id: str
    user_id: str
    user_email: str
    session_name: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    is_public: bool = False  # New field for public sharing
    message_count: int = 0
    last_sequence_number: int = -1
    model_id: Optional[str] = "gemini-2.0-flash-exp"  # Add model_id field
    metadata: Optional[dict] = None

class ChatMessage(BaseModel):
    message_id: str
    session_id: str
    user_id: str
    message_type: str  # 'user' or 'assistant'
    message_text: str
    timestamp: datetime
    sequence_number: int
    metadata: Optional[dict] = None

class CreateSessionRequest(BaseModel):
    session_name: Optional[str] = None
    first_message: Optional[str] = None

class UpdateSessionRequest(BaseModel):
    session_name: str

class SessionListResponse(BaseModel):
    sessions: List[ChatSession]

class SessionMessagesResponse(BaseModel):
    session: ChatSession
    messages: List[ChatMessage]
