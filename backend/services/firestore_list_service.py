"""
Firestore-based voter list management service
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from google.cloud import firestore
import os

from models.voter_list import VoterList


class FirestoreListService:
    def __init__(self, project_id: Optional[str] = None):
        """Initialize Firestore connection for list management"""
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        
        try:
            # Initialize Firestore client
            self.client = firestore.AsyncClient(project=self.project_id)
            
            # Collection reference
            self.lists_collection = self.client.collection('lists')
            
            self.connected = True
            print(f"[Firestore Lists] Service initialized successfully for project: {self.project_id}")
        except Exception as e:
            print(f"Warning: Could not connect to Firestore: {e}")
            self.connected = False
            self.client = None
    
    async def create_list(
        self,
        user_id: str,
        user_email: str,
        name: str,
        description: Optional[str] = None,
        query: str = "",
        prompt: Optional[str] = None,
        row_count: int = 0
    ) -> VoterList:
        """Create a new voter list"""
        if not self.connected:
            raise RuntimeError("Firestore is not connected")
            
        list_id = str(uuid.uuid4())
        
        list_data = {
            "id": list_id,
            "user_id": user_id,
            "user_email": user_email,
            "name": name,
            "description": description or "",
            "query": query,
            "prompt": prompt,
            "row_count": row_count,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Create document with list_id as document ID
        await self.lists_collection.document(list_id).set(list_data)
        
        return VoterList(**list_data)
    
    async def get_user_lists(
        self, 
        user_id: str,
        limit: int = 100
    ) -> List[VoterList]:
        """Get all lists (public access), ordered by most recent"""
        if not self.connected:
            print(f"[Firestore Lists] Not connected, returning empty list")
            return []
        
        try:
            # Get ALL lists, not filtered by user_id (public access)
            query = self.lists_collection.limit(limit)
            
            lists = []
            async for doc in query.stream():
                list_data = doc.to_dict()
                print(f"[Firestore Lists] Raw doc data: {list_data}")
                # Check if active in memory
                if list_data.get("is_active", True):
                    try:
                        voter_list = VoterList(**list_data)
                        lists.append(voter_list)
                    except Exception as e:
                        print(f"[Firestore Lists] Error creating VoterList: {e}")
                        print(f"  Data: {list_data}")
            
            # Sort by updated_at in memory
            lists.sort(key=lambda x: x.updated_at, reverse=True)
            
            print(f"[Firestore Lists] Found {len(lists)} lists for user {user_id}")
            return lists
            
        except Exception as e:
            print(f"[Firestore Lists] Error getting lists: {e}")
            return []
    
    async def get_list(self, list_id: str, user_id: str) -> Optional[VoterList]:
        """Get a specific list (public access)"""
        if not self.connected:
            return None
            
        doc_ref = self.lists_collection.document(list_id)
        doc = await doc_ref.get()
        
        if doc.exists:
            list_data = doc.to_dict()
            # No ownership check - public access
            if list_data.get("is_active"):
                return VoterList(**list_data)
        
        return None
    
    async def update_list(
        self,
        list_id: str,
        user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        query: Optional[str] = None,
        prompt: Optional[str] = None,
        row_count: Optional[int] = None
    ) -> bool:
        """Update a voter list (public access)"""
        if not self.connected:
            return False
            
        doc_ref = self.lists_collection.document(list_id)
        
        # No ownership verification - anyone can update
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        
        # Build update dict
        update_data = {"updated_at": datetime.utcnow()}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if query is not None:
            update_data["query"] = query
        if prompt is not None:
            update_data["prompt"] = prompt
        if row_count is not None:
            update_data["row_count"] = row_count
        
        # Update the list
        await doc_ref.update(update_data)
        
        return True
    
    async def delete_list(self, list_id: str, user_id: str) -> bool:
        """Soft delete a list (public access)"""
        if not self.connected:
            return False
            
        doc_ref = self.lists_collection.document(list_id)
        
        # No ownership verification - anyone can delete
        doc = await doc_ref.get()
        if not doc.exists:
            return False
        
        # Soft delete
        await doc_ref.update({
            "is_active": False,
            "updated_at": datetime.utcnow()
        })
        
        return True
    
    async def search_lists(
        self,
        user_id: str,
        query_text: str,
        limit: int = 20
    ) -> List[VoterList]:
        """Search all lists by name or description (public access)"""
        if not self.connected:
            return []
            
        # Get ALL lists and filter in memory
        # (Firestore doesn't have full-text search without additional setup)
        all_lists = await self.get_user_lists(user_id, limit=100)  # user_id param ignored now
        
        query_lower = query_text.lower()
        filtered_lists = [
            lst for lst in all_lists
            if query_lower in lst.name.lower() or 
               (lst.description and query_lower in lst.description.lower())
        ]
        
        return filtered_lists[:limit]


# Singleton instance
_firestore_list_service = None

def get_firestore_list_service() -> FirestoreListService:
    """Get or create the Firestore list service singleton"""
    global _firestore_list_service
    if _firestore_list_service is None:
        _firestore_list_service = FirestoreListService()
    return _firestore_list_service