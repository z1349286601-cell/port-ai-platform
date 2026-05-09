from app.core.llm import OpenAICompatibleClient
from app.core.embedding import OpenAIEmbeddingClient
from app.core.vector_store import ChromaVectorStore
from app.rag import RAGPipeline
from app.nl2sql import NL2SQLPipeline
from app.conversation import (
    IntentRouter, SqliteSessionStore, ContextManager, HistoryManager
)

_llm_client: OpenAICompatibleClient | None = None
_embedding_client: OpenAIEmbeddingClient | None = None
_vector_store: ChromaVectorStore | None = None
_rag_pipeline: RAGPipeline | None = None
_nl2sql_pipeline: NL2SQLPipeline | None = None
_intent_router: IntentRouter | None = None
_session_store: SqliteSessionStore | None = None
_context_manager: ContextManager | None = None
_history_manager: HistoryManager | None = None


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


def get_nl2sql_pipeline() -> NL2SQLPipeline:
    global _nl2sql_pipeline
    if _nl2sql_pipeline is None:
        _nl2sql_pipeline = NL2SQLPipeline(llm_client=get_llm_client())
    return _nl2sql_pipeline


def get_intent_router() -> IntentRouter:
    global _intent_router
    if _intent_router is None:
        _intent_router = IntentRouter(llm_client=get_llm_client())
    return _intent_router


def get_session_store() -> SqliteSessionStore:
    global _session_store
    if _session_store is None:
        _session_store = SqliteSessionStore()
    return _session_store


def get_context_manager() -> ContextManager:
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def get_history_manager() -> HistoryManager:
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager(llm_client=get_llm_client())
    return _history_manager
