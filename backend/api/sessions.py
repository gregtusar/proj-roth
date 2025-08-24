from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from api.auth import get_current_user
from models.chat_session import (
    CreateSessionRequest, UpdateSessionRequest,
    SessionListResponse, SessionMessagesResponse, ChatSession
)
from core.config import settings

router = APIRouter()

def get_session_service():
    """Get the appropriate session service based on configuration"""
    # Try Firestore first (GCP native solution)
    if settings.USE_FIRESTORE_FOR_CHAT:
        try:
            from services.firestore_chat_service import get_firestore_chat_service
            service = get_firestore_chat_service()
            if service.connected:
                print("Using Firestore for chat persistence")
                return service
            else:
                print("Firestore not available, checking other options")
        except Exception as e:
            print(f"Error initializing Firestore service: {e}")
    
    # Try MongoDB if configured
    if settings.USE_MONGODB_FOR_CHAT:
        try:
            from services.mongodb_chat_service import get_mongodb_chat_service
            service = get_mongodb_chat_service()
            if service.connected:
                print("Using MongoDB for chat persistence")
                return service
            else:
                print("MongoDB not available, falling back to BigQuery")
        except Exception as e:
            print(f"Error initializing MongoDB service: {e}")
    
    # Fall back to BigQuery
    print("Using BigQuery for chat persistence (fallback)")
    from services.chat_session_service import get_chat_session_service
    return get_chat_session_service()

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
        result = await service.get_session_messages(session_id, current_user["id"])
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