"""
API endpoints for user settings management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel

from api.auth import get_current_user
from services.user_settings_service import get_user_settings_service

router = APIRouter(prefix="/settings", tags=["settings"])

class CustomPromptRequest(BaseModel):
    custom_prompt: str

class UserSettingsResponse(BaseModel):
    custom_prompt: Optional[str] = None
    user_id: str

@router.get("/", response_model=UserSettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Get user settings including custom prompt"""
    user_id = current_user.get("id")
    
    service = get_user_settings_service()
    settings = await service.get_user_settings(user_id) or {}
    
    return UserSettingsResponse(
        custom_prompt=settings.get("custom_prompt", ""),
        user_id=user_id
    )

@router.post("/custom-prompt")
async def save_custom_prompt(
    request: CustomPromptRequest,
    current_user: dict = Depends(get_current_user)
):
    """Save or update user's custom prompt"""
    user_id = current_user.get("id")
    
    service = get_user_settings_service()
    success = await service.save_custom_prompt(user_id, request.custom_prompt)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save custom prompt"
        )
    
    return {"success": True, "message": "Custom prompt saved successfully"}

@router.delete("/custom-prompt")
async def delete_custom_prompt(current_user: dict = Depends(get_current_user)):
    """Delete user's custom prompt"""
    user_id = current_user.get("id")
    
    service = get_user_settings_service()
    success = await service.delete_custom_prompt(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete custom prompt"
        )
    
    return {"success": True, "message": "Custom prompt deleted successfully"}