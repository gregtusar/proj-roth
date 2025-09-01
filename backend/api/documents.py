from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

from api.auth import get_current_user
from services.user_google_docs_service import UserGoogleDocsService

logger = logging.getLogger(__name__)
router = APIRouter()

docs_service = UserGoogleDocsService()

class CreateDocumentRequest(BaseModel):
    title: str
    content: Optional[str] = ""

class UpdateDocumentRequest(BaseModel):
    content: str

class DocumentResponse(BaseModel):
    doc_id: str
    title: str
    url: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DocumentContentResponse(BaseModel):
    doc_id: str
    title: str
    content: str
    url: str
    metadata: Dict

@router.post("/documents", response_model=DocumentResponse)
async def create_document(
    request: CreateDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await docs_service.create_document(
            title=request.title,
            content=request.content,
            user_data=current_user
        )
        
        return DocumentResponse(
            doc_id=result['doc_id'],
            title=result['title'],
            url=result['url'],
            created_at=result['created_at'].isoformat() if result.get('created_at') else None,
            updated_at=result['updated_at'].isoformat() if result.get('updated_at') else None
        )
    except Exception as e:
        logger.error(f"Error creating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document: {str(e)}"
        )

@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_user: dict = Depends(get_current_user)
):
    try:
        documents = await docs_service.list_user_documents(user_data=current_user)
        
        return [
            DocumentResponse(
                doc_id=doc['doc_id'],
                title=doc['title'],
                url=doc['url'],
                created_at=doc.get('created_at'),
                updated_at=doc.get('updated_at')
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )

@router.get("/documents/{doc_id}", response_model=DocumentContentResponse)
async def get_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        document = await docs_service.read_document(
            doc_id=doc_id,
            user_data=current_user
        )
        
        return DocumentContentResponse(
            doc_id=document['doc_id'],
            title=document['title'],
            content=document['content'],
            url=document['url'],
            metadata=document['metadata']
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document: {str(e)}"
        )

@router.put("/documents/{doc_id}")
async def update_document(
    doc_id: str,
    request: UpdateDocumentRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await docs_service.update_document(
            doc_id=doc_id,
            content=request.content,
            user_data=current_user
        )
        
        return result
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document: {str(e)}"
        )

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        success = await docs_service.delete_document(
            doc_id=doc_id,
            user_data=current_user
        )
        
        if success:
            return {"status": "deleted", "doc_id": doc_id}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document"
            )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )