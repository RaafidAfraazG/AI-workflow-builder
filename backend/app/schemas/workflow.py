from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

class NodePosition(BaseModel):
    x: float
    y: float

class NodeData(BaseModel):
    label: str
    config: Dict[str, Any] = {}

class NodeCreate(BaseModel):
    id: str
    type: str
    position: NodePosition
    data: NodeData

class NodeResponse(NodeCreate):
    pass

class EdgeCreate(BaseModel):
    id: str
    source: str
    target: str
    type: str = "default"

class EdgeResponse(EdgeCreate):
    pass

class WorkflowCreate(BaseModel):
    name: str
    nodes: List[NodeCreate] = []
    edges: List[EdgeCreate] = []

class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    nodes: List[NodeResponse]
    edges: List[EdgeResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True