"""
BigQuery service for managing authorized users
"""
from typing import Optional, Dict, Any
from google.cloud import bigquery
from datetime import datetime
import uuid

class BigQueryUserService:
    def __init__(self):
        self.client = bigquery.Client(project="proj-roth")
        self.dataset_id = "voter_data"
        self.table_id = "authorized_users"
        self.table_ref = f"proj-roth.{self.dataset_id}.{self.table_id}"
    
    async def save_or_update_user(self, google_user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save or update user data in BigQuery authorized_users table"""
        try:
            google_id = google_user_data.get("googleId") or google_user_data.get("sub") or google_user_data.get("id")
            email = google_user_data.get("email")
            
            if not email or not google_id:
                raise ValueError("Email and Google ID are required")
            
            # First, check if user exists by email or google_id
            query = f"""
                SELECT user_id, email, google_id, full_name, picture_url, is_active, role
                FROM `{self.table_ref}`
                WHERE email = @email OR google_id = @google_id
                LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("email", "STRING", email),
                    bigquery.ScalarQueryParameter("google_id", "STRING", google_id),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                # User exists, update their info
                existing_user = dict(results[0])
                user_id = existing_user['user_id']
                
                update_query = f"""
                    UPDATE `{self.table_ref}`
                    SET 
                        google_id = @google_id,
                        full_name = @full_name,
                        given_name = @given_name,
                        family_name = @family_name,
                        picture_url = @picture_url,
                        last_login = CURRENT_TIMESTAMP(),
                        login_count = login_count + 1
                    WHERE user_id = @user_id
                """
                
                update_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                        bigquery.ScalarQueryParameter("google_id", "STRING", google_id),
                        bigquery.ScalarQueryParameter("full_name", "STRING", google_user_data.get("name", "")),
                        bigquery.ScalarQueryParameter("given_name", "STRING", google_user_data.get("given_name", "")),
                        bigquery.ScalarQueryParameter("family_name", "STRING", google_user_data.get("family_name", "")),
                        bigquery.ScalarQueryParameter("picture_url", "STRING", google_user_data.get("picture", "")),
                    ]
                )
                
                update_job = self.client.query(update_query, job_config=update_config)
                update_job.result()
                
                print(f"[BigQuery Users] Updated user {user_id} ({email})")
                
                # Return user data with internal user_id
                return {
                    "id": user_id,  # Use internal UUID, not Google ID
                    "user_id": user_id,
                    "email": email,
                    "name": google_user_data.get("name", existing_user.get('full_name', '')),
                    "picture": google_user_data.get("picture", existing_user.get('picture_url', '')),
                    "googleId": google_id,
                    "is_active": existing_user.get('is_active', True),
                    "role": existing_user.get('role', 'viewer')
                }
            else:
                # New user, create with UUID
                user_id = str(uuid.uuid4())
                
                insert_query = f"""
                    INSERT INTO `{self.table_ref}` (
                        user_id,
                        email,
                        google_id,
                        full_name,
                        given_name,
                        family_name,
                        picture_url,
                        is_active,
                        role,
                        created_at,
                        last_login,
                        login_count
                    ) VALUES (
                        @user_id,
                        @email,
                        @google_id,
                        @full_name,
                        @given_name,
                        @family_name,
                        @picture_url,
                        TRUE,
                        'viewer',
                        CURRENT_TIMESTAMP(),
                        CURRENT_TIMESTAMP(),
                        1
                    )
                """
                
                insert_config = bigquery.QueryJobConfig(
                    query_parameters=[
                        bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                        bigquery.ScalarQueryParameter("email", "STRING", email),
                        bigquery.ScalarQueryParameter("google_id", "STRING", google_id),
                        bigquery.ScalarQueryParameter("full_name", "STRING", google_user_data.get("name", "")),
                        bigquery.ScalarQueryParameter("given_name", "STRING", google_user_data.get("given_name", "")),
                        bigquery.ScalarQueryParameter("family_name", "STRING", google_user_data.get("family_name", "")),
                        bigquery.ScalarQueryParameter("picture_url", "STRING", google_user_data.get("picture", "")),
                    ]
                )
                
                insert_job = self.client.query(insert_query, job_config=insert_config)
                insert_job.result()
                
                print(f"[BigQuery Users] Created new user {user_id} ({email})")
                
                # Return user data with internal user_id
                return {
                    "id": user_id,  # Use internal UUID, not Google ID
                    "user_id": user_id,
                    "email": email,
                    "name": google_user_data.get("name", ""),
                    "picture": google_user_data.get("picture", ""),
                    "googleId": google_id,
                    "is_active": True,
                    "role": "viewer"
                }
                
        except Exception as e:
            print(f"[BigQuery Users] Error saving user: {e}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from BigQuery by internal user_id"""
        try:
            query = f"""
                SELECT user_id, email, google_id, full_name, picture_url, is_active, role
                FROM `{self.table_ref}`
                WHERE user_id = @user_id
                LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                user = dict(results[0])
                return {
                    "id": user['user_id'],  # Use internal UUID
                    "user_id": user['user_id'],
                    "email": user['email'],
                    "name": user.get('full_name', ''),
                    "picture": user.get('picture_url', ''),
                    "googleId": user.get('google_id', ''),
                    "is_active": user.get('is_active', True),
                    "role": user.get('role', 'viewer')
                }
            return None
        except Exception as e:
            print(f"[BigQuery Users] Error fetching user: {e}")
            return None
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from BigQuery by Google ID (for migration)"""
        try:
            query = f"""
                SELECT user_id, email, google_id, full_name, picture_url, is_active, role
                FROM `{self.table_ref}`
                WHERE google_id = @google_id
                LIMIT 1
            """
            
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("google_id", "STRING", google_id),
                ]
            )
            
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            
            if results:
                user = dict(results[0])
                return {
                    "id": user['user_id'],  # Use internal UUID
                    "user_id": user['user_id'],
                    "email": user['email'],
                    "name": user.get('full_name', ''),
                    "picture": user.get('picture_url', ''),
                    "googleId": user.get('google_id', ''),
                    "is_active": user.get('is_active', True),
                    "role": user.get('role', 'viewer')
                }
            return None
        except Exception as e:
            print(f"[BigQuery Users] Error fetching user by Google ID: {e}")
            return None

# Singleton instance
_bigquery_user_service = None

def get_bigquery_user_service() -> BigQueryUserService:
    global _bigquery_user_service
    if _bigquery_user_service is None:
        _bigquery_user_service = BigQueryUserService()
    return _bigquery_user_service