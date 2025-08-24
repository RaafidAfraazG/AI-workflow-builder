# backend/app/schemas/document.py
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional

class DocumentResponse(BaseModel):
    """Response model for document operations"""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    filename: str
    file_path: str
    content_type: Optional[str] = None
    created_at: datetime
    is_ingested: bool = False

class KnowledgeBaseSearchResult(BaseModel):
    """Search result from knowledge base"""
    id: str
    content: str
    metadata: dict
    score: float

class DocumentUploadRequest(BaseModel):
    """Request model for document upload"""
    collection: str = "default"

class DocumentListResponse(BaseModel):
    """Response model for listing documents"""
    documents: list[DocumentResponse]
    total: int