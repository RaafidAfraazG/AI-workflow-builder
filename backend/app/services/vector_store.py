"""
Pure-Python / NumPy vector store.
Drop-in replacement for the ChromaDB subset we use, so no C++ Build Tools
are needed on Windows Python 3.12.

API surface implemented:
  client = VectorStoreClient(path=...)
  col    = client.get_or_create_collection(name=...)
  col    = client.get_collection(name=...)
         client.delete_collection(name=...)
         client.list_collections()              -> list[str]
  col.add(ids, documents, embeddings, metadatas)
  col.query(query_embeddings, n_results)        -> {ids, documents, distances, metadatas}
  col.count()                                   -> int
"""
import os
import json
import shutil
import logging
from typing import Any, List, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class VectorCollection:
    """Single named collection backed by .npy + .json files."""

    def __init__(self, path: str):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self._embeddings_file = os.path.join(path, "embeddings.npy")
        self._meta_file = os.path.join(path, "metadata.json")
        self._data = self._load()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _load(self) -> Dict:
        if os.path.exists(self._embeddings_file) and os.path.exists(self._meta_file):
            try:
                embeddings = np.load(self._embeddings_file).tolist()
                with open(self._meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                return {
                    "ids": meta["ids"],
                    "documents": meta["documents"],
                    "metadatas": meta["metadatas"],
                    "embeddings": embeddings,
                }
            except Exception as e:
                logger.warning(f"Failed to load collection at {self.path}: {e}. Starting fresh.")
        return {"ids": [], "documents": [], "metadatas": [], "embeddings": []}

    def _save(self):
        np.save(
            self._embeddings_file,
            np.array(self._data["embeddings"], dtype=np.float32),
        )
        with open(self._meta_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "ids": self._data["ids"],
                    "documents": self._data["documents"],
                    "metadatas": self._data["metadatas"],
                },
                f,
                ensure_ascii=False,
            )

    # ------------------------------------------------------------------
    # ChromaDB-compatible API
    # ------------------------------------------------------------------
    def count(self) -> int:
        return len(self._data["ids"])

    def add(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
    ):
        existing = set(self._data["ids"])
        for i, id_ in enumerate(ids):
            if id_ in existing:
                continue  # skip duplicates
            self._data["ids"].append(id_)
            self._data["documents"].append(documents[i])
            self._data["embeddings"].append(embeddings[i])
            self._data["metadatas"].append(metadatas[i] if metadatas else {})
        self._save()
        logger.debug(f"Collection now has {len(self._data['ids'])} vectors")

    def query(
        self,
        query_embeddings: List[List[float]],
        n_results: int = 5,
    ) -> Dict:
        """Return top-n results sorted by cosine distance (ascending = most similar first)."""
        empty = {"ids": [[]], "documents": [[]], "distances": [[]], "metadatas": [[]]}
        if not self._data["embeddings"]:
            return empty

        q = np.array(query_embeddings[0], dtype=np.float32)
        db = np.array(self._data["embeddings"], dtype=np.float32)

        # Cosine similarity
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        db_norms = np.linalg.norm(db, axis=1, keepdims=True) + 1e-10
        db_normalized = db / db_norms
        similarities = db_normalized @ q_norm          # shape (N,)

        # distance = 1 - similarity (lower = more similar, matching ChromaDB convention)
        distances = (1.0 - similarities).tolist()

        k = min(n_results, len(distances))
        top_indices = np.argsort(distances)[:k].tolist()

        return {
            "ids": [[self._data["ids"][i] for i in top_indices]],
            "documents": [[self._data["documents"][i] for i in top_indices]],
            "distances": [[distances[i] for i in top_indices]],
            "metadatas": [[self._data["metadatas"][i] for i in top_indices]],
        }


class VectorStoreClient:
    """Manages multiple named VectorCollection instances on disk."""

    def __init__(self, path: str, settings: Any = None):
        self.path = path
        os.makedirs(path, exist_ok=True)
        logger.info(f"VectorStoreClient initialised at: {path}")

    def get_or_create_collection(self, name: str) -> VectorCollection:
        return VectorCollection(os.path.join(self.path, name))

    def get_collection(self, name: str) -> VectorCollection:
        col_path = os.path.join(self.path, name)
        if not os.path.exists(col_path):
            raise ValueError(f"Collection '{name}' does not exist")
        return VectorCollection(col_path)

    def delete_collection(self, name: str):
        col_path = os.path.join(self.path, name)
        if os.path.exists(col_path):
            shutil.rmtree(col_path)
            logger.info(f"Deleted collection: {name}")

    def list_collections(self) -> List[str]:
        return [
            d
            for d in os.listdir(self.path)
            if os.path.isdir(os.path.join(self.path, d))
        ]
