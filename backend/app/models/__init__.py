# Import all models here to make them available
from .document import Document
from .chat import Chat, Message
from .workflow import Workflow, Node, Edge

# Re-export Base so alembic/env.py can import it as: from app.models import Base
from app.core.db import Base

# Make all models and Base available when importing from app.models
__all__ = [
    "Base",
    "Document",
    "Chat",
    "Message",
    "Workflow",
    "Node",
    "Edge",
]