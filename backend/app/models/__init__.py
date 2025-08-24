# Import all models here to make them available
from .document import Document
from .chat import Chat, Message
from .workflow import Workflow, Node, Edge

# Make all models available when importing from app.models
__all__ = [
    "Document",
    "Chat", 
    "Message",
    "Workflow",
    "Node", 
    "Edge"
]