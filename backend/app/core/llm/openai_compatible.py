from openai import AsyncOpenAI
from collections.abc import AsyncIterator
from app.core.llm.base import BaseLLMClient
from app.core.config import settings


class OpenAICompatibleClient(BaseLLMClient):
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )

    async def chat(self, messages: list[dict], **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=False,
        )
        return response.choices[0].message.content or ""

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=settings.llm_model_name,
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 2048),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
