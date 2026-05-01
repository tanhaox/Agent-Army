"""Vector store — ChromaDB (primary) and pgvector (supplementary) backends.

ChromaDB is used for vector similarity search. pgvector column on
strategy_entries provides a backup store for future migration.
"""
import logging
import uuid

import chromadb
from sqlalchemy import text

from app.core.config import settings
from app.services.embedding import embed, embed_batch

logger = logging.getLogger(__name__)

COLLECTION_NAME = "strategies"


class VectorStore:
    """ChromaDB-backed vector store (synchronous, existing API unchanged)."""

    def __init__(self):
        self._client: chromadb.HttpClient | None = None
        self._collection = None

    def _get_client(self) -> chromadb.HttpClient:
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=settings.CHROMA_HOST, port=settings.CHROMA_PORT
            )
        return self._client

    def ensure_collection(self):
        client = self._get_client()
        self._collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("ChromaDB collection '%s' ready (%d items)", COLLECTION_NAME, self._collection.count())

    def _col(self):
        if self._collection is None:
            self.ensure_collection()
        return self._collection

    def add_vectors(
        self,
        ids: list[str],
        documents: list[str],
        metadatas: list[dict],
    ) -> None:
        embeddings = embed_batch(documents)
        self._col().add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    def query_vectors(
        self, query_text: str, top_k: int = 3
    ) -> list[dict]:
        query_embedding = embed(query_text)
        col = self._col()
        results = col.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, col.count()) if col.count() > 0 else 1,
        )
        items = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                items.append({
                    "id": doc_id,
                    "document": results["documents"][0][i] if results["documents"] else "",
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                })
        return items

    def delete_vectors(self, ids: list[str]) -> None:
        if ids:
            self._col().delete(ids=ids)


async def store_pgvector(db, strategy_id: uuid.UUID, text: str) -> None:
    """Store embedding vector in PostgreSQL pgvector column."""
    vec = embed(text)
    await db.execute(
        text("UPDATE strategy_entries SET embedding_vector = :vec WHERE id = :id"),
        {"vec": str(vec), "id": strategy_id},
    )
    await db.commit()


async def query_pgvector(
    db, query_text: str, top_k: int = 3
) -> list[dict]:
    """Semantic search via pgvector cosine distance."""
    query_vec = embed(query_text)
    result = await db.execute(
        text("""
            SELECT id, title, extracted_pattern, quality_score,
                   1 - (embedding_vector <=> :vec) AS similarity
            FROM strategy_entries
            WHERE embedding_vector IS NOT NULL
            ORDER BY embedding_vector <=> :vec
            LIMIT :limit
        """),
        {"vec": str(query_vec), "limit": top_k},
    )
    rows = result.fetchall()
    return [
        {
            "id": str(row[0]),
            "title": row[1],
            "document": row[2],
            "quality_score": row[3],
            "similarity": round(float(row[4]), 4),
        }
        for row in rows
    ]


vector_store = VectorStore()
