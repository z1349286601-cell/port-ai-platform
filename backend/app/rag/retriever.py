from app.core.vector_store import ChromaVectorStore, ChunkWithScore
from app.core.embedding import OpenAIEmbeddingClient


class Retriever:
    def __init__(
        self, vector_store: ChromaVectorStore, embedding_client: OpenAIEmbeddingClient,
    ):
        self.vector_store = vector_store
        self.embedding_client = embedding_client

    async def retrieve(
        self, query: str, top_k: int = 5, similarity_threshold: float = 0.35
    ) -> list[ChunkWithScore]:
        query_embedding = await self.embedding_client.embed_query(query)
        results = await self.vector_store.search(query_embedding, top_k=top_k)
        return [r for r in results if r.score >= similarity_threshold]

    async def retrieve_with_filter(
        self, query: str, doc_category: str = None,
        top_k: int = 5,
    ) -> list[ChunkWithScore]:
        query_embedding = await self.embedding_client.embed_query(query)
        filter_dict = None
        if doc_category:
            filter_dict = {"doc_category": doc_category}
        return await self.vector_store.search(query_embedding, top_k=top_k, filter=filter_dict)
