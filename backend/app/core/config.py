from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model_name: str = "qwen3-vl:8b"
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


settings = Settings()
