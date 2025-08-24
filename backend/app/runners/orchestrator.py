from typing import AsyncGenerator, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.workflow import Workflow, Node, Edge
from app.services.llm_service import LLMService
from app.services.kb_service import KnowledgeBaseService
from app.utils.prompt import PromptBuilder
import logging

logger = logging.getLogger(__name__)

class WorkflowOrchestrator:
    def __init__(self):
        self.llm_service = LLMService()
        self.kb_service = KnowledgeBaseService()
        self.prompt_builder = PromptBuilder()

    def validate_workflow(self, workflow: Workflow) -> None:
        """Validate that the workflow has a valid linear path"""
        try:
            if not workflow.nodes:
                raise ValueError("Workflow must have at least one node")

            # Check for required node types in a valid workflow
            node_types = [node.type for node in workflow.nodes]
            logger.info(f"Validating workflow with node types: {node_types}")
            
            if 'userQuery' not in node_types:
                raise ValueError("Workflow must contain a User Query node")
            
            if 'output' not in node_types:
                raise ValueError("Workflow must contain an Output node")

            # Validate edges create a connected path
            if len(workflow.nodes) > 1 and len(workflow.edges) == 0:
                raise ValueError("Workflow with multiple nodes must have connecting edges")
            
            # Additional validation: check if edges reference valid nodes
            node_ids = {node.id for node in workflow.nodes}
            for edge in workflow.edges:
                if edge.source not in node_ids:
                    raise ValueError(f"Edge references non-existent source node: {edge.source}")
                if edge.target not in node_ids:
                    raise ValueError(f"Edge references non-existent target node: {edge.target}")
            
            logger.info("Workflow validation completed successfully")
            
        except Exception as e:
            logger.error(f"Workflow validation failed: {str(e)}")
            raise

    async def run_workflow(self, workflow: Workflow, user_input: str, db: Session) -> AsyncGenerator[str, None]:
        """Execute the workflow and stream the response"""
        try:
            # Build execution path
            execution_path = self._build_execution_path(workflow)
            logger.info(f"Built execution path: {[node.type for node in execution_path]}")
            
            # Process each node in sequence
            context = {"user_input": user_input}
            
            for node in execution_path:
                context = await self._execute_node(node, context, str(workflow.id), db)
            
            # Stream the final response
            if "response" in context:
                response = context["response"]
                for char in str(response):
                    yield char
            else:
                async for token in self._generate_response(context):
                    yield token
                    
        except Exception as e:
            logger.error(f"Error executing workflow: {str(e)}")
            yield f"Error executing workflow: {str(e)}"

    def _build_execution_path(self, workflow: Workflow) -> List[Node]:
        """Build a linear execution path from the workflow graph"""
        try:
            # Simple implementation: find nodes in order
            # Start with userQuery node
            path = []
            node_map = {node.id: node for node in workflow.nodes}
            edge_map = {edge.source: edge.target for edge in workflow.edges}
            
            # Find starting node (userQuery)
            start_node = next((node for node in workflow.nodes if node.type == 'userQuery'), None)
            if not start_node:
                logger.warning("No userQuery node found, using all nodes")
                return list(workflow.nodes)  # Fallback
            
            current = start_node
            path.append(current)
            visited = {current.id}  # Prevent infinite loops
            
            # Follow the edges
            while current.id in edge_map and len(path) < len(workflow.nodes):
                next_id = edge_map[current.id]
                if next_id in visited:
                    logger.warning(f"Circular reference detected at node {next_id}")
                    break
                if next_id in node_map:
                    current = node_map[next_id]
                    path.append(current)
                    visited.add(current.id)
                else:
                    logger.warning(f"Edge references non-existent node: {next_id}")
                    break
            
            logger.info(f"Execution path built with {len(path)} nodes")
            return path
            
        except Exception as e:
            logger.error(f"Error building execution path: {str(e)}")
            return list(workflow.nodes)  # Fallback

    async def _execute_node(self, node: Node, context: Dict[str, Any], workflow_id: str, db: Session) -> Dict[str, Any]:
        """Execute a single node and update context"""
        try:
            logger.info(f"Executing node {node.id} of type {node.type}")
            
            # Safely get node data and config
            node_data = node.data if node.data else {}
            config = node_data.get('config', {}) if isinstance(node_data, dict) else {}
            
            if node.type == 'userQuery':
                # User query node just passes through the input
                logger.info("Processing userQuery node")
                return context
                
            elif node.type == 'knowledgeBase':
                # Search knowledge base
                logger.info("Processing knowledgeBase node")
                query = context.get('user_input', '')
                if query:
                    try:
                        top_k = config.get('top_k', 5) if isinstance(config, dict) else 5
                        results = await self.kb_service.search(workflow_id, query, top_k)
                        context['kb_results'] = results
                        context['kb_context'] = '\n\n'.join([result.content for result in results])
                        logger.info(f"Retrieved {len(results)} KB results")
                    except Exception as e:
                        logger.warning(f"KB search failed: {str(e)}")
                        context['kb_context'] = ""
                return context
                
            elif node.type == 'llmEngine':
                # Generate LLM response
                logger.info("Processing llmEngine node")
                try:
                    custom_prompt = config.get('customPrompt', '') if isinstance(config, dict) else ''
                    prompt = self.prompt_builder.build_prompt(
                        user_query=context.get('user_input', ''),
                        context=context.get('kb_context', ''),
                        custom_prompt=custom_prompt
                    )
                    
                    response = ""
                    async for token in self.llm_service.stream(prompt):
                        response += token
                    
                    context['llm_response'] = response
                    logger.info("LLM response generated successfully")
                except Exception as e:
                    logger.error(f"LLM generation failed: {str(e)}")
                    context['llm_response'] = f"Error generating response: {str(e)}"
                return context
                
            elif node.type == 'output':
                # Format output
                logger.info("Processing output node")
                response = context.get('llm_response', context.get('user_input', ''))
                output_format = config.get('format', 'text') if isinstance(config, dict) else 'text'
                
                try:
                    if output_format == 'json':
                        import json
                        try:
                            # Try to parse as JSON, fallback to wrapping in JSON
                            json.loads(response)
                        except json.JSONDecodeError:
                            response = json.dumps({"response": response})
                    elif output_format == 'markdown':
                        if not response.startswith('#'):
                            response = f"# Response\n\n{response}"
                except Exception as e:
                    logger.warning(f"Output formatting failed: {str(e)}")
                
                context['response'] = response
                return context
            
            logger.warning(f"Unknown node type: {node.type}")
            return context
            
        except Exception as e:
            logger.error(f"Error executing node {node.id}: {str(e)}")
            # Don't fail the entire workflow, just log and continue
            return context

    async def _generate_response(self, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Generate a default response if no explicit response is set"""
        response = context.get('llm_response', context.get('user_input', 'No response generated'))
        for char in str(response):
            yield char