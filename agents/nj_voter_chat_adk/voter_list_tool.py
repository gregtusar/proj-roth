"""
Tool for managing voter lists in Firestore
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from google.cloud import firestore
from google.cloud.exceptions import GoogleCloudError
import json

logger = logging.getLogger(__name__)

class VoterListTool:
    """Tool for saving and managing voter lists in Firestore"""
    
    def __init__(self, project_id: str = "proj-roth"):
        self.project_id = project_id
        self.client = firestore.Client(project=project_id)
        self.collection_name = "voter_lists"
    
    def save_voter_list(
        self,
        user_id: str,
        user_email: str,
        list_name: str,
        description_text: str,
        sql_query: str,
        row_count: int,
        model_name: str = "gemini-1.5-flash",
        execution_time_ms: Optional[int] = None,
        is_shared: bool = False,
        share_type: str = "private"
    ) -> Dict[str, Any]:
        """
        Save a voter list to BigQuery
        
        Args:
            user_id: User ID from authentication
            user_email: User's email address
            list_name: Name for the list (model-generated or user-provided)
            description_text: Original query text
            sql_query: SQL query to regenerate the list
            row_count: Number of voters in the result
            model_name: Name of the model that created the list
            execution_time_ms: Query execution time in milliseconds
            is_shared: Whether the list is shared
            share_type: Type of sharing ('private', 'team', 'public')
        
        Returns:
            Dict with list_id and success status
        """
        try:
            list_id = str(uuid.uuid4())
            current_time = datetime.utcnow()
            
            # Prepare the document for Firestore (using field names that match the backend)
            doc_data = {
                "id": list_id,  # Firestore uses 'id' not 'list_id'
                "user_id": user_id,
                "user_email": user_email,
                "name": list_name,  # Firestore uses 'name' not 'list_name'
                "description": description_text,  # Firestore uses 'description' not 'description_text'
                "query": sql_query,  # Firestore uses 'query' not 'sql_query'
                "row_count": row_count,
                "is_shared": is_shared,
                "is_active": True,
                "created_at": current_time,  # Firestore handles datetime objects natively
                "updated_at": current_time,  # Firestore handles datetime objects natively
                "created_by_model": model_name,
                "query_execution_time_ms": execution_time_ms,
                "access_count": 0,
                "share_type": share_type
            }
            
            # Save to Firestore
            doc_ref = self.client.collection(self.collection_name).document(list_id)
            doc_ref.set(doc_data)
            
            logger.info(f"Successfully saved voter list {list_id} to Firestore for user {user_email}")
            return {
                "success": True,
                "list_id": list_id,
                "message": f"List '{list_name}' saved successfully to Firestore"
            }
            
        except Exception as e:
            logger.error(f"Error saving voter list: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "list_id": None
            }
    
    def get_user_lists(
        self,
        user_id: str,
        include_shared: bool = True,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all lists for a user from Firestore
        
        Args:
            user_id: User ID to get lists for
            include_shared: Whether to include shared lists
            limit: Maximum number of lists to return
        
        Returns:
            List of voter lists
        """
        try:
            # Query Firestore for user's lists
            query = self.client.collection(self.collection_name)
            query = query.where("user_id", "==", user_id)
            query = query.where("is_active", "==", True)
            query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
            query = query.limit(limit)
            
            docs = query.stream()
            
            lists = []
            for doc in docs:
                data = doc.to_dict()
                # Convert Firestore field names back to expected format
                lists.append({
                    "list_id": data.get("id"),
                    "list_name": data.get("name"),
                    "description_text": data.get("description"),
                    "sql_query": data.get("query"),
                    "row_count": data.get("row_count"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "is_shared": data.get("is_shared"),
                    "share_type": data.get("share_type"),
                    "access_count": data.get("access_count", 0)
                })
            
            return lists
            
        except Exception as e:
            logger.error(f"Error getting user lists: {str(e)}")
            return []
    
    def update_list(
        self,
        list_id: str,
        user_id: str,
        list_name: Optional[str] = None,
        description_text: Optional[str] = None,
        is_shared: Optional[bool] = None,
        share_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a voter list
        
        Args:
            list_id: ID of the list to update
            user_id: User ID (for authorization check)
            list_name: New name for the list
            description_text: New description
            is_shared: New sharing status
            share_type: New share type
        
        Returns:
            Dict with success status
        """
        try:
            # Build the update query
            updates = []
            params = [
                bigquery.ScalarQueryParameter("list_id", "STRING", list_id),
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
            ]
            
            if list_name is not None:
                updates.append("list_name = @list_name")
                params.append(bigquery.ScalarQueryParameter("list_name", "STRING", list_name))
            
            if description_text is not None:
                updates.append("description_text = @description_text")
                params.append(bigquery.ScalarQueryParameter("description_text", "STRING", description_text))
            
            if is_shared is not None:
                updates.append("is_shared = @is_shared")
                params.append(bigquery.ScalarQueryParameter("is_shared", "BOOL", is_shared))
            
            if share_type is not None:
                updates.append("share_type = @share_type")
                params.append(bigquery.ScalarQueryParameter("share_type", "STRING", share_type))
            
            if not updates:
                return {"success": False, "error": "No updates provided"}
            
            updates.append("updated_at = CURRENT_TIMESTAMP()")
            
            query = f"""
            UPDATE `{self.full_table_id}`
            SET {', '.join(updates)}
            WHERE list_id = @list_id AND user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(query_parameters=params)
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            return {"success": True, "message": "List updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating list: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def delete_list(self, list_id: str, user_id: str) -> Dict[str, Any]:
        """
        Soft delete a voter list
        
        Args:
            list_id: ID of the list to delete
            user_id: User ID (for authorization check)
        
        Returns:
            Dict with success status
        """
        try:
            query = f"""
            UPDATE `{self.full_table_id}`
            SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP()
            WHERE list_id = @list_id AND user_id = @user_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("list_id", "STRING", list_id),
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
            return {"success": True, "message": "List deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting list: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def increment_access_count(self, list_id: str) -> None:
        """
        Increment the access count for a list
        
        Args:
            list_id: ID of the list
        """
        try:
            query = f"""
            UPDATE `{self.full_table_id}`
            SET 
                access_count = IFNULL(access_count, 0) + 1,
                last_accessed_at = CURRENT_TIMESTAMP()
            WHERE list_id = @list_id
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("list_id", "STRING", list_id),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            
        except Exception as e:
            logger.error(f"Error incrementing access count: {str(e)}")