import logging
from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
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
        self.oauth_service = OAuthTokenService()
        self.shared_folder_id = None
        self._load_config()
    
    def _load_config(self):
        """Load the shared folder configuration if needed"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'google_drive_config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self.shared_folder_id = config.get('shared_folder_id')
                    logger.info(f"Loaded shared folder ID: {self.shared_folder_id}")
            else:
                logger.debug("No google_drive_config.json found - documents will be created in user's My Drive")
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
            
            # Create the document with user's credentials
            doc = docs_service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            
            # Optionally move to shared folder if configured
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
                    logger.info(f"Moved document {doc_id} to shared folder {self.shared_folder_id}")
                except Exception as e:
                    logger.warning(f"Could not move document to shared folder: {e}")
                    # Continue even if moving fails
            
            # Add initial content if provided
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
            
            logger.info(f"Document created: {doc_id} for user {user_id}")
            
            result = {
                'doc_id': doc_id,
                'title': title,
                'url': f"https://docs.google.com/document/d/{doc_id}/edit",
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
            # Get user-specific services
            docs_service, _ = await self._get_user_services(user_id)
            if not docs_service:
                return json.dumps({'error': 'Unable to get user OAuth credentials. Please re-login with Google Docs permissions.'})
            
            # Fetch the document directly from Google Docs API
            try:
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
                if error.resp.status == 404:
                    return json.dumps({'error': f"Document {doc_id} not found. Please check the document ID."})
                elif error.resp.status == 403:
                    return json.dumps({'error': f"Permission denied: You don't have access to document {doc_id}. Make sure the document is shared with you."})
                else:
                    logger.error(f"Error accessing document: {error}")
                    return json.dumps({'error': f"Failed to read document: {str(error)}"})
            
        except Exception as e:
            logger.error(f"Error reading document: {e}")
            return json.dumps({'error': f"Failed to read document: {str(e)}"})
    
    async def list_documents(self, user_id: str, max_results: int = 20) -> str:
        """
        List documents accessible by the user.
        
        Args:
            user_id: The ID of the user
            max_results: Maximum number of documents to return
            
        Returns:
            A JSON string containing the list of documents
        """
        try:
            # Get user-specific services
            _, drive_service = await self._get_user_services(user_id)
            if not drive_service:
                return json.dumps({'error': 'Unable to get user OAuth credentials. Please re-login with Google Docs permissions.'})
            
            # Query for Google Docs files
            query = "mimeType='application/vnd.google-apps.document'"
            
            # If we have a shared folder, also include it
            if self.shared_folder_id:
                query = f"({query}) or ('{self.shared_folder_id}' in parents and mimeType='application/vnd.google-apps.document')"
            
            # List documents from Google Drive
            results = drive_service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, createdTime, modifiedTime, webViewLink)",
                orderBy="modifiedTime desc"
            ).execute()
            
            files = results.get('files', [])
            
            documents = []
            for file in files:
                documents.append({
                    'doc_id': file['id'],
                    'title': file['name'],
                    'created_at': file.get('createdTime'),
                    'updated_at': file.get('modifiedTime'),
                    'url': file.get('webViewLink', f"https://docs.google.com/document/d/{file['id']}/edit")
                })
            
            result = {
                'documents': documents,
                'count': len(documents),
                'message': f"Found {len(documents)} document(s)"
            }
            
            return json.dumps(result)
            
        except HttpError as error:
            logger.error(f"Error listing documents: {error}")
            return json.dumps({'error': f"Failed to list documents: {str(error)}"})
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
            # Get user-specific services
            docs_service, _ = await self._get_user_services(user_id)
            if not docs_service:
                return json.dumps({'error': 'Unable to get user OAuth credentials. Please re-login with Google Docs permissions.'})
            
            # Get the current document to find the content range
            try:
                document = docs_service.documents().get(documentId=doc_id).execute()
                end_index = document['body']['content'][-1]['endIndex'] - 1
                
                # Clear existing content and insert new content
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
                
                logger.info(f"Document updated: {doc_id} for user {user_id}")
                
                result = {
                    'doc_id': doc_id,
                    'status': 'updated',
                    'message': f"Document {doc_id} updated successfully",
                    'url': f"https://docs.google.com/document/d/{doc_id}/edit"
                }
                
                return json.dumps(result)
                
            except HttpError as error:
                if error.resp.status == 404:
                    return json.dumps({'error': f"Document {doc_id} not found. Please check the document ID."})
                elif error.resp.status == 403:
                    return json.dumps({'error': f"Permission denied: You don't have edit access to document {doc_id}"})
                else:
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