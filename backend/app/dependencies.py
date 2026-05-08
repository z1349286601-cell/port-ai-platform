from app.core.llm import OpenAICompatibleClient
from app.core.embedding import OpenAIEmbeddingClient
from app.core.vector_store import ChromaVectorStore
from app.rag import RAGPipeline

_llm_client: OpenAICompatibleClient | None = None
_embedding_client: OpenAIEmbeddingClient | None = None
_vector_store: ChromaVectorStore | None = None
_rag_pipeline: RAGPipeline | None = None


def get_llm_client() -> OpenAICompatibleClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = OpenAICompatibleClient()
    return _llm_client


def get_embedding_client() -> OpenAIEmbeddingClient:
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = OpenAIEmbeddingClient()
    return _embedding_client


def get_vector_store() -> ChromaVectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = ChromaVectorStore()
    return _vector_store


def get_rag_pipeline() -> RAGPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RAGPipeline(
            llm_client=get_llm_client(),
            embedding_client=get_embedding_client(),
            vector_store=get_vector_store(),
        )
    return _rag_pipeline
