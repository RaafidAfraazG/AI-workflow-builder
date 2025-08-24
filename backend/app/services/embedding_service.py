# backend/app/services/embedding_service.py - Robust Embedding Service
from typing import List
import logging
import asyncio
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(self):
        self.provider = None
        self._initialize_safely()
    
    def _initialize_safely(self):
        """Initialize embedding provider with proper error handling"""
        try:
            embedding_provider = getattr(settings, 'EMBEDDING_PROVIDER', 'mock')
            openai_key = getattr(settings, 'OPENAI_API_KEY', None)
            
            if embedding_provider == "openai" and openai_key:
                logger.info("Attempting to initialize OpenAI embeddings")
                self._init_openai()
                logger.info("OpenAI embeddings initialized successfully")
            else:
                logger.info("Using Mock embedding provider")
                self.provider = "mock"
        except Exception as e:
            logger.warning(f"Failed to initialize embedding provider: {str(e)}. Using mock.")
            self.provider = "mock"
    
    def _init_openai(self):
        """Initialize OpenAI embedding client"""
        try:
            import openai
            self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.provider = "openai"
        except ImportError:
            raise ImportError("openai package not installed")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if self.provider == "openai":
            return await self._openai_embed_text(text)
        else:
            return self._mock_embed_text(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        if self.provider == "openai":
            return await self._openai_embed_texts(texts)
        else:
            return [self._mock_embed_text(text) for text in texts]
    
    async def _openai_embed_text(self, text: str) -> List[float]:
        """Generate OpenAI embedding for single text"""
        try:
            response = self.openai_client.embeddings.create(
                input=text,
                model="text-embedding-ada-002"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {str(e)}")
            return self._mock_embed_text(text)
    
    async def _openai_embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate OpenAI embeddings for multiple texts"""
        try:
            response = self.openai_client.embeddings.create(
                input=texts,
                model="text-embedding-ada-002"
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI batch embedding failed: {str(e)}")
            return [self._mock_embed_text(text) for text in texts]
    
    def _mock_embed_text(self, text: str) -> List[float]:
        """Generate mock embedding based on text hash"""
        import hashlib
        # Create a deterministic embedding based on text content
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Generate 1536-dimensional embedding (same as OpenAI ada-002)
        embedding = []
        for i in range(1536):
            # Use hash to generate pseudo-random values between -1 and 1
            val = ((hash_int >> (i % 32)) & 0xFF) / 127.5 - 1.0
            embedding.append(val)
        
        # Normalize to unit vector
        norm = sum(x*x for x in embedding) ** 0.5
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding