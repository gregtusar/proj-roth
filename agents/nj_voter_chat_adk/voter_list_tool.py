"""
Tool for managing voter lists in BigQuery
"""
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import json

logger = logging.getLogger(__name__)

class VoterListTool:
    """Tool for saving and managing voter lists"""
    
    def __init__(self, project_id: str = "proj-roth"):
        self.project_id = project_id
        self.dataset_id = "voter_data"
        self.table_id = "voter_lists"
        self.full_table_id = f"{project_id}.{self.dataset_id}.{self.table_id}"
        self.client = bigquery.Client(project=project_id)
    
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
            
            # Prepare the row to insert
            row = {
                "list_id": list_id,
                "user_id": user_id,
                "user_email": user_email,
                "list_name": list_name,
                "description_text": description_text,
                "sql_query": sql_query,
                "row_count": row_count,
                "is_shared": is_shared,
                "is_active": True,
                "created_at": current_time,
                "updated_at": current_time,
                "created_by_model": model_name,
                "query_execution_time_ms": execution_time_ms,
                "access_count": 0,
                "share_type": share_type
            }
            
            # Insert the row
            table = self.client.get_table(self.full_table_id)
            errors = self.client.insert_rows_json(table, [row])
            
            if errors:
                logger.error(f"Failed to insert voter list: {errors}")
                return {
                    "success": False,
                    "error": f"Failed to save list: {errors}",
                    "list_id": None
                }
            
            logger.info(f"Successfully saved voter list {list_id} for user {user_email}")
            return {
                "success": True,
                "list_id": list_id,
                "message": f"List '{list_name}' saved successfully"
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
        Get all lists for a user
        
        Args:
            user_id: User ID to get lists for
            include_shared: Whether to include shared lists
            limit: Maximum number of lists to return
        
        Returns:
            List of voter lists
        """
        try:
            if include_shared:
                query = f"""
                SELECT 
                    list_id,
                    list_name,
                    description_text,
                    sql_query,
                    row_count,
                    created_at,
                    updated_at,
                    is_shared,
                    share_type,
                    access_count
                FROM `{self.full_table_id}`
                WHERE (user_id = @user_id OR is_shared = TRUE)
                    AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT @limit
                """
            else:
                query = f"""
                SELECT 
                    list_id,
                    list_name,
                    description_text,
                    sql_query,
                    row_count,
                    created_at,
                    updated_at,
                    is_shared,
                    share_type,
                    access_count
                FROM `{self.full_table_id}`
                WHERE user_id = @user_id
                    AND is_active = TRUE
                ORDER BY created_at DESC
                LIMIT @limit
                """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            lists = []
            for row in results:
                lists.append({
                    "list_id": row.list_id,
                    "list_name": row.list_name,
                    "description_text": row.description_text,
                    "sql_query": row.sql_query,
                    "row_count": row.row_count,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "is_shared": row.is_shared,
                    "share_type": row.share_type,
                    "access_count": row.access_count
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