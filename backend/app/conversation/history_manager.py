from app.conversation.session_store import SessionStore
from app.core.llm import OpenAICompatibleClient


SUMMARY_PROMPT = """将以下对话历史压缩为一段简短摘要，保留关键实体（船名、箱号、泊位等）和用户的查询意图。

对话历史：
{history_text}

摘要（不超过200字）："""


class HistoryManager:
    MAX_TURNS_BEFORE_COMPRESS = 30
    KEEP_RECENT = 10

    def __init__(self, llm_client: OpenAICompatibleClient = None):
        self.llm_client = llm_client or OpenAICompatibleClient()

    async def save_turn(self, session_id: str, user_msg: str,
                        assistant_msg: str, intent: str,
                        sources: list[dict] = None,
                        session_store: SessionStore = None):
        if session_store is None:
            return

        await session_store.add_message(
            session_id=session_id, role="user",
            content=user_msg, intent=intent
        )
        await session_store.add_message(
            session_id=session_id, role="assistant",
            content=assistant_msg, intent=intent, sources=sources
        )

    async def maybe_compress(self, session_id: str,
                             session_store: SessionStore):
        messages = await session_store.get_messages(session_id, limit=200)
        user_assistant = [m for m in messages if m.role in ("user", "assistant")]

        if len(user_assistant) < self.MAX_TURNS_BEFORE_COMPRESS * 2:
            return

        older = user_assistant[:-(self.KEEP_RECENT * 2)]
        if not older:
            return

        history_text = "\n".join(
            f"{'用户' if m.role == 'user' else '助手'}: {m.content[:200]}"
            for m in older
        )

        messages_payload = [
            {"role": "system", "content": "你是一个对话摘要助手。"},
            {"role": "user", "content": SUMMARY_PROMPT.format(history_text=history_text)},
        ]
        summary = await self.llm_client.chat(messages_payload)

        await session_store.add_message(
            session_id=session_id, role="system",
            content=f"[对话摘要] {summary.strip()}"
        )
