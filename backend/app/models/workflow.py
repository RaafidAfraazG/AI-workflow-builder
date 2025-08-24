from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.db import Base

class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Fixed relationships with overlaps to prevent warnings
    nodes = relationship("Node", cascade="all, delete-orphan", lazy="select", overlaps="workflow")
    edges = relationship("Edge", cascade="all, delete-orphan", lazy="select", overlaps="workflow")
    chats = relationship("Chat", lazy="select")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(String(255), primary_key=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    position_x = Column(String(50))
    position_y = Column(String(50))
    data = Column(JSON)

    # Fixed relationship with overlaps parameter
    workflow = relationship("Workflow", lazy="select", overlaps="nodes")


class Edge(Base):
    __tablename__ = "edges"

    id = Column(String(255), primary_key=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(255), nullable=False)
    target = Column(String(255), nullable=False)
    type = Column(String(50))

    # Fixed relationship with overlaps parameter
    workflow = relationship("Workflow", lazy="select", overlaps="edges")