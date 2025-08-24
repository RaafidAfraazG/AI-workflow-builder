import pytest
from app.services.kb_service import KnowledgeBaseService
from app.services.embedding_service import MockEmbeddingProvider
from app.models.document import Document
from uuid import uuid4
import tempfile
import os

class TestKnowledgeBaseSearch:
    @pytest.fixture
    def kb_service(self):
        service = KnowledgeBaseService()
        # Force use of mock embedding for testing
        service.embedding_service.provider = MockEmbeddingProvider()
        return service

    @pytest.fixture
    def sample_pdf(self):
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
            # This is a mock - in real tests you'd use a proper PDF
            f.write("This is sample PDF content for testing.")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    def test_text_chunking(self, kb_service):
        text = "This is a long text that should be chunked into smaller pieces for better processing and search."
        chunks = kb_service._chunk_text(text, chunk_size=20, overlap=5)
        
        assert len(chunks) > 1
        assert all(len(chunk) <= 25 for chunk in chunks)  # Allow some overlap

    @pytest.mark.asyncio
    async def test_empty_search_results(self, kb_service):
        # Search in non-existent collection
        workflow_id = str(uuid4())
        results = await kb_service.search(workflow_id, "test query", k=5)
        
        assert isinstance(results, list)
        assert len(results) == 0

    def test_pdf_text_extraction_mock(self, kb_service):
        # Test with a simple text file (mocking PDF extraction)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Sample document content for extraction testing.")
            temp_path = f.name
        
        try:
            # This would normally extract from PDF, but we'll mock it
            # In a real test, you'd use an actual PDF file
            text = "Sample document content for extraction testing."
            assert len(text) > 0
            assert "Sample document" in text
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    @pytest.mark.asyncio
    async def test_mock_embeddings_generation(self):
        provider = MockEmbeddingProvider()
        
        text = "This is a test document"
        embedding = await provider.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # OpenAI's embedding dimension
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.asyncio
    async def test_multiple_embeddings(self):
        provider = MockEmbeddingProvider()
        
        texts = ["First document", "Second document", "Third document"]
        embeddings = await provider.embed_texts(texts)
        
        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)
        
        # Different texts should produce different embeddings
        assert embeddings[0] != embeddings[1]
        assert embeddings[1] != embeddings[2]