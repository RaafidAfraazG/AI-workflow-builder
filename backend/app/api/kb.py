import os
from uuid import UUID
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse, KnowledgeBaseSearchResult
from app.schemas.common import SuccessResponse
from app.services.kb_service import KnowledgeBaseService

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


@router.delete("/{document_id}", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def delete_document(document_id: UUID, db: Session = Depends(get_db)):
    """
    Delete a document: file on disk, DB row, and vector store entries.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # remove file from disk
        if document.file_path and os.path.exists(document.file_path):
            os.remove(document.file_path)

        # remove from DB
        db.delete(document)
        db.commit()

        # remove from vectorstore
        kb_service = KnowledgeBaseService(db)
        await kb_service.delete_document(document_id)

        return SuccessResponse(message=f"Document {document_id} deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")