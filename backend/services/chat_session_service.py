import uuid
from datetime import datetime
from typing import List, Optional
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError
import os
import json

from models.chat_session import (
    ChatSession, ChatMessage, CreateSessionRequest,
    UpdateSessionRequest, SessionListResponse, SessionMessagesResponse
)

class ChatSessionService:
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
        self.dataset_id = os.getenv("VOTER_DATASET", "voter_data")
        self.sessions_table = f"{self.project_id}.{self.dataset_id}.chat_sessions"
        self.messages_table = f"{self.project_id}.{self.dataset_id}.chat_messages"
        
        try:
            self.client = bigquery.Client(project=self.project_id)
        except Exception as e:
            print(f"Failed to initialize BigQuery client: {e}")
            self.client = None
    
    async def create_session(
        self, 
        user_id: str, 
        user_email: str,
        session_name: Optional[str] = None,
        first_message: Optional[str] = None
    ) -> ChatSession:
        """Create a new chat session"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Use first message as session name if not provided
        if not session_name and first_message:
            # Take first 50 chars of the message as the name
            session_name = first_message[:50] + ("..." if len(first_message) > 50 else "")
        elif not session_name:
            session_name = f"New Chat {now.strftime('%Y-%m-%d %H:%M')}"
        
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            user_email=user_email,
            session_name=session_name,
            created_at=now,
            updated_at=now,
            is_active=True,
            message_count=0,
            metadata={}
        )
        
        # Insert into BigQuery
        if self.client:
            try:
                table = self.client.get_table(self.sessions_table)
                rows_to_insert = [{
                    "session_id": session.session_id,
                    "user_id": session.user_id,
                    "user_email": session.user_email,
                    "session_name": session.session_name,
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "is_active": session.is_active,
                    "message_count": session.message_count,
                    "metadata": json.dumps(session.metadata) if session.metadata else None
                }]
                
                errors = self.client.insert_rows_json(table, rows_to_insert)
                if errors:
                    print(f"Failed to create session: {errors}")
                    raise Exception(f"Failed to create session: {errors}")
            except GoogleCloudError as e:
                print(f"BigQuery error creating session: {e}")
                raise
            except Exception as e:
                # If table doesn't exist, create it
                if "Not found" in str(e):
                    await self._create_tables()
                    return await self.create_session(user_id, user_email, session_name, first_message)
                raise
        
        return session
    
    async def get_user_sessions(self, user_id: str) -> List[ChatSession]:
        """Get all sessions for a user"""
        if not self.client:
            return []
        
        query = f"""
        SELECT 
            session_id,
            user_id,
            user_email,
            session_name,
            created_at,
            updated_at,
            is_active,
            message_count,
            metadata
        FROM `{self.sessions_table}`
        WHERE user_id = @user_id
            AND is_active = TRUE
        ORDER BY updated_at DESC
        LIMIT 100
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()
            
            sessions = []
            for row in results:
                sessions.append(ChatSession(
                    session_id=row.session_id,
                    user_id=row.user_id,
                    user_email=row.user_email,
                    session_name=row.session_name,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    is_active=row.is_active,
                    message_count=row.message_count,
                    metadata=json.loads(row.metadata) if row.metadata else None
                ))
            
            return sessions
        except Exception as e:
            print(f"Error fetching sessions: {e}")
            return []
    
    async def get_session_messages(self, session_id: str, user_id: str) -> SessionMessagesResponse:
        """Get all messages for a session"""
        if not self.client:
            raise Exception("BigQuery client not available")
        
        # First get the session
        session_query = f"""
        SELECT 
            session_id,
            user_id,
            user_email,
            session_name,
            created_at,
            updated_at,
            is_active,
            message_count,
            metadata
        FROM `{self.sessions_table}`
        WHERE session_id = @session_id
            AND user_id = @user_id
        """
        
        # Then get the messages
        messages_query = f"""
        SELECT 
            message_id,
            session_id,
            user_id,
            message_type,
            message_text,
            timestamp,
            sequence_number,
            metadata
        FROM `{self.messages_table}`
        WHERE session_id = @session_id
        ORDER BY sequence_number ASC
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        try:
            # Get session
            session_job = self.client.query(session_query, job_config=job_config)
            session_results = list(session_job.result())
            
            if not session_results:
                raise Exception(f"Session {session_id} not found")
            
            row = session_results[0]
            session = ChatSession(
                session_id=row.session_id,
                user_id=row.user_id,
                user_email=row.user_email,
                session_name=row.session_name,
                created_at=row.created_at,
                updated_at=row.updated_at,
                is_active=row.is_active,
                message_count=row.message_count,
                metadata=json.loads(row.metadata) if row.metadata else None
            )
            
            # Get messages
            messages_job = self.client.query(messages_query, job_config=bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
                ]
            ))
            messages_results = messages_job.result()
            
            messages = []
            for row in messages_results:
                messages.append(ChatMessage(
                    message_id=row.message_id,
                    session_id=row.session_id,
                    user_id=row.user_id,
                    message_type=row.message_type,
                    message_text=row.message_text,
                    timestamp=row.timestamp,
                    sequence_number=row.sequence_number,
                    metadata=json.loads(row.metadata) if row.metadata else None
                ))
            
            return SessionMessagesResponse(session=session, messages=messages)
        except Exception as e:
            print(f"Error fetching session messages: {e}")
            raise
    
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        message_type: str,
        message_text: str,
        sequence_number: Optional[int] = None
    ) -> ChatMessage:
        """Add a message to a session"""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Get the next sequence number if not provided
        if sequence_number is None:
            sequence_number = await self._get_next_sequence_number(session_id)
        
        message = ChatMessage(
            message_id=message_id,
            session_id=session_id,
            user_id=user_id,
            message_type=message_type,
            message_text=message_text,
            timestamp=now,
            sequence_number=sequence_number,
            metadata={}
        )
        
        if self.client:
            try:
                # Insert message
                table = self.client.get_table(self.messages_table)
                rows_to_insert = [{
                    "message_id": message.message_id,
                    "session_id": message.session_id,
                    "user_id": message.user_id,
                    "message_type": message.message_type,
                    "message_text": message.message_text,
                    "timestamp": message.timestamp.isoformat(),
                    "sequence_number": message.sequence_number,
                    "metadata": json.dumps(message.metadata) if message.metadata else None
                }]
                
                errors = self.client.insert_rows_json(table, rows_to_insert)
                if errors:
                    print(f"Failed to add message: {errors}")
                    raise Exception(f"Failed to add message: {errors}")
                
                # Update session updated_at and message_count
                await self._update_session_activity(session_id)
                
            except Exception as e:
                # If table doesn't exist, create it
                if "Not found" in str(e):
                    await self._create_tables()
                    return await self.add_message(session_id, user_id, message_type, message_text, sequence_number)
                raise
        
        return message
    
    async def update_session_name(self, session_id: str, user_id: str, new_name: str) -> bool:
        """Update a session's name"""
        if not self.client:
            return False
        
        query = f"""
        UPDATE `{self.sessions_table}`
        SET 
            session_name = @new_name,
            updated_at = CURRENT_TIMESTAMP()
        WHERE session_id = @session_id
            AND user_id = @user_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
                bigquery.ScalarQueryParameter("new_name", "STRING", new_name)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            return True
        except Exception as e:
            print(f"Error updating session name: {e}")
            return False
    
    async def delete_session(self, session_id: str, user_id: str) -> bool:
        """Soft delete a session"""
        if not self.client:
            return False
        
        query = f"""
        UPDATE `{self.sessions_table}`
        SET 
            is_active = FALSE,
            updated_at = CURRENT_TIMESTAMP()
        WHERE session_id = @session_id
            AND user_id = @user_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id),
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    async def _get_next_sequence_number(self, session_id: str) -> int:
        """Get the next sequence number for a session"""
        if not self.client:
            return 0
        
        query = f"""
        SELECT MAX(sequence_number) as max_seq
        FROM `{self.messages_table}`
        WHERE session_id = @session_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            results = list(query_job.result())
            if results and results[0].max_seq is not None:
                return results[0].max_seq + 1
            return 0
        except:
            return 0
    
    async def _update_session_activity(self, session_id: str):
        """Update session's updated_at and message_count"""
        if not self.client:
            return
        
        # Skip update if session was recently created (within streaming buffer)
        # BigQuery doesn't allow UPDATE on streaming buffer data
        # The updated_at field will be slightly stale but this is acceptable
        
        query = f"""
        UPDATE `{self.sessions_table}`
        SET 
            updated_at = CURRENT_TIMESTAMP(),
            message_count = (
                SELECT COUNT(*) 
                FROM `{self.messages_table}` 
                WHERE session_id = @session_id
            )
        WHERE session_id = @session_id
        AND created_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 SECOND)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("session_id", "STRING", session_id)
            ]
        )
        
        try:
            query_job = self.client.query(query, job_config=job_config)
            query_job.result()
        except Exception as e:
            # Ignore streaming buffer errors - the data is still saved
            if "streaming buffer" in str(e).lower():
                print(f"Session {session_id} is in streaming buffer, skipping activity update")
            else:
                print(f"Error updating session activity: {e}")
    
    async def _create_tables(self):
        """Create tables if they don't exist"""
        if not self.client:
            return
        
        # Create sessions table
        sessions_schema = [
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_email", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("is_active", "BOOLEAN", mode="NULLABLE"),
            bigquery.SchemaField("message_count", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
        ]
        
        sessions_table = bigquery.Table(self.sessions_table, schema=sessions_schema)
        sessions_table.clustering_fields = ["user_id", "created_at"]
        
        try:
            self.client.create_table(sessions_table)
            print(f"Created table {self.sessions_table}")
        except Exception as e:
            if "Already Exists" not in str(e):
                print(f"Error creating sessions table: {e}")
        
        # Create messages table
        messages_schema = [
            bigquery.SchemaField("message_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("message_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("message_text", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("sequence_number", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
        ]
        
        messages_table = bigquery.Table(self.messages_table, schema=messages_schema)
        messages_table.clustering_fields = ["session_id", "sequence_number"]
        
        try:
            self.client.create_table(messages_table)
            print(f"Created table {self.messages_table}")
        except Exception as e:
            if "Already Exists" not in str(e):
                print(f"Error creating messages table: {e}")

# Global instance
_chat_session_service = None

def get_chat_session_service() -> ChatSessionService:
    global _chat_session_service
    if _chat_session_service is None:
        _chat_session_service = ChatSessionService()
    return _chat_session_service