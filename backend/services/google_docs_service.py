import logging
from typing import Dict, List, Optional, Any
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import firestore
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleDocsService:
    def __init__(self):
        self.project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "proj-roth")
        self.service = None
        self.drive_service = None
        self.db = firestore.Client(project=self.project_id)
        self.shared_folder_id = None
        self._load_config()
        self._initialize_services()
    
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
    
    def _initialize_services(self):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'),
                scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/drive'
                ]
            ) if os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') else None
            
            if not credentials:
                from google.auth import default
                credentials, _ = default(scopes=[
                    'https://www.googleapis.com/auth/documents',
                    'https://www.googleapis.com/auth/drive'
                ])
            
            self.service = build('docs', 'v1', credentials=credentials)
            self.drive_service = build('drive', 'v3', credentials=credentials)
            logger.info("Google Docs services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Docs services: {e}")
            raise
    
    async def create_document(self, title: str, content: str, user_id: str) -> Dict[str, Any]:
        try:
            document = {
                'title': title
            }
            
            # First create the document
            doc = self.service.documents().create(body=document).execute()
            doc_id = doc.get('documentId')
            
            # Then move it to the shared folder if configured
            if self.shared_folder_id and self.drive_service:
                try:
                    # Get the document's current parents
                    file = self.drive_service.files().get(
                        fileId=doc_id,
                        fields='parents'
                    ).execute()
                    
                    # Move the document to the shared folder
                    previous_parents = ",".join(file.get('parents', []))
                    if previous_parents:
                        self.drive_service.files().update(
                            fileId=doc_id,
                            addParents=self.shared_folder_id,
                            removeParents=previous_parents,
                            fields='id, parents'
                        ).execute()
                    else:
                        self.drive_service.files().update(
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
                self.service.documents().batchUpdate(
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
            return doc_metadata
            
        except HttpError as error:
            logger.error(f"Error creating document: {error}")
            raise
    
    async def read_document(self, doc_id: str, user_id: str) -> Dict[str, Any]:
        try:
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                raise ValueError(f"Document {doc_id} not found in database")
            
            metadata = doc_metadata.to_dict()
            if metadata['owner_id'] != user_id:
                raise PermissionError(f"User {user_id} does not have access to document {doc_id}")
            
            document = self.service.documents().get(documentId=doc_id).execute()
            
            content = self._extract_text_from_document(document)
            
            return {
                'doc_id': doc_id,
                'title': document.get('title'),
                'content': content,
                'metadata': metadata,
                'url': f"https://docs.google.com/document/d/{doc_id}/edit"
            }
            
        except HttpError as error:
            logger.error(f"Error reading document: {error}")
            raise
    
    async def list_user_documents(self, user_id: str) -> List[Dict[str, Any]]:
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
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing user documents: {e}")
            raise
    
    async def update_document(self, doc_id: str, content: str, user_id: str) -> Dict[str, Any]:
        try:
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                raise ValueError(f"Document {doc_id} not found in database")
            
            metadata = doc_metadata.to_dict()
            if metadata['owner_id'] != user_id:
                raise PermissionError(f"User {user_id} does not have access to document {doc_id}")
            
            document = self.service.documents().get(documentId=doc_id).execute()
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
            
            self.service.documents().batchUpdate(
                documentId=doc_id,
                body={'requests': requests}
            ).execute()
            
            doc_ref.update({
                'updated_at': datetime.utcnow()
            })
            
            logger.info(f"Document updated: {doc_id} for user {user_id}")
            return {'doc_id': doc_id, 'status': 'updated'}
            
        except HttpError as error:
            logger.error(f"Error updating document: {error}")
            raise
    
    async def delete_document(self, doc_id: str, user_id: str) -> bool:
        try:
            doc_ref = self.db.collection('user_documents').document(doc_id)
            doc_metadata = doc_ref.get()
            
            if not doc_metadata.exists:
                raise ValueError(f"Document {doc_id} not found in database")
            
            metadata = doc_metadata.to_dict()
            if metadata['owner_id'] != user_id:
                raise PermissionError(f"User {user_id} does not have access to document {doc_id}")
            
            self.drive_service.files().delete(fileId=doc_id).execute()
            
            doc_ref.delete()
            
            logger.info(f"Document deleted: {doc_id} for user {user_id}")
            return True
            
        except HttpError as error:
            logger.error(f"Error deleting document: {error}")
            raise
    
    def _extract_text_from_document(self, document: Dict) -> str:
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_element in element['paragraph'].get('elements', []):
                    if 'textRun' in text_element:
                        content.append(text_element['textRun'].get('content', ''))
        return ''.join(content)