import pytest
from unittest.mock import AsyncMock, MagicMock
from app.conversation.context_manager import ContextManager, Context
from app.conversation.session_store import Session, Message


class TestTruncateByTokens:
    def setup_method(self):
        self.mgr = ContextManager(max_messages=20, max_tokens=4000)

    def test_no_truncation_when_under_budget(self):
        messages = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好，有什么可以帮助你的？"},
        ]
        result = self.mgr._truncate_by_tokens(messages)
        assert len(result) == 2

    def test_truncates_oldest_when_over_budget(self):
        self.mgr.max_tokens = 5  # ~10 chars
        messages = [
            {"role": "user", "content": "这是第一条很长的消息" * 10},   # ~100 chars
            {"role": "assistant", "content": "回复" * 20},              # ~40 chars
            {"role": "user", "content": "第三条"},                       # ~3 chars
            {"role": "assistant", "content": "第四条"},                   # ~3 chars
            {"role": "user", "content": "第五条"},                       # ~3 chars
        ]
        result = self.mgr._truncate_by_tokens(messages)
        assert len(result) < 5
        assert len(result) >= 4  # keeps at least 4

    def test_keeps_at_least_four_messages(self):
        self.mgr.max_tokens = 1  # impossibly small
        messages = [
            {"role": "user", "content": "消息1" * 100},
            {"role": "assistant", "content": "消息2" * 100},
            {"role": "user", "content": "消息3" * 100},
            {"role": "assistant", "content": "消息4" * 100},
            {"role": "user", "content": "消息5" * 100},
        ]
        result = self.mgr._truncate_by_tokens(messages)
        assert len(result) == 4  # minimum 4 preserved

    def test_empty_messages(self):
        result = self.mgr._truncate_by_tokens([])
        assert result == []


class TestExtractSubject:
    def setup_method(self):
        self.mgr = ContextManager()

    def test_finds_ship_keyword(self):
        subject = self.mgr._extract_subject("船舶预计明天到港，请做好准备。")
        assert subject == "船舶"

    def test_finds_container_keyword(self):
        subject = self.mgr._extract_subject("集装箱BC-101目前在A01贝位。")
        assert subject == "集装箱"

    def test_finds_first_keyword_only(self):
        subject = self.mgr._extract_subject("船舶和集装箱都需要检查。")
        assert subject == "船舶"  # appears first in keyword list

    def test_no_keyword_returns_empty(self):
        subject = self.mgr._extract_subject("好的，明白了。")
        assert subject == ""


class TestBuild:
    async def test_build_context_with_messages(self):
        mgr = ContextManager(max_messages=20, max_tokens=4000)
        session_store = AsyncMock()
        session_store.get_messages.return_value = [
            Message(id=1, session_id="s1", role="user", content="箱号BC-101在哪里", intent="", sources=[]),
            Message(id=2, session_id="s1", role="assistant", content="集装箱BC-101目前在A01贝位。", intent="data_query", sources=[]),
        ]

        ctx = await mgr.build("s1", "那BC-102呢", session_store)
        assert len(ctx.messages) == 2
        assert ctx.messages[0]["role"] == "user"
        assert ctx.messages[1]["role"] == "assistant"
        # "集装箱" is in the keyword list and appears in the assistant reply
        assert "集装箱" in ctx.system_context

    async def test_build_context_no_keyword_in_reply(self):
        mgr = ContextManager(max_messages=20, max_tokens=4000)
        session_store = AsyncMock()
        session_store.get_messages.return_value = [
            Message(id=1, session_id="s1", role="user", content="hello", intent="", sources=[]),
            Message(id=2, session_id="s1", role="assistant", content="你好，请问有什么可以帮助你的？", intent="chitchat", sources=[]),
        ]

        ctx = await mgr.build("s1", "帮我查一下", session_store)
        assert ctx.system_context == ""

    async def test_build_with_too_many_messages_truncates(self):
        mgr = ContextManager(max_messages=4, max_tokens=4000)
        session_store = AsyncMock()
        msgs = []
        for i in range(10):
            msgs.append(Message(id=i, session_id="s1", role="user" if i % 2 == 0 else "assistant",
                                content=f"消息{i}", intent="", sources=[]))
        session_store.get_messages.return_value = msgs

        ctx = await mgr.build("s1", "新问题", session_store)
        # max_messages limits to last 4
        assert len(ctx.messages) <= 4


class TestContext:
    def test_default_values(self):
        c = Context()
        assert c.messages == []
        assert c.system_context == ""

    def test_custom_values(self):
        c = Context(messages=[{"role": "user", "content": "hi"}], system_context="ctx")
        assert len(c.messages) == 1
        assert c.system_context == "ctx"
