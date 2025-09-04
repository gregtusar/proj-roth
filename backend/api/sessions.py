from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.auth import get_current_user
from models.chat_session import (
    CreateSessionRequest, UpdateSessionRequest,
    SessionListResponse, SessionMessagesResponse, ChatSession
)
from pydantic import BaseModel

class UpdateSessionModelRequest(BaseModel):
    model_id: str

router = APIRouter()

def get_session_service():
    """Get the Firestore chat service"""
    from services.firestore_chat_service import get_firestore_chat_service
    service = get_firestore_chat_service()
    if not service.connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not available. Please check Firestore configuration."
        )
    return service

@router.get("/", response_model=SessionListResponse)
async def get_sessions(current_user: dict = Depends(get_current_user)):
    """Get all chat sessions for the current user"""
    service = get_session_service()
    sessions = await service.get_user_sessions(current_user["id"])
    return SessionListResponse(sessions=sessions)

@router.post("/", response_model=ChatSession)
async def create_session(
    request: CreateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new chat session"""
    service = get_session_service()
    session = await service.create_session(
        user_id=current_user["id"],
        user_email=current_user["email"],
        session_name=request.session_name,
        first_message=request.first_message
    )
    return session

@router.get("/{session_id}", response_model=SessionMessagesResponse)
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all messages for a specific session"""
    service = get_session_service()
    try:
        # Allow public access when fetching messages
        result = await service.get_session_messages(session_id, current_user["id"], allow_public=True)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.put("/{session_id}")
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a session (rename)"""
    service = get_session_service()
    success = await service.update_session_name(
        session_id=session_id,
        user_id=current_user["id"],
        new_name=request.session_name
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update session"
        )
    return {"success": True}

@router.patch("/{session_id}/model")
async def update_session_model(
    session_id: str,
    request: UpdateSessionModelRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update the model for a session"""
    service = get_session_service()
    success = await service.update_session_model(
        session_id=session_id,
        user_id=current_user["id"],
        model_id=request.model_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update session model"
        )
    return {"success": True, "model_id": request.model_id}

@router.post("/{session_id}/share")
async def share_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Make a session public"""
    service = get_session_service()
    success = await service.toggle_session_public(
        session_id=session_id,
        user_id=current_user["id"],
        is_public=True
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to share session"
        )
    return {"success": True, "is_public": True}

@router.delete("/{session_id}/share")
async def unshare_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Make a session private"""
    service = get_session_service()
    success = await service.toggle_session_public(
        session_id=session_id,
        user_id=current_user["id"],
        is_public=False
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to unshare session"
        )
    return {"success": True, "is_public": False}

@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a session (soft delete)"""
    service = get_session_service()
    success = await service.delete_session(
        session_id=session_id,
        user_id=current_user["id"]
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete session"
        )
    return {"success": True}