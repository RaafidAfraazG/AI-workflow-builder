from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List

class ChatCreate(BaseModel):
    workflow_id: UUID

class ChatResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class MessageCreate(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: UUID
    chat_id: UUID
    content: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class StreamToken(BaseModel):
    token: str