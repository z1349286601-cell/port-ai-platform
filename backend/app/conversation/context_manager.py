from dataclasses import dataclass, field
from app.conversation.session_store import SessionStore, Message
from app.core.config import settings


@dataclass
class Context:
    messages: list[dict] = field(default_factory=list)
    system_context: str = ""


class ContextManager:
    def __init__(self, max_messages: int = None, max_tokens: int = None):
        self.max_messages = max_messages or settings.max_context_messages
        self.max_tokens = max_tokens or settings.max_context_tokens

    async def build(self, session_id: str, current_message: str,
                    session_store: SessionStore) -> Context:
        messages = await session_store.get_messages(session_id, limit=self.max_messages)

        history = []
        last_assistant_reply = None

        for msg in messages:
            history.append({"role": msg.role, "content": msg.content})
            if msg.role == "assistant":
                last_assistant_reply = msg.content

        system_context = ""
        if last_assistant_reply:
            subject = self._extract_subject(last_assistant_reply)
            if subject:
                system_context = f"上一轮你回答了关于「{subject}」的问题。"

        history = self._truncate_by_tokens(history)
        history = history[-self.max_messages:]

        return Context(messages=history, system_context=system_context)

    def _extract_subject(self, assistant_reply: str) -> str:
        keywords = ["船舶", "集装箱", "箱号", "泊位", "堆场", "设备", "能耗",
                     "安全", "应急", "危险品", "靠泊", "卸船", "岸桥"]
        for kw in keywords:
            if kw in assistant_reply:
                return kw
        return ""

    def _truncate_by_tokens(self, messages: list[dict]) -> list[dict]:
        # Approximate token count: 1 token ≈ 2 chars for Chinese
        total = sum(len(m.get("content", "")) for m in messages)
        while total > self.max_tokens * 2 and len(messages) > 4:
            removed = messages.pop(0)
            total -= len(removed.get("content", ""))
        return messages
