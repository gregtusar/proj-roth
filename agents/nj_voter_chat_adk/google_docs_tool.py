import logging
from typing import Dict, List, Optional, Any
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore
import os
from datetime import datetime
import json
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))
from services.oauth_token_service import OAuthTokenService

logger = logging.getLogger(__name__)

class GoogleDocsTool:
    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "proj-roth")
        self.db = firestore.Client(project=self.project_id)
        self.oauth_service = OAuthTokenService()
        self.shared_folder_id = None
        self._load_config()
        # Don't initialize services here - we'll do it per-request with user credentials
    
    def _load_config(self):
        """Load the shared folder configuration"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'google_drive_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.shared_folder_id = config.get('shared_folder_id')
                    logger.info(f"Loaded shared folder ID: {self.shared_folder_id}")
            else:
                logger.warning("No google_drive_config.json found")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    async def _get_user_services(self, user_id: str):
        """Get Google services with user OAuth credentials"""
        try:
            # Get user's OAuth credentials from token service
            creds = await self.oauth_service.get_valid_credentials(user_id)
            if not creds:
                logger.error(f"No OAuth credentials found for user {user_id}")
                return None, None
            
            # Build services with user credentials
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            return docs_service, drive_service
        except Exception as e:
            logger.error(f"Failed to get user services: {e}")
            return None, None
    
    async def create_document(self, title: str, content: str, user_id: str) -> str:
        """
        Create a new Google Doc with the specified title and content.
        
        Args:
            title: The title of the document
            content: The initial content of the document
            user_id: The ID of the user creating the document
            
        Returns:
            A JSON string containing the document details
        """
        try:
            # Get user-specific services
            docs_service, drive_service = await self._get_user_services(user_id)
            if not docs_service:
                return json.dumps({'error': 'Unable to get user OAuth credentials. Please re-login with Google Docs permissions.'})
            
            document = {
                'title': title
            }
            
            # First create the document with user's credentials
            doc = docs_service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            
            # Then move it to the shared folder if configured
            if self.shared_folder_id and drive_service:
                try:
                    # Get the document's current parents
                    file = drive_service.files().get(
                        fileId=doc_id,
                        fields='parents'
                    ).execute()
                    
                    # Move the document to the shared folder
                    previous_parents = ",".join(file.get('parents', []))
                    if previous_parents:
                        drive_service.files().update(
                            fileId=doc_id,
                            addParents=self.shared_folder_id,
                            removeParents=previous_parents,
                            fields='id, parents'
                        ).execute()
                    else:
                        drive_service.files().update(
                            fileId=doc_id,
                            addParents=self.shared_folder_id,
                            fields='id, parents'
                        ).execute()
                    
                    logger.info(f"Moved document {doc_id} to shared folder {self.shared_folder_id}")
                except Exception as e:
                    logger.warning(f"Could not move document to shared folder: {e}")
                    # Continue even if moving fails
            
            if content:
                requests = [
                    {
                        'insertText': {
                            'location': {
                                'index': 1,
                            },
                            'text': content
                        }
                    }
                ]
                docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
            
            doc_metadata = {
                'doc_id': doc_id,
                'title': title,
                'owner_id': user_id,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'url': f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
            self.db.collection('user_documents').document(doc_id).set(doc_metadata)
            
            logger.info(f"Document created: {doc_id} for user {user_id}")
            
            result = {
                'doc_id': doc_id,
                'title': title,
                'url': doc_metadata['url'],
                'message': f"Document '{title}' created successfully"
            }
            
            return json.dumps(result)
            
        except HttpError as error:
            logger.error(f"Error creating document: {error}")
            return json.dumps({'error': f"Failed to create document: {str(error)}"})
        except Exception as e:
            logger.error(f"Error creating document: {e}")
            return json.dumps({'error': f"Failed to create document: {str(e)}"})
    
    async def read_document(self, doc_id: str, user_id: str) -> str:
        """
        Read the content of a Google Doc.
        
        Args:
            doc_id: The ID of the document to read
            user_id: The ID of the user requesting the document
            
        Returns:
            A JSON string containing the document content
        """
        try:
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                return json.dumps({'error': f"Document {doc_id} not found"})
            
            metadata = doc_metadata.to_dict()
            if metadata['owner_id'] != user_id:
                return json.dumps({'error': f"You don't have permission to access document {doc_id}"})
            
            # Get user-specific services
            docs_service, _ = await self._get_user_services(metadata['owner_id'])
            if not docs_service:
                return json.dumps({'error': 'Unable to get user OAuth credentials'})
            
            document = docs_service.documents().get(documentId=doc_id).execute()
            
            content = self._extract_text_from_document(document)
            
            result = {
                'doc_id': doc_id,
                'title': document.get('title'),
                'content': content,
                'url': f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
            return json.dumps(result)
            
        except HttpError as error:
            logger.error(f"Error reading document: {error}")
            return json.dumps({'error': f"Failed to read document: {str(error)}"})
        except Exception as e:
            logger.error(f"Error reading document: {e}")
            return json.dumps({'error': f"Failed to read document: {str(e)}"})
    
    async def list_documents(self, user_id: str) -> str:
        """
        List all documents owned by the user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            A JSON string containing the list of documents
        """
        try:
            docs_ref = self.db.collection('user_documents').where('owner_id', '==', user_id)
            docs = docs_ref.order_by('created_at', direction=firestore.Query.DESCENDING).stream()
            
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
            
            result = {
                'documents': documents,
                'count': len(documents),
                'message': f"Found {len(documents)} document(s)"
            }
            
            return json.dumps(result)
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            return json.dumps({'error': f"Failed to list documents: {str(e)}"})
    
    async def update_document(self, doc_id: str, content: str, user_id: str) -> str:
        """
        Update the content of a Google Doc.
        
        Args:
            doc_id: The ID of the document to update
            content: The new content for the document
            user_id: The ID of the user updating the document
            
        Returns:
            A JSON string with the update status
        """
        try:
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                return json.dumps({'error': f"Document {doc_id} not found"})
            
            metadata = doc_metadata.to_dict()
            if metadata['owner_id'] != user_id:
                return json.dumps({'error': f"You don't have permission to update document {doc_id}"})
            
            # Get user-specific services
            docs_service, _ = await self._get_user_services(user_id)
            if not docs_service:
                return json.dumps({'error': 'Unable to get user OAuth credentials'})
            
            document = docs_service.documents().get(documentId=doc_id).execute()
            end_index = document['body']['content'][-1]['endIndex'] - 1
            
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
                        'location': {
                            'index': 1,
                        },
                        'text': content
                    }
                }
            ]
            
            docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            doc_ref.update({
                'updated_at': datetime.utcnow()
            })
            
            logger.info(f"Document updated: {doc_id} for user {user_id}")
            
            result = {
                'doc_id': doc_id,
                'status': 'updated',
                'message': f"Document {doc_id} updated successfully",
                'url': f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
            return json.dumps(result)
            
        except HttpError as error:
            logger.error(f"Error updating document: {error}")
            return json.dumps({'error': f"Failed to update document: {str(error)}"})
        except Exception as e:
            logger.error(f"Error updating document: {e}")
            return json.dumps({'error': f"Failed to update document: {str(e)}"})
    
    def _extract_text_from_document(self, document: Dict) -> str:
        """Extract text content from a Google Docs document structure."""
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_element in element['paragraph'].get('elements', []):
                    if 'textRun' in text_element:
                        content.append(text_element['textRun'].get('content', ''))
        return ''.join(content)