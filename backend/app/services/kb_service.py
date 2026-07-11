# backend/app/services/kb_service.py
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
            from chromadb.config import Settings as ChromaSettings

            # Embedded persistent mode — no Docker / no HTTP server needed.
            # Data is stored in CHROMA_PERSIST_DIR (default: ./chroma_data).
            self.chroma_client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=ChromaSettings(anonymized_telemetry=False),
            )
            logger.info(f"ChromaDB PersistentClient initialized at: {settings.CHROMA_PERSIST_DIR}")
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
        """Save uploaded PDF to disk + DB record"""
        try:
            upload_dir = settings.UPLOAD_DIR
            os.makedirs(upload_dir, exist_ok=True)

            file_path = os.path.join(upload_dir, file.filename)

            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            logger.info(f"File saved to: {file_path}")

            # Parse workflow_id if collection is a valid UUID, otherwise store as-is
            workflow_id = None
            try:
                from uuid import UUID as _UUID
                workflow_id = _UUID(collection)
            except (ValueError, AttributeError):
                pass

            document = Document(
                filename=file.filename,
                file_path=file_path,
                content_type=file.content_type or "application/pdf",
                is_ingested=False,
                workflow_id=workflow_id,
            )

            self.db.add(document)
            self.db.commit()
            self.db.refresh(document)

            logger.info(f"Document created with ID: {document.id}")
            return DocumentResponse.model_validate(document)

        except Exception as e:
            logger.error(f"Error in upload_document: {str(e)}")
            self.db.rollback()
            raise

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
            if not text:
                return SuccessResponse(message=f"Document {document_id} has no extractable text")

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

            document.is_ingested = True
            self.db.commit()

            logger.info(f"Successfully ingested document {document.id}")
            return SuccessResponse(message=f"Document {document_id} ingested successfully")
        except Exception as e:
            logger.error(f"Error ingesting document {document_id}: {str(e)}")
            self.db.rollback()
            raise

    async def search_documents(self, query: str, collection: str, top_k: int = 5) -> List[KnowledgeBaseSearchResult]:
        """Search all ingested documents for a workflow (collection = workflow_id)."""
        if not self.chroma_client or not self.embedding_service:
            logger.warning("Search unavailable, returning empty list")
            return []

        try:
            # Find all ingested documents for this workflow
            from uuid import UUID as _UUID
            workflow_uuid = None
            try:
                workflow_uuid = _UUID(collection)
            except (ValueError, AttributeError):
                pass

            if workflow_uuid:
                docs_in_workflow = (
                    self.db.query(Document)
                    .filter(Document.workflow_id == workflow_uuid, Document.is_ingested == True)
                    .all()
                )
            else:
                docs_in_workflow = []

            if not docs_in_workflow:
                logger.warning(f"No ingested documents found for workflow {collection}")
                return []

            query_embedding = await self.embedding_service.embed_text(query)

            all_results: List[KnowledgeBaseSearchResult] = []
            for doc in docs_in_workflow:
                col_name = f"doc_{doc.id}".replace("-", "_")
                try:
                    col_obj = self.chroma_client.get_collection(name=col_name)
                    count = col_obj.count()
                    if count == 0:
                        continue
                    results = col_obj.query(
                        query_embeddings=[query_embedding],
                        n_results=min(top_k, count)
                    )
                    if results.get("documents"):
                        for i, chunk in enumerate(results["documents"][0]):
                            all_results.append(
                                KnowledgeBaseSearchResult(
                                    id=results["ids"][0][i],
                                    content=chunk,
                                    metadata=results["metadatas"][0][i] if results.get("metadatas") else {},
                                    score=1.0 - results["distances"][0][i] if results.get("distances") else 0.0,
                                )
                            )
                except Exception as col_err:
                    logger.warning(f"Failed to search collection {col_name}: {col_err}")

            # Sort by score descending, return top_k
            all_results.sort(key=lambda x: x.score, reverse=True)
            logger.info(f"KB search returned {len(all_results)} total results across {len(docs_in_workflow)} document(s)")
            return all_results[:top_k]

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    async def delete_document(self, document_id: UUID) -> SuccessResponse:
        """Remove from ChromaDB (vector store)"""
        if not self.chroma_client:
            logger.warning("ChromaDB not available, skipping vector delete")
            return SuccessResponse(message="Skipped vector delete (ChromaDB not available)")

        try:
            collection_name = f"doc_{document_id}".replace("-", "_")

            try:
                existing_collections = self.chroma_client.list_collections()
                # In chromadb 0.6+, list_collections() returns a list of Collection objects
                collection_names = [
                    col if isinstance(col, str) else col.name
                    for col in existing_collections
                ]
                if collection_name in collection_names:
                    self.chroma_client.delete_collection(name=collection_name)
                    logger.info(f"Deleted collection for document {document_id}")
                    return SuccessResponse(message=f"Document {document_id} removed from vectorstore")
                else:
                    logger.info(f"Collection {collection_name} does not exist, skipping")
                    return SuccessResponse(message=f"Collection {collection_name} did not exist")

            except Exception as delete_error:
                logger.warning(f"ChromaDB collection deletion failed: {str(delete_error)}")
                return SuccessResponse(message=f"Vector delete completed with warnings: {str(delete_error)}")

        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from ChromaDB: {str(e)}")
            return SuccessResponse(message=f"Vector delete failed: {str(e)}")

    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF with PyMuPDF; return empty if no text"""
        try:
            doc = fitz.open(file_path)
            text = "".join(page.get_text() for page in doc).strip()
            doc.close()

            if not text:
                logger.warning(f"No extractable text found in {file_path}")

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
