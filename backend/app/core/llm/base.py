from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class BaseLLMClient(ABC):

    @abstractmethod
    async def chat(self, messages: list[dict], **kwargs) -> str: ...

    @abstractmethod
    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]: ...
