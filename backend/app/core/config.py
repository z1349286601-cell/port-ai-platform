from pathlib import Path
from pydantic_settings import BaseSettings

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _resolve_path(p: str) -> str:
    """Resolve a relative path against the project root."""
    path = Path(p)
    if not path.is_absolute():
        return str(_PROJECT_ROOT / path)
    return p


class Settings(BaseSettings):
    model_config = {"env_file": str(_PROJECT_ROOT / ".env"), "env_file_encoding": "utf-8"}

    # LLM
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model_name: str = "qwen3:8b"
    llm_api_key: str = "not-needed"

    # Embedding
    embedding_base_url: str = "http://localhost:11434/v1"
    embedding_model_name: str = "bge-m3"

    # ChromaDB
    chroma_persist_dir: str = "./data/chromadb"
    chroma_collection_name: str = "port_docs"

    # SQLite (multi-DB by domain)
    sqlite_data_dir: str = "./data/sqlite"

    # Chat
    max_context_messages: int = 20
    max_context_tokens: int = 4000
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Rate limit
    rate_limit_per_minute: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    # Intent router
    intent_confidence_threshold: float = 0.7

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.chroma_persist_dir = _resolve_path(self.chroma_persist_dir)
        self.sqlite_data_dir = _resolve_path(self.sqlite_data_dir)


settings = Settings()
