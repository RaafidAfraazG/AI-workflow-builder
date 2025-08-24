import pytest
from app.runners.orchestrator import WorkflowOrchestrator
from app.models.workflow import Workflow, Node, Edge
from uuid import uuid4

class TestGraphValidation:
    def test_empty_workflow_fails_validation(self):
        workflow = Workflow(id=uuid4(), name="Test")
        workflow.nodes = []
        workflow.edges = []
        
        orchestrator = WorkflowOrchestrator()
        with pytest.raises(ValueError, match="Workflow must have at least one node"):
            orchestrator.validate_workflow(workflow)

    def test_workflow_without_user_query_fails(self):
        workflow = Workflow(id=uuid4(), name="Test")
        node = Node(id="1", workflow_id=workflow.id, type="output", data={"label": "Output", "config": {}})
        workflow.nodes = [node]
        workflow.edges = []
        
        orchestrator = WorkflowOrchestrator()
        with pytest.raises(ValueError, match="Workflow must contain a User Query node"):
            orchestrator.validate_workflow(workflow)

    def test_workflow_without_output_fails(self):
        workflow = Workflow(id=uuid4(), name="Test")
        node = Node(id="1", workflow_id=workflow.id, type="userQuery", data={"label": "Query", "config": {}})
        workflow.nodes = [node]
        workflow.edges = []
        
        orchestrator = WorkflowOrchestrator()
        with pytest.raises(ValueError, match="Workflow must contain an Output node"):
            orchestrator.validate_workflow(workflow)

    def test_valid_simple_workflow_passes(self):
        workflow = Workflow(id=uuid4(), name="Test")
        
        node1 = Node(id="1", workflow_id=workflow.id, type="userQuery", data={"label": "Query", "config": {}})
        node2 = Node(id="2", workflow_id=workflow.id, type="output", data={"label": "Output", "config": {}})
        edge = Edge(id="e1", workflow_id=workflow.id, source="1", target="2", type="default")
        
        workflow.nodes = [node1, node2]
        workflow.edges = [edge]
        
        orchestrator = WorkflowOrchestrator()
        # Should not raise any exception
        orchestrator.validate_workflow(workflow)

    def test_execution_path_building(self):
        workflow = Workflow(id=uuid4(), name="Test")
        
        node1 = Node(id="1", workflow_id=workflow.id, type="userQuery", data={"label": "Query", "config": {}})
        node2 = Node(id="2", workflow_id=workflow.id, type="llmEngine", data={"label": "LLM", "config": {}})
        node3 = Node(id="3", workflow_id=workflow.id, type="output", data={"label": "Output", "config": {}})
        
        edge1 = Edge(id="e1", workflow_id=workflow.id, source="1", target="2", type="default")
        edge2 = Edge(id="e2", workflow_id=workflow.id, source="2", target="3", type="default")
        
        workflow.nodes = [node1, node2, node3]
        workflow.edges = [edge1, edge2]
        
        orchestrator = WorkflowOrchestrator()
        path = orchestrator._build_execution_path(workflow)
        
        assert len(path) == 3
        assert path[0].type == "userQuery"
        assert path[1].type == "llmEngine"
        assert path[2].type == "output"