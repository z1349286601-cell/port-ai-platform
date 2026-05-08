from collections.abc import AsyncIterator
from app.core.llm import OpenAICompatibleClient
from app.core.llm.prompt_templates import RAG_SYSTEM_PROMPT, build_messages
from app.core.vector_store import ChunkWithScore
from app.core.context import sanitize_document_content


class Generator:
    def __init__(self, llm_client: OpenAICompatibleClient):
        self.llm_client = llm_client

    def _build_context(self, chunks: list[ChunkWithScore]) -> str:
        parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.metadata
            source = f"文档: {meta.get('doc_name','')}"
            if meta.get("section_title"):
                source += f" - {meta['section_title']}"
            content = sanitize_document_content(chunk.content)
            parts.append(f"[{i}] {source}\n{content}")
        return "\n\n---\n\n".join(parts)

    async def generate(self, query: str, chunks: list[ChunkWithScore],
                       history: list[dict] = None) -> str:
        context = self._build_context(chunks)
        user_message = f"参考资料：\n{context}\n\n用户问题：{query}"
        messages = build_messages(RAG_SYSTEM_PROMPT, user_message, history)
        return await self.llm_client.chat(messages)

    async def generate_stream(self, query: str, chunks: list[ChunkWithScore],
                              history: list[dict] = None) -> AsyncIterator[str]:
        context = self._build_context(chunks)
        user_message = f"参考资料：\n{context}\n\n用户问题：{query}"
        messages = build_messages(RAG_SYSTEM_PROMPT, user_message, history)
        async for token in self.llm_client.chat_stream(messages):
            yield token

    def format_sources(self, chunks: list[ChunkWithScore]) -> list[dict]:
        return [
            {
                "doc_name": c.metadata.get("doc_name", ""),
                "doc_title": c.metadata.get("doc_title", c.metadata.get("doc_name", "")),
                "section_title": c.metadata.get("section_title", ""),
                "relevance_score": round(c.score, 4),
                "excerpt": c.content[:100],
            }
            for c in chunks
        ]
