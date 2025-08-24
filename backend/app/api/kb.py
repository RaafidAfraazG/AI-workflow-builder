import os
import logging
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, KnowledgeBaseSearchResult
from app.schemas.common import SuccessResponse
from app.services.kb_service import KnowledgeBaseService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    collection: str = Form("default"),
    db: Session = Depends(get_db),
):
    """
    Upload a PDF to disk and create a DB record.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    kb_service = KnowledgeBaseService(db)
    try:
        return await kb_service.upload_document(file, collection)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/ingest/{document_id}", response_model=SuccessResponse)
async def ingest_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Extract text, embed, and push chunks to vector DB for a document.
    """
    kb_service = KnowledgeBaseService(db)
    try:
        return await kb_service.ingest_document(document_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/search", response_model=List[KnowledgeBaseSearchResult])
async def search_documents(
    query: str,
    collection: str = "default",
    top_k: int = 5,
    db: Session = Depends(get_db),
):
    """
    Semantic search against a collection.
    """
    kb_service = KnowledgeBaseService(db)
    try:
        return await kb_service.search_documents(query, collection, top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Fetch a single document by its ID
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.model_validate(document)


@router.delete("/{document_id}", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a document: file on disk, DB row, and vector store entries.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Initialize service first
        kb_service = KnowledgeBaseService(db)
        
        # Store file path before deletion
        file_path = document.file_path
        
        # Step 1: Remove from vector store first (this can fail without affecting DB)
        try:
            await kb_service.delete_document(document_id)
        except Exception as e:
            logger.warning(f"Failed to delete from vector store: {str(e)}")
            # Continue with deletion even if vector store fails
        
        # Step 2: Remove file from disk
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {str(e)}")
                # Continue with DB deletion even if file deletion fails
        
        # Step 3: Remove from database (this should be last)
        db.delete(document)
        db.commit()
        
        return SuccessResponse(message=f"Document {document_id} deleted successfully")
        
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
