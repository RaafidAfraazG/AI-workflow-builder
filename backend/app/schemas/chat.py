from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import List, Optional

class ChatCreate(BaseModel):
    workflow_id: UUID
    title: Optional[str] = "New Chat"

class ChatUpdate(BaseModel):
    title: str

class ChatResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    title: Optional[str] = None
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

class ChatWithMessagesResponse(ChatResponse):
    messages: List[MessageResponse]

class StreamToken(BaseModel):
    token: str