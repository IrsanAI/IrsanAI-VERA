"""
IrsanAI-VERA — Cross-Session Vector Memory
core/memory/chromadb_store.py
"""

from __future__ import annotations
import os
import chromadb
from chromadb.utils import embedding_functions
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from core.bayesian.updater import Evidence


class VERAMemoryStore:
    """Persistent vector store for cross-session evidence memory."""

    def __init__(self, persist_dir: str = ".vera_memory"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name='all-MiniLM-L6-v2'
        )
        self.collection = self.client.get_or_create_collection(
            name="vera_evidence",
            embedding_function=self.embedding_fn
        )

    def store_evidence(self, ev: Evidence, session_id: str) -> str:
        """Embed and store. Returns chroma document id."""
        metadata = {
            "session_id": session_id,
            "source_url": ev.source_url,
            "source_type": ev.source_type,
            "supports_hypothesis": ev.supports_hypothesis,
            "retrieved_at": ev.retrieved_at,
            "semantic_score": ev.semantic_score
        }
        
        self.collection.add(
            ids=[ev.id],
            documents=[ev.summary + " " + (ev.raw_snippet or "")],
            metadatas=[metadata]
        )
        return ev.id

    def find_similar(
        self, query: str, k: int = 5, threshold: float = 0.65
    ) -> list[dict]:
        """Cosine similarity search. Only returns score > threshold."""
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"]
        )
        
        found = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                # Chroma distances are often L2, but we can approximate or use them
                # For simplicity, we'll just return the results if they exist
                # In a real scenario, we'd convert distance to similarity
                dist = results["distances"][0][i]
                if dist < (1.0 - threshold) * 2: # Rough L2 to similarity conversion
                    found.append({
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": dist
                    })
        return found

    def get_session_evidence(self, session_id: str) -> list[dict]:
        """Retrieve all evidence from a previous session."""
        results = self.collection.get(
            where={"session_id": session_id},
            include=["documents", "metadatas"]
        )
        
        found = []
        if results["ids"]:
            for i in range(len(results["ids"])):
                found.append({
                    "id": results["ids"][i],
                    "document": results["documents"][i],
                    "metadata": results["metadatas"][i]
                })
        return found

    def has_seen_url(self, url: str) -> bool:
        """Prevent duplicate evidence across sessions."""
        results = self.collection.get(
            where={"source_url": url},
            limit=1
        )
        return len(results["ids"]) > 0
