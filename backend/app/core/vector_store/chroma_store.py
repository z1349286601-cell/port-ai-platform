import uuid
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.vector_store.base import BaseVectorStore, ChunkWithScore
from app.core.config import settings as app_settings


class ChromaVectorStore(BaseVectorStore):
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=app_settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=app_settings.chroma_collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add(self, chunks: list[ChunkWithScore], embeddings: list[list[float]]) -> None:
        ids = [c.chunk_id or uuid.uuid4().hex for c in chunks]
        metadatas = [c.metadata for c in chunks]
        documents = [c.content for c in chunks]

        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    async def search(self, query_embedding: list[float], top_k: int = 5,
                     filter: dict = None) -> list[ChunkWithScore]:
        kwargs = {"query_embeddings": [query_embedding], "n_results": top_k}
        if filter:
            kwargs["where"] = filter

        results = self.collection.query(**kwargs)

        chunks = []
        if results["ids"] and results["ids"][0]:
            for i, chunk_id in enumerate(results["ids"][0]):
                chunks.append(ChunkWithScore(
                    chunk_id=chunk_id,
                    content=results["documents"][0][i] if results["documents"] else "",
                    metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                    score=1.0 - results["distances"][0][i] if results["distances"] else 0.0,
                ))
        return chunks

    async def delete(self, chunk_ids: list[str]) -> None:
        self.collection.delete(ids=chunk_ids)

    async def count(self) -> int:
        return self.collection.count()

    async def list_documents(self) -> list[dict]:
        """List unique documents with chunk counts from metadata."""
        docs: dict[str, int] = {}
        result = self.collection.get(include=["metadatas"])
        if result["metadatas"]:
            for meta in result["metadatas"]:
                if meta and "doc_name" in meta:
                    doc_name = meta["doc_name"]
                    docs[doc_name] = docs.get(doc_name, 0) + 1
        return [{"doc_name": k, "chunk_count": v, "status": "ready"} for k, v in docs.items()]

    async def delete_by_doc_name(self, doc_name: str) -> int:
        """Delete all chunks for a document. Returns number of chunks deleted."""
        result = self.collection.get(where={"doc_name": doc_name}, include=["metadatas"])
        chunk_ids = result["ids"] if result["ids"] else []
        if chunk_ids:
            self.collection.delete(ids=chunk_ids)
        return len(chunk_ids)
