from openai import AsyncOpenAI
from app.core.embedding.base import BaseEmbeddingClient
from app.core.config import settings


class OpenAIEmbeddingClient(BaseEmbeddingClient):
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.embedding_base_url,
            api_key=settings.llm_api_key,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = await self.client.embeddings.create(
            model=settings.embedding_model_name,
            input=texts,
        )
        return [d.embedding for d in response.data]

    async def embed_query(self, text: str) -> list[float]:
        results = await self.embed([text])
        return results[0]
