from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from typing import List
from uuid import UUID, uuid4
import json
import logging
import time

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
    start_time = time.time()
    
    try:
        logger.info(f"Creating workflow: {workflow.name}")
        logger.info(f"Nodes: {len(workflow.nodes)}, Edges: {len(workflow.edges)}")
        
        # OPTIMIZATION 1: Use bulk operations instead of individual adds
        db_start = time.time()
        
        # Create workflow
        db_workflow = Workflow(name=workflow.name)
        db.add(db_workflow)
        db.flush()  # Get the ID without committing
        
        logger.info(f"Workflow creation took: {time.time() - db_start:.3f}s")
        
        # OPTIMIZATION 2: Prepare all nodes and edges in memory first
        nodes_start = time.time()
        db_nodes = []
        db_edges = []
        node_id_mapping = {}
        
        # Prepare nodes
        for node in workflow.nodes:
            unique_node_id = f"{db_workflow.id}_{node.id}"
            node_id_mapping[node.id] = unique_node_id
            
            db_node = Node(
                id=unique_node_id,
                workflow_id=db_workflow.id,
                type=node.type,
                position_x=str(node.position.x),
                position_y=str(node.position.y),
                data=node.data.dict()
            )
            db_nodes.append(db_node)

        # Prepare edges
        for edge in workflow.edges:
            unique_edge_id = str(uuid4())
            mapped_source = node_id_mapping.get(edge.source, edge.source)
            mapped_target = node_id_mapping.get(edge.target, edge.target)
            
            db_edge = Edge(
                id=unique_edge_id,
                workflow_id=db_workflow.id,
                source=mapped_source,
                target=mapped_target,
                type=edge.type
            )
            db_edges.append(db_edge)
        
        logger.info(f"Node/Edge preparation took: {time.time() - nodes_start:.3f}s")
        
        # OPTIMIZATION 3: Use bulk_save_objects for better performance
        bulk_start = time.time()
        db.bulk_save_objects(db_nodes)
        db.bulk_save_objects(db_edges)
        logger.info(f"Bulk save took: {time.time() - bulk_start:.3f}s")

        # Commit all changes
        commit_start = time.time()
        db.commit()
        db.refresh(db_workflow)
        logger.info(f"Commit took: {time.time() - commit_start:.3f}s")
        
        # OPTIMIZATION 4: Build response more efficiently
        response_start = time.time()
        response_nodes = [
            NodeResponse(
                id=workflow.nodes[i].id,
                type=db_node.type,
                position={
                    "x": float(db_node.position_x),
                    "y": float(db_node.position_y)
                },
                data=db_node.data
            ) for i, db_node in enumerate(db_nodes)
        ]
        
        response_edges = [
            EdgeResponse(
                id=workflow.edges[i].id,
                source=workflow.edges[i].source,
                target=workflow.edges[i].target,
                type=db_edge.type
            ) for i, db_edge in enumerate(db_edges)
        ]
        logger.info(f"Response building took: {time.time() - response_start:.3f}s")
        
        response = WorkflowResponse(
            id=db_workflow.id,
            name=db_workflow.name,
            nodes=response_nodes,
            edges=response_edges,
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at
        )
        
        total_time = time.time() - start_time
        logger.info(f"Successfully created workflow in {total_time:.3f}s")
        return response
        
    except IntegrityError as ie:
        logger.error(f"Database integrity error: {str(ie)}")
        db.rollback()
        raise HTTPException(status_code=409, detail="Duplicate node or edge IDs detected. Please refresh and try again.")
    except Exception as e:
        logger.error(f"Error creating workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

# OPTIMIZATION 5: Use JOIN queries instead of separate queries
@router.get("/", response_model=List[WorkflowResponse])
async def get_all_workflows(db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        # Single query with joins instead of multiple queries
        query = text("""
            SELECT 
                w.id as workflow_id, w.name, w.created_at, w.updated_at,
                n.id as node_id, n.type as node_type, n.position_x, n.position_y, n.data as node_data,
                e.id as edge_id, e.source, e.target, e.type as edge_type
            FROM workflows w
            LEFT JOIN nodes n ON w.id = n.workflow_id
            LEFT JOIN edges e ON w.id = e.workflow_id
            ORDER BY w.updated_at DESC
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        # Group results by workflow
        workflows_dict = {}
        for row in rows:
            workflow_id = row.workflow_id
            if workflow_id not in workflows_dict:
                workflows_dict[workflow_id] = {
                    'workflow': {
                        'id': workflow_id,
                        'name': row.name,
                        'created_at': row.created_at,
                        'updated_at': row.updated_at
                    },
                    'nodes': {},
                    'edges': {}
                }
            
            # Add node if exists
            if row.node_id:
                original_id = row.node_id.split('_', 1)[1] if '_' in row.node_id else row.node_id
                workflows_dict[workflow_id]['nodes'][row.node_id] = {
                    'id': original_id,
                    'type': row.node_type,
                    'position': {'x': float(row.position_x), 'y': float(row.position_y)},
                    'data': row.node_data
                }
            
            # Add edge if exists
            if row.edge_id:
                original_source = row.source.split('_', 1)[1] if '_' in row.source else row.source
                original_target = row.target.split('_', 1)[1] if '_' in row.target else row.target
                workflows_dict[workflow_id]['edges'][row.edge_id] = {
                    'id': row.edge_id,
                    'source': original_source,
                    'target': original_target,
                    'type': row.edge_type
                }
        
        # Build response
        response_workflows = []
        for workflow_data in workflows_dict.values():
            workflow_response = WorkflowResponse(
                id=workflow_data['workflow']['id'],
                name=workflow_data['workflow']['name'],
                nodes=[NodeResponse(**node) for node in workflow_data['nodes'].values()],
                edges=[EdgeResponse(**edge) for edge in workflow_data['edges'].values()],
                created_at=workflow_data['workflow']['created_at'],
                updated_at=workflow_data['workflow']['updated_at']
            )
            response_workflows.append(workflow_response)
        
        total_time = time.time() - start_time
        logger.info(f"Fetched {len(response_workflows)} workflows in {total_time:.3f}s")
        return response_workflows
        
    except Exception as e:
        logger.error(f"Error fetching workflows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching workflows: {str(e)}")

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: UUID, workflow: WorkflowCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        logger.info(f"Updating workflow: {workflow_id}")
        
        # Get existing workflow
        db_workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not db_workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update workflow name
        db_workflow.name = workflow.name
        
        # OPTIMIZATION 6: Use bulk delete operations
        delete_start = time.time()
        db.query(Edge).filter(Edge.workflow_id == workflow_id).delete(synchronize_session=False)
        db.query(Node).filter(Node.workflow_id == workflow_id).delete(synchronize_session=False)
        logger.info(f"Bulk delete took: {time.time() - delete_start:.3f}s")
        
        # Prepare new data
        db_nodes = []
        db_edges = []
        node_id_mapping = {}
        
        for node in workflow.nodes:
            unique_node_id = f"{workflow_id}_{node.id}"
            node_id_mapping[node.id] = unique_node_id
            
            db_node = Node(
                id=unique_node_id,
                workflow_id=workflow_id,
                type=node.type,
                position_x=str(node.position.x),
                position_y=str(node.position.y),
                data=node.data.dict()
            )
            db_nodes.append(db_node)

        for edge in workflow.edges:
            unique_edge_id = str(uuid4())
            mapped_source = node_id_mapping.get(edge.source, edge.source)
            mapped_target = node_id_mapping.get(edge.target, edge.target)
            
            db_edge = Edge(
                id=unique_edge_id,
                workflow_id=workflow_id,
                source=mapped_source,
                target=mapped_target,
                type=edge.type
            )
            db_edges.append(db_edge)

        # Bulk save
        db.bulk_save_objects(db_nodes)
        db.bulk_save_objects(db_edges)
        db.commit()
        db.refresh(db_workflow)
        
        # Build response
        response_nodes = [
            NodeResponse(
                id=workflow.nodes[i].id,
                type=db_node.type,
                position={
                    "x": float(db_node.position_x),
                    "y": float(db_node.position_y)
                },
                data=db_node.data
            ) for i, db_node in enumerate(db_nodes)
        ]
        
        response_edges = [
            EdgeResponse(
                id=workflow.edges[i].id,
                source=workflow.edges[i].source,
                target=workflow.edges[i].target,
                type=db_edge.type
            ) for i, db_edge in enumerate(db_edges)
        ]
        
        response = WorkflowResponse(
            id=db_workflow.id,
            name=db_workflow.name,
            nodes=response_nodes,
            edges=response_edges,
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at
        )
        
        total_time = time.time() - start_time
        logger.info(f"Successfully updated workflow in {total_time:.3f}s")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")

# Keep the rest of your endpoints unchanged...
@router.delete("/{workflow_id}", response_model=SuccessResponse)
async def delete_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # OPTIMIZATION 7: Use bulk delete with synchronize_session=False
        chats = db.query(Chat).filter(Chat.workflow_id == workflow_id).all()
        for chat in chats:
            db.query(Message).filter(Message.chat_id == chat.id).delete(synchronize_session=False)
        
        db.query(Chat).filter(Chat.workflow_id == workflow_id).delete(synchronize_session=False)
        db.query(Edge).filter(Edge.workflow_id == workflow_id).delete(synchronize_session=False)
        db.query(Node).filter(Node.workflow_id == workflow_id).delete(synchronize_session=False)
        
        db.delete(workflow)
        db.commit()
        
        total_time = time.time() - start_time
        logger.info(f"Successfully deleted workflow in {total_time:.3f}s")
        return SuccessResponse(message="Workflow deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting workflow: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")

# Rest of your endpoints remain the same...
@router.post("/{workflow_id}/build", response_model=SuccessResponse)
async def build_workflow(workflow_id: UUID, db: Session = Depends(get_db)):
    try:
        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()
        
        workflow.nodes = nodes
        workflow.edges = edges
        
        orchestrator = WorkflowOrchestrator()
        try:
            orchestrator.validate_workflow(workflow)
            return SuccessResponse(message="Workflow built successfully")
        except ValueError as validation_error:
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

        nodes = db.query(Node).filter(Node.workflow_id == workflow_id).all()
        edges = db.query(Edge).filter(Edge.workflow_id == workflow_id).all()
        workflow.nodes = nodes
        workflow.edges = edges

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