from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    session_id: str | None = None
    channel: str = "web"
    user_id: str = "anonymous"


class IntentEvent(BaseModel):
    intent: str
    confidence: float
    reasoning: str = ""


class TokenEvent(BaseModel):
    token: str


class SourceItem(BaseModel):
    doc_name: str
    doc_title: str = ""
    section_title: str = ""
    relevance_score: float = 0.0
    excerpt: str = ""


class SourcesEvent(BaseModel):
    sources: list[SourceItem]


class DoneEvent(BaseModel):
    session_id: str
    message_id: int
    intent: str = ""
    latency_ms: int = 0


class ErrorEvent(BaseModel):
    code: str
    detail: str
    trace_id: str = ""


class ChatResponse(BaseModel):
    session_id: str
    message_id: int
    reply: str
    intent: str = ""
    sources: list[SourceItem] = []
