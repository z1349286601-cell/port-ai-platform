from app.core.llm.base import BaseLLMClient
from app.core.llm.openai_compatible import OpenAICompatibleClient
from app.core.llm.prompt_templates import (
    INTENT_CLASSIFY_SYSTEM_PROMPT,
    RAG_SYSTEM_PROMPT,
    NL2SQL_SYSTEM_PROMPT,
    CHITCHAT_SYSTEM_PROMPT,
    build_messages,
)
