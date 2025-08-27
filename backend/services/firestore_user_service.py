"""
Firestore service for managing user data
"""
from typing import Optional, Dict, Any
from google.cloud import firestore
from datetime import datetime

class FirestoreUserService:
    def __init__(self):
        self.db = firestore.AsyncClient()
        self.collection = "users"
        self.connected = True
    
    async def save_user(self, user_data: Dict[str, Any]) -> None:
        """Save or update user data in Firestore"""
        try:
            user_ref = self.db.collection(self.collection).document(user_data["id"])
            await user_ref.set({
                **user_data,
                "updated_at": datetime.utcnow().isoformat(),
            }, merge=True)
            print(f"[Firestore Users] Saved user {user_data['id']}")
        except Exception as e:
            print(f"[Firestore Users] Error saving user: {e}")
            raise
    
    async def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from Firestore"""
        try:
            user_ref = self.db.collection(self.collection).document(user_id)
            doc = await user_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"[Firestore Users] Error fetching user: {e}")
            return None

# Singleton instance
_firestore_user_service = None

def get_firestore_user_service() -> FirestoreUserService:
    global _firestore_user_service
    if _firestore_user_service is None:
        _firestore_user_service = FirestoreUserService()
    return _firestore_user_service