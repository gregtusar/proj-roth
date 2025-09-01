"""
Service for storing and managing user OAuth tokens in Firestore
"""
import logging
from typing import Dict, Optional
from google.cloud import firestore
from google.cloud import secretmanager
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os

logger = logging.getLogger(__name__)

class OAuthTokenService:
    def __init__(self):
        self.db = firestore.Client()
        self.collection = 'user_oauth_tokens'
        self.secret_client = secretmanager.SecretManagerServiceClient()
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'proj-roth')
        self._client_id = None
        self._client_secret = None
    
    def _get_secret(self, secret_id: str) -> str:
        """Get secret value from Secret Manager"""
        try:
            name = f"projects/{self.project_id}/secrets/{secret_id}/versions/latest"
            response = self.secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode('UTF-8')
        except Exception as e:
            logger.error(f"Error accessing secret {secret_id}: {e}")
            return None
    
    def _get_client_credentials(self):
        """Get OAuth client credentials from Secret Manager"""
        if not self._client_id:
            self._client_id = self._get_secret('google-oauth-client-id')
        if not self._client_secret:
            self._client_secret = self._get_secret('google-oauth-client-secret')
        return self._client_id, self._client_secret
        
    async def store_tokens(self, user_id: str, tokens: Dict) -> bool:
        """Store or update user's OAuth tokens"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            
            token_data = {
                'user_id': user_id,
                'access_token': tokens.get('access_token'),
                'refresh_token': tokens.get('refresh_token'),
                'expires_at': tokens.get('expires_at'),
                'updated_at': datetime.utcnow(),
                'scopes': tokens.get('scopes', [])
            }
            
            doc_ref.set(token_data, merge=True)
            logger.info(f"Stored OAuth tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing OAuth tokens: {e}")
            return False
    
    async def get_valid_credentials(self, user_id: str) -> Optional[Credentials]:
        """Get valid OAuth credentials for a user, refreshing if needed"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                logger.warning(f"No OAuth tokens found for user {user_id}")
                return None
            
            token_data = doc.to_dict()
            
            # Get client credentials from Secret Manager
            client_id, client_secret = self._get_client_credentials()
            if not client_id or not client_secret:
                logger.error("Failed to get OAuth client credentials from Secret Manager")
                return None
            
            # Create credentials object
            creds = Credentials(
                token=token_data.get('access_token'),
                refresh_token=token_data.get('refresh_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=client_id,
                client_secret=client_secret,
                scopes=['https://www.googleapis.com/auth/drive.file', 
                       'https://www.googleapis.com/auth/documents']
            )
            
            # Check if token is expired
            if token_data.get('expires_at'):
                if isinstance(token_data['expires_at'], datetime):
                    if token_data['expires_at'] <= datetime.utcnow():
                        # Token is expired, refresh it
                        logger.info(f"Refreshing expired token for user {user_id}")
                        creds.refresh(Request())
                        
                        # Store the new tokens
                        await self.store_tokens(user_id, {
                            'access_token': creds.token,
                            'refresh_token': creds.refresh_token,
                            'expires_at': datetime.utcnow() + timedelta(seconds=3600)
                        })
            
            return creds
            
        except Exception as e:
            logger.error(f"Error getting OAuth credentials: {e}")
            return None
    
    async def revoke_tokens(self, user_id: str) -> bool:
        """Remove user's OAuth tokens"""
        try:
            doc_ref = self.db.collection(self.collection).document(user_id)
            doc_ref.delete()
            logger.info(f"Revoked OAuth tokens for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error revoking OAuth tokens: {e}")
            return False