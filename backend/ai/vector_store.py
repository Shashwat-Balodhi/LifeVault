"""
Vector Store Module
--------------------
Manages ChromaDB PersistentClient with a single "lifevault" collection.
Handles upsert, search, and retrieval operations.

Key design decisions:
    - Uses MD5 hash of file path as document ID → no duplicates ever.
    - Two separate collections for different embedding dimensions:
        • lifevault_images (512-dim, CLIP)
        • lifevault_documents (384-dim, SentenceTransformer)
    - Cosine similarity metric for both.
"""

import hashlib
from typing import Dict, Any, List, Optional

import chromadb
from chromadb.config import Settings

from backend.utils.config import CHROMA_DB_PATH, COLLECTION_NAME
from backend.utils.logger import get_logger

logger = get_logger(__name__)


def _file_id(file_path: str) -> str:
    """Generate a deterministic ID from file path using MD5."""
    return hashlib.md5(file_path.encode("utf-8")).hexdigest()


class VectorStore:
    """Manages ChromaDB collections for images and documents."""

    def __init__(self):
        logger.info(f"Initializing ChromaDB at {CHROMA_DB_PATH}")
        self.client = chromadb.PersistentClient(
            path=CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False),
        )

        # Separate collections for different embedding dimensions
        self.image_collection = self.client.get_or_create_collection(
            name=f"{COLLECTION_NAME}_images",
            metadata={"hnsw:space": "cosine"},
        )
        self.doc_collection = self.client.get_or_create_collection(
            name=f"{COLLECTION_NAME}_documents",
            metadata={"hnsw:space": "cosine"},
        )

        img_count = self.image_collection.count()
        doc_count = self.doc_collection.count()
        logger.info(
            f"✓ ChromaDB ready — {img_count} images, {doc_count} documents indexed."
        )

    def upsert_image(
        self,
        file_path: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        text_content: str = "",
    ):
        """Upsert an image record into the image collection."""
        doc_id = _file_id(file_path)
        # ChromaDB metadata values must be str, int, float, or bool
        clean_meta = {k: v for k, v in metadata.items() if v is not None and v != ""}

        self.image_collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[clean_meta],
            documents=[text_content or f"Image: {metadata.get('file_name', '')}"],
        )
        logger.info(f"  ↳ Upserted image: {metadata.get('file_name', doc_id)}")

    def upsert_document(
        self,
        file_path: str,
        embedding: List[float],
        metadata: Dict[str, Any],
        text_content: str = "",
    ):
        """Upsert a document record into the document collection."""
        doc_id = _file_id(file_path)
        clean_meta = {k: v for k, v in metadata.items() if v is not None and v != ""}

        self.doc_collection.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            metadatas=[clean_meta],
            documents=[text_content[:5000] or f"Document: {metadata.get('file_name', '')}"],
        )
        logger.info(f"  ↳ Upserted document: {metadata.get('file_name', doc_id)}")

    def search_images(
        self,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search the image collection by embedding similarity."""
        results = self.image_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.image_collection.count() or 1),
            include=["metadatas", "documents", "distances"],
        )
        return self._format_results(results)

    def search_documents(
        self,
        query_embedding: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """Search the document collection by embedding similarity."""
        results = self.doc_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.doc_collection.count() or 1),
            include=["metadatas", "documents", "distances"],
        )
        return self._format_results(results)

    def get_all_metadata(self) -> List[Dict[str, Any]]:
        """Return metadata for all indexed files (for analytics)."""
        all_meta = []
        
        # Images
        if self.image_collection.count() > 0:
            img_data = self.image_collection.get(include=["metadatas", "documents"])
            for meta, doc in zip(img_data["metadatas"], img_data["documents"]):
                meta["_document_preview"] = doc[:200] if doc else ""
                all_meta.append(meta)

        # Documents
        if self.doc_collection.count() > 0:
            doc_data = self.doc_collection.get(include=["metadatas", "documents"])
            for meta, doc in zip(doc_data["metadatas"], doc_data["documents"]):
                meta["_document_preview"] = doc[:200] if doc else ""
                all_meta.append(meta)

        return all_meta

    def get_random_memory(self) -> Optional[Dict[str, Any]]:
        """Return a random indexed file for 'Surprise Me' mode."""
        import random

        all_meta = self.get_all_metadata()
        if not all_meta:
            return None
        return random.choice(all_meta)

    def is_file_indexed(self, file_path: str) -> bool:
        """Check if a file is already indexed (by its MD5 ID)."""
        doc_id = _file_id(file_path)
        try:
            result = self.image_collection.get(ids=[doc_id])
            if result["ids"]:
                return True
        except Exception:
            pass
        try:
            result = self.doc_collection.get(ids=[doc_id])
            if result["ids"]:
                return True
        except Exception:
            pass
        return False

    def get_stats(self) -> Dict[str, int]:
        """Return collection statistics."""
        return {
            "total_images": self.image_collection.count(),
            "total_documents": self.doc_collection.count(),
            "total_files": self.image_collection.count() + self.doc_collection.count(),
        }

    @staticmethod
    def _format_results(raw_results: Dict) -> List[Dict[str, Any]]:
        """Convert ChromaDB query results into a clean list of dicts."""
        formatted = []
        if not raw_results or not raw_results.get("ids"):
            return formatted

        ids = raw_results["ids"][0]
        metadatas = raw_results["metadatas"][0] if raw_results.get("metadatas") else [{}] * len(ids)
        documents = raw_results["documents"][0] if raw_results.get("documents") else [""] * len(ids)
        distances = raw_results["distances"][0] if raw_results.get("distances") else [0.0] * len(ids)

        for i, doc_id in enumerate(ids):
            # ChromaDB cosine distance → similarity score (1 - distance)
            score = max(0.0, 1.0 - distances[i])
            formatted.append({
                "id": doc_id,
                "score": round(score, 4),
                "match_percentage": round(score * 100, 1),
                "metadata": metadatas[i],
                "text_preview": documents[i][:300] if documents[i] else "",
            })

        # Sort by score descending
        formatted.sort(key=lambda x: x["score"], reverse=True)
        return formatted
