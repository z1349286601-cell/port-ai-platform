from collections.abc import AsyncIterator
from pathlib import Path
from langchain_core.documents import Document
from app.core.vector_store import ChromaVectorStore, ChunkWithScore
from app.core.embedding import OpenAIEmbeddingClient
from app.core.llm import OpenAICompatibleClient
from app.rag.document_loader import DocumentLoader
from app.rag.chunker import MarkdownChunker
from app.rag.retriever import Retriever
from app.rag.generator import Generator


class RAGPipeline:
    def __init__(
        self,
        llm_client: OpenAICompatibleClient = None,
        embedding_client: OpenAIEmbeddingClient = None,
        vector_store: ChromaVectorStore = None,
    ):
        self.llm_client = llm_client or OpenAICompatibleClient()
        self.embedding_client = embedding_client or OpenAIEmbeddingClient()
        self.vector_store = vector_store or ChromaVectorStore()
        self.loader = DocumentLoader()
        self.chunker = MarkdownChunker()
        self.retriever = Retriever(self.vector_store, self.embedding_client)
        self.generator = Generator(self.llm_client)

    async def ingest_file(self, file_path: str) -> int:
        documents = await self.loader.load(file_path)
        return await self._index_documents(documents)

    async def ingest_directory(self, dir_path: str) -> int:
        documents = await self.loader.load_directory(dir_path)
        return await self._index_documents(documents)

    async def _index_documents(self, documents: list[Document]) -> int:
        chunks = self.chunker.split(documents)
        if not chunks:
            return 0

        texts = [c.page_content for c in chunks]
        embeddings = await self.embedding_client.embed(texts)

        chunk_objs = [
            ChunkWithScore(
                chunk_id=f"{c.metadata.get('doc_name','')}_{i}",
                content=c.page_content,
                metadata=c.metadata,
            )
            for i, c in enumerate(chunks)
        ]
        await self.vector_store.add(chunk_objs, embeddings)
        return len(chunks)

    async def query(self, question: str, top_k: int = 5,
                    history: list[dict] = None) -> dict:
        chunks = await self.retriever.retrieve(question, top_k=top_k)
        answer = await self.generator.generate(question, chunks, history)
        sources = self.generator.format_sources(chunks)
        return {"answer": answer, "sources": sources}

    async def query_stream(self, question: str, top_k: int = 5,
                           history: list[dict] = None) -> AsyncIterator[str]:
        chunks = await self.retriever.retrieve(question, top_k=top_k)
        self._last_sources = self.generator.format_sources(chunks)
        async for token in self.generator.generate_stream(question, chunks, history):
            yield token

    def get_last_sources(self) -> list[dict]:
        return getattr(self, "_last_sources", [])
