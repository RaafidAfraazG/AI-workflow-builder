from sqlalchemy.orm import declarative_base

# Create a single Base for all models
Base = declarative_base()

# Import all models so they are registered with Base
from .workflow import Workflow, Node, Edge
from .document import Document
from .chat import Chat, Message

# Optional: define what is exported when using 'from app.models import *'
__all__ = ["Base", "Workflow", "Node", "Edge", "Document", "Chat", "Message"]
