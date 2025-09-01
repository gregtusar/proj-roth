"""
Google Docs service using user OAuth tokens
This allows users to create documents in their own Google Drive
"""
import logging
from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore
from datetime import datetime
import os
import json
from .oauth_token_service import OAuthTokenService

logger = logging.getLogger(__name__)

class UserGoogleDocsService:
    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "proj-roth")
        self.db = firestore.Client(project=self.project_id)
        self.oauth_service = OAuthTokenService()
        self.shared_folder_id = None
        self._load_config()
    
    def _load_config(self):
        """Load the shared folder configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'google_drive_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.shared_folder_id = config.get('shared_folder_id')
                    logger.info(f"Loaded shared folder ID: {self.shared_folder_id}")
            else:
                logger.warning("No google_drive_config.json found")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    async def _get_user_credentials(self, user_data: Dict) -> Optional[Credentials]:
        """Get valid OAuth credentials for user from token service"""
        user_id = user_data.get('user_id', user_data.get('id'))
        if not user_id:
            logger.error("No user ID found")
            return None
        
        try:
            # Get credentials from token service (handles refresh automatically)
            creds = await self.oauth_service.get_valid_credentials(user_id)
            return creds
        except Exception as e:
            logger.error(f"Error getting user credentials: {e}")
            return None
    
    async def create_document(self, title: str, content: str, user_data: Dict) -> Dict[str, Any]:
        """Create a document using user's OAuth credentials"""
        try:
            # Get user credentials
            creds = await self._get_user_credentials(user_data)
            if not creds:
                raise ValueError("Unable to get user credentials for Google Docs")
            
            # Build services with user credentials
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            # Create the document
            document = {'title': title}
            doc = docs_service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            
            # Add content if provided
            if content:
                requests = [
                    {
                        'insertText': {
                            'location': {'index': 1},
                            'text': content
                        }
                    }
                ]
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            # Optionally move to shared folder
            if self.shared_folder_id:
                try:
                    # Get current parents
                    file = drive_service.files().get(
                        fileId=doc_id,
                        fields='parents'
                    ).execute()
                    
                    # Move to shared folder
                    previous_parents = ",".join(file.get('parents', []))
                    if previous_parents:
                        drive_service.files().update(
                            fileId=doc_id,
                            addParents=self.shared_folder_id,
                            removeParents=previous_parents,
                            fields='id, parents'
                        ).execute()
                        logger.info(f"Moved document {doc_id} to shared folder")
                except Exception as e:
                    logger.warning(f"Could not move to shared folder: {e}")
            
            # Store metadata in Firestore
            doc_metadata = {
                'doc_id': doc_id,
                'title': title,
                'owner_id': user_data.get('user_id', user_data.get('id')),
                'owner_email': user_data.get('email'),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'url': f"https://docs.google.com/document/d/{doc_id}/edit",
                'created_with': 'user_oauth'
            }
            
            self.db.collection('user_documents').document(doc_id).set(doc_metadata)
            logger.info(f"Document created: {doc_id} for user {user_data.get('email')}")
            
            return doc_metadata
            
        except HttpError as error:
            logger.error(f"Google API error creating document: {error}")
            raise
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            raise
    
    async def read_document(self, doc_id: str, user_data: Dict) -> Dict[str, Any]:
        """Read a document using user's OAuth credentials"""
        try:
            # Check permissions in Firestore first
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                raise ValueError(f"Document {doc_id} not found in database")
            
            metadata = doc_metadata.to_dict()
            user_id = user_data.get('user_id', user_data.get('id'))
            
            # Check if user has access
            if metadata['owner_id'] != user_id and user_data.get('email') != metadata.get('owner_email'):
                raise PermissionError(f"User does not have access to document {doc_id}")
            
            # Get user credentials
            creds = await self._get_user_credentials(user_data)
            if not creds:
                raise ValueError("Unable to get user credentials for Google Docs")
            
            # Read the document
            docs_service = build('docs', 'v1', credentials=creds)
            document = docs_service.documents().get(documentId=doc_id).execute()
            
            # Extract content
            content = self._extract_text_from_document(document)
            
            return {
                'doc_id': doc_id,
                'title': document.get('title'),
                'content': content,
                'metadata': metadata,
                'url': f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
        except HttpError as error:
            logger.error(f"Google API error reading document: {error}")
            raise
        except Exception as e:
            logger.error(f"Error reading document: {e}")
            raise
    
    async def list_user_documents(self, user_data: Dict) -> List[Dict[str, Any]]:
        """List documents for a user from Firestore metadata"""
        try:
            user_id = user_data.get('user_id', user_data.get('id'))
            user_email = user_data.get('email')
            
            # Query by user_id or email
            docs_ref = self.db.collection('user_documents')\
                .where('owner_id', '==', user_id)\
                .order_by('updated_at', direction=firestore.Query.DESCENDING)
            
            docs = docs_ref.stream()
            
            documents = []
            for doc in docs:
                doc_data = doc.to_dict()
                documents.append({
                    'doc_id': doc_data['doc_id'],
                    'title': doc_data['title'],
                    'created_at': doc_data['created_at'].isoformat() if doc_data.get('created_at') else None,
                    'updated_at': doc_data['updated_at'].isoformat() if doc_data.get('updated_at') else None,
                    'url': doc_data.get('url')
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing user documents: {e}")
            raise
    
    async def update_document(self, doc_id: str, content: str, user_data: Dict) -> Dict[str, Any]:
        """Update a document using user's OAuth credentials"""
        try:
            # Check permissions in Firestore
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                raise ValueError(f"Document {doc_id} not found in database")
            
            metadata = doc_metadata.to_dict()
            user_id = user_data.get('user_id', user_data.get('id'))
            
            if metadata['owner_id'] != user_id:
                raise PermissionError(f"User cannot update document {doc_id}")
            
            # Get user credentials
            creds = await self._get_user_credentials(user_data)
            if not creds:
                raise ValueError("Unable to get user credentials for Google Docs")
            
            # Update the document
            docs_service = build('docs', 'v1', credentials=creds)
            
            # Get current document to find end index
            document = docs_service.documents().get(documentId=doc_id).execute()
            end_index = document['body']['content'][-1]['endIndex'] - 1
            
            # Clear and replace content
            requests = [
                {
                    'deleteContentRange': {
                        'range': {
                            'startIndex': 1,
                            'endIndex': end_index
                        }
                    }
                },
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            # Update metadata
            doc_ref.update({
                'updated_at': datetime.utcnow()
            })
            
            logger.info(f"Document updated: {doc_id} by user {user_data.get('email')}")
            return {'doc_id': doc_id, 'status': 'updated'}
            
        except HttpError as error:
            logger.error(f"Google API error updating document: {error}")
            raise
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            raise
    
    async def delete_document(self, doc_id: str, user_data: Dict) -> bool:
        """Delete a document using user's OAuth credentials"""
        try:
            # Check permissions in Firestore
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                raise ValueError(f"Document {doc_id} not found in database")
            
            metadata = doc_metadata.to_dict()
            user_id = user_data.get('user_id', user_data.get('id'))
            
            if metadata['owner_id'] != user_id:
                raise PermissionError(f"User cannot delete document {doc_id}")
            
            # Get user credentials
            creds = await self._get_user_credentials(user_data)
            if not creds:
                raise ValueError("Unable to get user credentials for Google Docs")
            
            # Delete from Google Drive
            drive_service = build('drive', 'v3', credentials=creds)
            drive_service.files().delete(fileId=doc_id).execute()
            
            # Delete from Firestore
            doc_ref.delete()
            
            logger.info(f"Document deleted: {doc_id} by user {user_data.get('email')}")
            return True
            
        except HttpError as error:
            logger.error(f"Google API error deleting document: {error}")
            raise
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            raise
    
    def _extract_text_from_document(self, document: Dict) -> str:
        """Extract text content from a Google Docs document"""
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_element in element['paragraph'].get('elements', []):
                    if 'textRun' in text_element:
                        content.append(text_element['textRun'].get('content', ''))
        return ''.join(content)