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
from app.schemas.chat import ChatResponse, MessageCreate, StreamToken
from app.schemas.common import SuccessResponse
from app.runners.orchestrator import WorkflowOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=WorkflowResponse)
async def create_workflow(workflow: WorkflowCreate, db: Session = Depends(get_db)):
    try:
        logger.info(f"Creating workflow: {workflow.name}")
        logger.info(f"Nodes: {len(workflow.nodes)}, Edges: {len(workflow.edges)}")
        
        # Create workflow
        db_workflow = Workflow(name=workflow.name)
        db.add(db_workflow)
        db.flush()  # Get the ID without committing
        
        logger.info(f"Created workflow with ID: {db_workflow.id}")

        # Add nodes
        db_nodes = []
        for node in workflow.nodes:
            logger.info(f"Adding node: {node.id} of type {node.type}")
            db_node = Node(
                id=node.id,
                workflow_id=db_workflow.id,
                type=node.type,
                position_x=str(node.position.x),
                position_y=str(node.position.y),
                data=node.data.dict()
            )
            db.add(db_node)
            db_nodes.append(db_node)

        # Add edges with unique IDs
        db_edges = []
        for edge in workflow.edges:
            # Generate unique edge ID using UUID to avoid conflicts
            unique_edge_id = str(uuid4())
            logger.info(f"Adding edge: {unique_edge_id} from {edge.source} to {edge.target} (original ID: {edge.id})")
            db_edge = Edge(
                id=unique_edge_id,
                workflow_id=db_workflow.id,
                source=edge.source,
                target=edge.target,
                type=edge.type
            )
            db.add(db_edge)
            db_edges.append(db_edge)

        # Commit all changes
        db.commit()
        db.refresh(db_workflow)
        
        # Manually construct response to avoid serialization issues
        response_nodes = []
        for db_node in db_nodes:
            node_data = {
                "id": db_node.id,
                "type": db_node.type,
                "position": {
                    "x": float(db_node.position_x),
                    "y": float(db_node.position_y)
                },
                "data": db_node.data
            }
            response_nodes.append(NodeResponse(**node_data))
        
        response_edges = []
        for db_edge in db_edges:
            edge_data = {
                "id": db_edge.id,
                "source": db_edge.source,
                "target": db_edge.target,
                "type": db_edge.type
            }
            response_edges.append(EdgeResponse(**edge_data))
        
        # Create response
        response = WorkflowResponse(
            id=db_workflow.id,
            name=db_workflow.name,
            nodes=response_nodes,
            edges=response_edges,
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at
        )
        
        logger.info(f"Successfully created workflow: {db_workflow.id}")
        return response
        
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        # Query workflow
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Query nodes and edges separately
        nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()
        
        # Manually construct response
        response_nodes = []
        for node in nodes:
            node_data = {
                "id": node.id,
                "type": node.type,
                "position": {
                    "x": float(node.position_x),
                    "y": float(node.position_y)
                },
                "data": node.data
            }
            response_nodes.append(NodeResponse(**node_data))
        
        response_edges = []
        for edge in edges:
            edge_data = {
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "type": edge.type
            }
            response_edges.append(EdgeResponse(**edge_data))
        
        response = WorkflowResponse(
            id=workflow.id,
            name=workflow.name,
            nodes=response_nodes,
            edges=response_edges,
            created_at=workflow.created_at,
            updated_at=workflow.updated_at
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching workflow: {str(e)}")

@router.post("/{workflow_id}/build", response_model=SuccessResponse)
async def build_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Load nodes and edges for validation
        nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()
        
        logger.info(f"Building workflow {workflow_id}")
        logger.info(f"Found {len(nodes)} nodes: {[n.type for n in nodes]}")
        logger.info(f"Found {len(edges)} edges: {[(e.source, e.target) for e in edges]}")
        
        # Set relationships for orchestrator
        workflow.nodes = nodes
        workflow.edges = edges
        
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

@router.post("/{workflow_id}/chat", response_model=ChatResponse)
async def create_chat(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        chat = Chat(workflow_id=workflow_id)
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

@router.post("/{workflow_id}/chat/{chat_id}/message")
async def send_message(
    workflow_id: UUID, 
    chat_id: UUID, 
    message: MessageCreate, 
    db: Session = Depends(get_db)
):
    try:
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
        
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Load workflow relationships for orchestrator
        nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()
        workflow.nodes = nodes
        workflow.edges = edges

        # Save user message
        user_message = Message(
            chat_id=chat_id,
            content=message.content,
            role="user"
        )
        db.add(user_message)
        db.commit()

        async def generate_stream():
            orchestrator = WorkflowOrchestrator()
            assistant_content = ""
            
            try:
                async for token in orchestrator.run_workflow(workflow, message.content, db):
                    assistant_content += token
                    yield f"data: {StreamToken(token=token).json()}\n\n"
                
                # Save assistant message
                assistant_message = Message(
                    chat_id=chat_id,
                    content=assistant_content,
                    role="assistant"
                )
                db.add(assistant_message)
                db.commit()
                
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}")
                yield f"data: {{'error': '{str(e)}'}}\n\n"
            finally:
                yield f"data: [DONE]\n\n"

        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")