# app/services/kb_service.py - Fixed version
import os
import logging
import fitz  # PyMuPDF
from typing import List
from uuid import UUID

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.schemas.document import DocumentResponse, KnowledgeBaseSearchResult
from app.schemas.common import SuccessResponse
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class KnowledgeBaseService:
    def __init__(self, db: Session):
        self.db = db
        self.chroma_client = None
        self.embedding_service = None
        self._initialize_safely()

    def _initialize_safely(self):
        """Initialize services with error handling"""
        try:
            import chromadb
            from chromadb.config import Settings

            self.chroma_client = chromadb.HttpClient(
                host=getattr(settings, "CHROMA_HOST", "localhost"),
                port=getattr(settings, "CHROMA_PORT", 8000),
                settings=Settings(anonymized_telemetry=False),
            )
            logger.info("ChromaDB client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB: {str(e)}. Using mock mode.")
            self.chroma_client = None

        try:
            self.embedding_service = EmbeddingService()
            logger.info("Embedding service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize embedding service: {str(e)}. Using mock mode.")
            self.embedding_service = None

    async def upload_document(self, file: UploadFile, collection: str) -> DocumentResponse:
        """Save uploaded PDF to disk + DB record - FIXED"""
        # Use settings.UPLOAD_DIR consistently
        upload_dir = settings.UPLOAD_DIR
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        
        # Read file content
        content = await file.read()
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved to: {file_path}")

        # Create database record - FIXED: Use correct field names
        document = Document(
            filename=file.filename,                    # ✅ Correct field name
            file_path=file_path,                      # ✅ Correct
            content_type=file.content_type or "application/pdf",  # ✅ Use actual field
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)

        logger.info(f"Document created with ID: {document.id}")
        return DocumentResponse.from_attributes(document)

    async def ingest_document(self, document_id: UUID) -> SuccessResponse:
        """Extract text, create embeddings, and push to ChromaDB"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError("Document not found")

        if not self.chroma_client or not self.embedding_service:
            logger.warning("ChromaDB or embedding service not available, skipping ingestion")
            return SuccessResponse(message="Skipped ingestion (no vector DB or embedding service)")

        try:
            text = self._extract_text_from_pdf(document.file_path)
            chunks = self._chunk_text(text)
            embeddings = await self.embedding_service.embed_texts(chunks)

            collection_name = f"doc_{document.id}".replace("-", "_")
            collection = self.chroma_client.get_or_create_collection(name=collection_name)

            ids = [f"{document.id}_{i}" for i in range(len(chunks))]
            metadatas = [{"document_id": str(document.id), "chunk_index": i} for i in range(len(chunks))]

            collection.add(
                ids=ids,
                documents=chunks,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            
            # Mark document as ingested
            document.is_ingested = True
            self.db.commit()
            
            logger.info(f"Successfully ingested document {document.id}")
            return SuccessResponse(message=f"Document {document_id} ingested successfully")
        except Exception as e:
            logger.error(f"Error ingesting document {document_id}: {str(e)}")
            raise

    async def search_documents(self, query: str, collection: str, top_k: int = 5) -> List[KnowledgeBaseSearchResult]:
        """Search relevant documents - FIXED: Return proper search results"""
        if not self.chroma_client or not self.embedding_service:
            logger.warning("Search unavailable, returning empty list")
            return []

        try:
            query_embedding = await self.embedding_service.embed_text(query)
            collection_obj = self.chroma_client.get_or_create_collection(name=collection)

            results = collection_obj.query(query_embeddings=[query_embedding], n_results=top_k)

            search_results: List[KnowledgeBaseSearchResult] = []
            if results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    search_results.append(
                        KnowledgeBaseSearchResult(
                            id=results["ids"][0][i],
                            content=doc,
                            metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                            score=1.0 - results["distances"][0][i] if results.get("distances") else 0.0,
                        )
                    )
            return search_results
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    async def delete_document(self, document_id: UUID) -> SuccessResponse:
        """Remove from ChromaDB (vector store)"""
        if not self.chroma_client:
            logger.warning("ChromaDB not available, skipping vector delete")
            return SuccessResponse(message="Skipped vector delete")

        try:
            collection_name = f"doc_{document_id}".replace("-", "_")
            self.chroma_client.delete_collection(name=collection_name)
            logger.info(f"Deleted collection for document {document_id}")
            return SuccessResponse(message=f"Document {document_id} removed from vectorstore")
        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from ChromaDB: {str(e)}")
            return SuccessResponse(message=f"Failed vector delete: {str(e)}")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF with PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return ""

    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return [c for c in chunks if c.strip()]