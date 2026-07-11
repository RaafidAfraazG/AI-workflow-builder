from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID, uuid4
import json
import logging

from app.core.db import get_db
from app.models.workflow import Workflow, Node, Edge
from app.models.chat import Chat, Message
from app.schemas.workflow import WorkflowCreate, WorkflowResponse, NodeResponse, EdgeResponse
from app.schemas.chat import ChatResponse, MessageCreate, StreamToken, ChatCreate, ChatUpdate, ChatWithMessagesResponse
from app.schemas.common import SuccessResponse
from app.runners.orchestrator import WorkflowOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


def _build_workflow_response(workflow: Workflow, nodes: List[Node], edges: List[Edge]) -> WorkflowResponse:
    """Helper to construct a WorkflowResponse from ORM objects."""
    response_nodes = [
        NodeResponse(
            id=n.id,
            type=n.type,
            position={"x": float(n.position_x), "y": float(n.position_y)},
            data=n.data,
        )
        for n in nodes
    ]
    response_edges = [
        EdgeResponse(id=e.id, source=e.source, target=e.target, type=e.type)
        for e in edges
    ]
    return WorkflowResponse(
        id=workflow.id,
        name=workflow.name,
        nodes=response_nodes,
        edges=response_edges,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


# ---------------------------------------------------------------------------
# GET / — list all workflows
# ---------------------------------------------------------------------------
@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(db: Session = Depends(get_db)):
    try:
        workflows = db.query(Workflow).order_by(Workflow.created_at.desc()).all()
        results = []
        for wf in workflows:
            nodes = db.query(Node).filter(Node.workflow_id == wf.id).all()
            edges = db.query(Edge).filter(Edge.workflow_id == wf.id).all()
            results.append(_build_workflow_response(wf, nodes, edges))
        return results
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing workflows: {str(e)}")


# ---------------------------------------------------------------------------
# POST / — create workflow
# ---------------------------------------------------------------------------
@router.post("/", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Creating workflow: {workflow.name}")
        logger.info(f"Nodes: {len(workflow.nodes)}, Edges: {len(workflow.edges)}")

        db_workflow = Workflow(name=workflow.name)
        db.add(db_workflow)
        db.flush()

        logger.info(f"Created workflow with ID: {db_workflow.id}")

        db_nodes = []
        for node in workflow.nodes:
            logger.info(f"Adding node: {node.id} of type {node.type}")
            db_node = Node(
                id=node.id,
                workflow_id=db_workflow.id,
                type=node.type,
                position_x=str(node.position.x),
                position_y=str(node.position.y),
                data=node.data.model_dump(),
            )
            db.add(db_node)
            db_nodes.append(db_node)

        db_edges = []
        for edge in workflow.edges:
            unique_edge_id = str(uuid4())
            logger.info(f"Adding edge: {unique_edge_id} from {edge.source} to {edge.target}")
            db_edge = Edge(
                id=unique_edge_id,
                workflow_id=db_workflow.id,
                source=edge.source,
                target=edge.target,
                type=edge.type,
            )
            db.add(db_edge)
            db_edges.append(db_edge)

        db.commit()
        db.refresh(db_workflow)

        response = _build_workflow_response(db_workflow, db_nodes, db_edges)
        logger.info(f"Successfully created workflow: {db_workflow.id}")
        return response

    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")


# ---------------------------------------------------------------------------
# GET /{workflow_id} — get single workflow
# ---------------------------------------------------------------------------
@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()

        return _build_workflow_response(workflow, nodes, edges)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching workflow: {str(e)}")


# ---------------------------------------------------------------------------
# PUT /{workflow_id} — update workflow (replace nodes/edges)
# ---------------------------------------------------------------------------
@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: UUID, workflow: WorkflowCreate, db: Session = Depends(get_db)):
    try:
        db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not db_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        db_workflow.name = workflow.name

        # Delete existing nodes and edges
        db.query(Node).filter(Node.workflow_id == workflow_id).delete()
        db.query(Edge).filter(Edge.workflow_id == workflow_id).delete()
        db.flush()

        db_nodes = []
        for node in workflow.nodes:
            db_node = Node(
                id=node.id,
                workflow_id=workflow_id,
                type=node.type,
                position_x=str(node.position.x),
                position_y=str(node.position.y),
                data=node.data.model_dump(),
            )
            db.add(db_node)
            db_nodes.append(db_node)

        db_edges = []
        for edge in workflow.edges:
            db_edge = Edge(
                id=str(uuid4()),
                workflow_id=workflow_id,
                source=edge.source,
                target=edge.target,
                type=edge.type,
            )
            db.add(db_edge)
            db_edges.append(db_edge)

        db.commit()
        db.refresh(db_workflow)

        logger.info(f"Successfully updated workflow: {workflow_id}")
        return _build_workflow_response(db_workflow, db_nodes, db_edges)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE /{workflow_id} — delete workflow
# ---------------------------------------------------------------------------
@router.delete("/{workflow_id}", response_model=SuccessResponse)
async def delete_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not db_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        db.delete(db_workflow)
        db.commit()
        logger.info(f"Deleted workflow: {workflow_id}")
        return SuccessResponse(message="Workflow deleted successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")


# ---------------------------------------------------------------------------
# POST /{workflow_id}/build — validate workflow
# ---------------------------------------------------------------------------
@router.post("/{workflow_id}/build", response_model=SuccessResponse)
async def build_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # nodes/edges are already loaded via selectin — no manual assignment needed
        logger.info(f"Building workflow {workflow_id}")
        logger.info(f"Found {len(workflow.nodes)} nodes: {[n.type for n in workflow.nodes]}")
        logger.info(f"Found {len(workflow.edges)} edges: {[(e.source, e.target) for e in workflow.edges]}")

        orchestrator = WorkflowOrchestrator()
        try:
            orchestrator.validate_workflow(workflow)
            logger.info("Workflow validation passed")
            return SuccessResponse(message="Workflow built successfully")
        except ValueError as validation_error:
            logger.error(f"Validation error: {str(validation_error)}")
            raise HTTPException(status_code=400, detail=str(validation_error))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error building workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error building workflow: {str(e)}")


# ---------------------------------------------------------------------------
# GET /{workflow_id}/chats — list chats for a workflow
# ---------------------------------------------------------------------------
@router.get("/{workflow_id}/chats", response_model=List[ChatResponse])
async def list_chats(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        chats = db.query(Chat).filter(Chat.workflow_id == workflow_id).order_by(Chat.created_at.desc()).all()
        return chats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing chats: {str(e)}")


# ---------------------------------------------------------------------------
# GET /{workflow_id}/chat/{chat_id} — get a specific chat with messages
# ---------------------------------------------------------------------------
@router.get("/{workflow_id}/chat/{chat_id}", response_model=ChatWithMessagesResponse)
async def get_chat(workflow_id: UUID, chat_id: UUID, db: Session = Depends(get_db)):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.workflow_id == workflow_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        return chat
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching chat: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching chat: {str(e)}")


# ---------------------------------------------------------------------------
# PUT /{workflow_id}/chat/{chat_id} — update chat (title)
# ---------------------------------------------------------------------------
@router.put("/{workflow_id}/chat/{chat_id}", response_model=ChatResponse)
async def update_chat(workflow_id: UUID, chat_id: UUID, chat_update: ChatUpdate, db: Session = Depends(get_db)):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.workflow_id == workflow_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        chat.title = chat_update.title
        db.commit()
        db.refresh(chat)
        return chat
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating chat: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating chat: {str(e)}")


# ---------------------------------------------------------------------------
# DELETE /{workflow_id}/chat/{chat_id} — delete chat
# ---------------------------------------------------------------------------
@router.delete("/{workflow_id}/chat/{chat_id}", response_model=SuccessResponse)
async def delete_chat(workflow_id: UUID, chat_id: UUID, db: Session = Depends(get_db)):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id, Chat.workflow_id == workflow_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        db.delete(chat)
        db.commit()
        return SuccessResponse(message="Chat deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting chat: {str(e)}")


# ---------------------------------------------------------------------------
# POST /{workflow_id}/chat — create chat session
# ---------------------------------------------------------------------------
@router.post("/{workflow_id}/chat", response_model=ChatResponse)
async def create_chat(workflow_id: UUID, chat_in: ChatCreate = None, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        title = chat_in.title if chat_in and chat_in.title else "New Chat"
        chat = Chat(workflow_id=workflow_id, title=title)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating chat: {str(e)}")


# ---------------------------------------------------------------------------
# POST /{workflow_id}/chat/{chat_id}/message — send message & stream response
# ---------------------------------------------------------------------------
@router.post("/{workflow_id}/chat/{chat_id}/message")
async def send_message(
    workflow_id: UUID,
    chat_id: UUID,
    message: MessageCreate,
    db: Session = Depends(get_db),
):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # nodes/edges are loaded via selectin — workflow.nodes and workflow.edges are ready
        logger.info(f"Workflow has {len(workflow.nodes)} nodes, {len(workflow.edges)} edges")

        # Save user message
        user_message = Message(chat_id=chat_id, content=message.content, role="user")
        db.add(user_message)
        db.commit()

        # Snapshot nodes/edges as plain data so they survive session closure inside the generator
        nodes_snapshot = list(workflow.nodes)
        edges_snapshot = list(workflow.edges)
        workflow.nodes = nodes_snapshot
        workflow.edges = edges_snapshot

        async def generate_stream():
            orchestrator = WorkflowOrchestrator()
            assistant_content = ""

            try:
                async for token in orchestrator.run_workflow(workflow, message.content, db):
                    assistant_content += token
                    yield f"data: {StreamToken(token=token).model_dump_json()}\n\n"

                assistant_message = Message(
                    chat_id=chat_id,
                    content=assistant_content,
                    role="assistant",
                )
                db.add(assistant_message)
                db.commit()

            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
            finally:
                yield "data: [DONE]\n\n"

        return StreamingResponse(generate_stream(), media_type="text/event-stream")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")