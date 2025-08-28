"""
Service for managing user settings including custom prompts in Firestore
"""
from typing import Dict, Any, Optional
from datetime import datetime
from google.cloud import firestore
from google.cloud.firestore_v1 import DocumentReference
import os

class UserSettingsService:
    def __init__(self):
        self.db = firestore.Client(project=os.getenv('GOOGLE_CLOUD_PROJECT', 'proj-roth'))
        self.collection = 'user_settings'
        
    async def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user settings from Firestore"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting user settings: {e}")
            return None
    
    async def save_custom_prompt(self, user_id: str, custom_prompt: str) -> bool:
        """Save or update user's custom prompt"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            
            # Check if document exists
            doc = doc_ref.get()
            
            if doc.exists:
                # Update existing document
                doc_ref.update({
                    'custom_prompt': custom_prompt,
                    'updated_at': datetime.utcnow().isoformat()
                })
            else:
                # Create new document
                doc_ref.set({
                    'user_id': user_id,
                    'custom_prompt': custom_prompt,
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat()
                })
            
            return True
        except Exception as e:
            print(f"Error saving custom prompt: {e}")
            return False
    
    async def get_custom_prompt(self, user_id: str) -> Optional[str]:
        """Get user's custom prompt"""
        settings = await self.get_user_settings(user_id)
        if settings:
            return settings.get('custom_prompt')
        return None
    
    async def delete_custom_prompt(self, user_id: str) -> bool:
        """Delete user's custom prompt (set to empty string)"""
        return await self.save_custom_prompt(user_id, "")

# Singleton instance
_user_settings_service = None

def get_user_settings_service() -> UserSettingsService:
    global _user_settings_service
    if _user_settings_service is None:
        _user_settings_service = UserSettingsService()
    return _user_settings_service