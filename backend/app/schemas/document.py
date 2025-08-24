from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    file_path: str
    content_type: str
    created_at: datetime
    is_ingested: bool

    class Config:
        from_attributes = True

class KnowledgeBaseSearchResult(BaseModel):
    id: str
    content: str
    metadata: dict
    score: float