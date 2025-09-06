from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import uuid
from google.cloud import firestore
import os
import re

from api.auth import get_current_user

router = APIRouter()

class DocumentLink(BaseModel):
    doc_id: str
    user_id: str
    title: str
    url: str
    source: str  # 'manual', 'ai_generated', 'campaign'
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None  # Store additional info like campaign_id, etc.
    
class CreateDocumentLinkRequest(BaseModel):
    title: str
    url: str
    description: Optional[str] = None
    source: str = 'manual'
    metadata: Optional[dict] = None

class DocumentLinkResponse(BaseModel):
    doc_id: str
    title: str
    url: str
    source: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[dict] = None

def get_firestore_client():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "proj-roth")
    return firestore.Client(project=project_id)

def validate_google_doc_url(url: str) -> bool:
    """Validate that URL is a Google Doc or Drive link"""
    google_patterns = [
        r'docs\.google\.com',
        r'drive\.google\.com',
        r'spreadsheets\.google\.com',
        r'forms\.google\.com',
        r'slides\.google\.com'
    ]
    return any(re.search(pattern, url) for pattern in google_patterns)

@router.get("/", response_model=List[DocumentLinkResponse])
async def get_user_document_links(current_user: dict = Depends(get_current_user)):
    """Get all document links for the current user"""
    try:
        db = get_firestore_client()
        docs_ref = db.collection('document_links').where('user_id', '==', current_user['id'])
        docs = docs_ref.stream()
        
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            documents.append(DocumentLinkResponse(
                doc_id=doc.id,
                title=doc_data.get('title', ''),
                url=doc_data.get('url', ''),
                source=doc_data.get('source', 'manual'),
                created_at=doc_data.get('created_at').isoformat() if doc_data.get('created_at') else None,
                updated_at=doc_data.get('updated_at').isoformat() if doc_data.get('updated_at') else None,
                description=doc_data.get('description'),
                metadata=doc_data.get('metadata')
            ))
        
        # Sort by created_at descending (newest first)
        documents.sort(key=lambda x: x.created_at or '', reverse=True)
        return documents
    except Exception as e:
        print(f"Error fetching document links: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch document links")

@router.post("/", response_model=DocumentLinkResponse)
async def create_document_link(
    request: CreateDocumentLinkRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new document link entry"""
    try:
        db = get_firestore_client()
        
        # Validate that URL is a Google Doc URL
        if not validate_google_doc_url(request.url):
            raise HTTPException(
                status_code=400, 
                detail="URL must be a Google Docs, Sheets, Slides, Forms, or Drive link"
            )
        
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        document_data = {
            'doc_id': doc_id,
            'user_id': current_user['id'],
            'user_email': current_user.get('email', ''),
            'title': request.title,
            'url': request.url,
            'source': request.source,
            'description': request.description,
            'metadata': request.metadata or {},
            'created_at': now,
            'updated_at': now
        }
        
        # Save to Firestore
        db.collection('document_links').document(doc_id).set(document_data)
        
        return DocumentLinkResponse(
            doc_id=doc_id,
            title=request.title,
            url=request.url,
            source=request.source,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            description=request.description,
            metadata=request.metadata
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating document link: {e}")
        raise HTTPException(status_code=500, detail="Failed to create document link")

@router.delete("/{doc_id}")
async def delete_document_link(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a document link"""
    try:
        db = get_firestore_client()
        
        # Check if document exists and belongs to user
        doc_ref = db.collection('document_links').document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document link not found")
        
        doc_data = doc.to_dict()
        if doc_data.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to delete this document link")
        
        # Delete the document
        doc_ref.delete()
        
        return {"success": True, "message": "Document link deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting document link: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document link")

@router.put("/{doc_id}")
async def update_document_link(
    doc_id: str,
    request: CreateDocumentLinkRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update a document link"""
    try:
        db = get_firestore_client()
        
        # Validate that URL is a Google Doc URL
        if not validate_google_doc_url(request.url):
            raise HTTPException(
                status_code=400, 
                detail="URL must be a Google Docs, Sheets, Slides, Forms, or Drive link"
            )
        
        # Check if document exists and belongs to user
        doc_ref = db.collection('document_links').document(doc_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Document link not found")
        
        doc_data = doc.to_dict()
        if doc_data.get('user_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="Not authorized to update this document link")
        
        # Update the document
        update_data = {
            'title': request.title,
            'url': request.url,
            'description': request.description,
            'metadata': request.metadata or {},
            'updated_at': datetime.utcnow()
        }
        doc_ref.update(update_data)
        
        # Get updated document
        updated_doc = doc_ref.get().to_dict()
        
        return DocumentLinkResponse(
            doc_id=doc_id,
            title=updated_doc.get('title', ''),
            url=updated_doc.get('url', ''),
            source=updated_doc.get('source', 'manual'),
            created_at=updated_doc.get('created_at').isoformat() if updated_doc.get('created_at') else None,
            updated_at=updated_doc.get('updated_at').isoformat() if updated_doc.get('updated_at') else None,
            description=updated_doc.get('description'),
            metadata=updated_doc.get('metadata')
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating document link: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document link")

# Helper function to be called from other parts of the backend when AI generates a document
async def store_ai_generated_document_link(
    user_id: str, 
    title: str, 
    url: str, 
    description: str = None,
    metadata: dict = None
):
    """Store a document link that was generated by AI"""
    try:
        db = get_firestore_client()
        doc_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        document_data = {
            'doc_id': doc_id,
            'user_id': user_id,
            'title': title,
            'url': url,
            'source': 'ai_generated',
            'description': description or f"AI-generated document created on {now.strftime('%Y-%m-%d')}",
            'metadata': metadata or {},
            'created_at': now,
            'updated_at': now
        }
        
        db.collection('document_links').document(doc_id).set(document_data)
        return doc_id
    except Exception as e:
        print(f"Error storing AI-generated document link: {e}")
        return None