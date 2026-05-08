from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChunkWithScore:
    chunk_id: str
    content: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class BaseVectorStore(ABC):
    @abstractmethod
    async def add(self, chunks: list[ChunkWithScore], embeddings: list[list[float]]) -> None: ...

    @abstractmethod
    async def search(self, query_embedding: list[float], top_k: int = 5,
                     filter: dict = None) -> list[ChunkWithScore]: ...

    @abstractmethod
    async def delete(self, chunk_ids: list[str]) -> None: ...

    @abstractmethod
    async def count(self) -> int: ...
