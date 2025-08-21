from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from api.auth import get_current_user
from services.agent_service import process_message_stream

router = APIRouter()

class SendMessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class Message(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[dict] = None

class ChatSession(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[Message]
    user_id: str

# In-memory storage for demo (replace with Firestore in production)
chat_sessions = {}

@router.post("/send")
async def send_message(
    request: SendMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Send a message to the chat agent
    """
    # Create or get session
    session_id = request.session_id or str(uuid.uuid4())
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "id": session_id,
            "title": request.message[:50],  # Use first 50 chars as title
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "messages": [],
            "user_id": current_user["id"]
        }
    
    # Add user message
    user_message = {
        "id": str(uuid.uuid4()),
        "role": "user",
        "content": request.message,
        "timestamp": datetime.utcnow().isoformat()
    }
    chat_sessions[session_id]["messages"].append(user_message)
    
    # Process through agent (response will be streamed via WebSocket)
    # Here we just return the user message confirmation
    return {
        "session_id": session_id,
        "message": user_message
    }

@router.get("/history")
async def get_chat_history(
    current_user: dict = Depends(get_current_user)
):
    """
    Get user's chat history
    """
    user_sessions = [
        session for session in chat_sessions.values()
        if session["user_id"] == current_user["id"]
    ]
    
    # Sort by updated_at descending
    user_sessions.sort(key=lambda x: x["updated_at"], reverse=True)
    
    return user_sessions

@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific chat session
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    
    # Check if user owns this session
    if session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return session

@router.post("/session/{session_id}/save")
async def save_session(
    session_id: str,
    messages: List[Message],
    current_user: dict = Depends(get_current_user)
):
    """
    Save/update a chat session
    """
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {
            "id": session_id,
            "title": messages[0].content[:50] if messages else "New Chat",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "messages": [],
            "user_id": current_user["id"]
        }
    
    session = chat_sessions[session_id]
    
    # Check ownership
    if session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update messages
    session["messages"] = [msg.dict() for msg in messages]
    session["updated_at"] = datetime.utcnow().isoformat()
    
    return {"message": "Session saved successfully"}

@router.delete("/session/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a chat session
    """
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = chat_sessions[session_id]
    
    # Check ownership
    if session["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del chat_sessions[session_id]
    
    return {"message": "Session deleted successfully"}