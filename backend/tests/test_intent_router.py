import pytest
from unittest.mock import AsyncMock, MagicMock
from app.conversation.intent_router import IntentRouter, IntentResult


class TestParseLlmResponse:
    def setup_method(self):
        self.router = IntentRouter.__new__(IntentRouter)
        self.router.rules = []
        self.router.rules_config_path = ""

    def test_valid_json_document_qa(self):
        json_str = '{"intent": "document_qa", "confidence": 0.95, "reasoning": "asks about SOP"}'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "document_qa"
        assert result.confidence == 0.95
        assert result.reasoning == "asks about SOP"

    def test_valid_json_data_query(self):
        json_str = '{"intent": "data_query", "confidence": 0.9}'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "data_query"
        assert result.confidence == 0.9

    def test_valid_json_mixed(self):
        json_str = '{"intent": "mixed", "confidence": 0.85}'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "mixed"

    def test_valid_json_chitchat(self):
        json_str = '{"intent": "chitchat", "confidence": 0.99}'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "chitchat"

    def test_markdown_code_fence_stripped(self):
        json_str = '```json\n{"intent": "data_query", "confidence": 0.8}\n```'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "data_query"

    def test_markdown_code_fence_no_lang(self):
        json_str = '```\n{"intent": "document_qa", "confidence": 0.7}\n```'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "document_qa"

    def test_invalid_intent_defaults_to_chitchat(self):
        json_str = '{"intent": "unknown", "confidence": 0.8}'
        result = self.router._parse_llm_response(json_str)
        assert result.intent == "chitchat"

    def test_confidence_clamped_to_zero(self):
        json_str = '{"intent": "document_qa", "confidence": -0.5}'
        result = self.router._parse_llm_response(json_str)
        assert result.confidence == 0.0

    def test_confidence_clamped_to_one(self):
        json_str = '{"intent": "document_qa", "confidence": 2.5}'
        result = self.router._parse_llm_response(json_str)
        assert result.confidence == 1.0

    def test_json_parse_failure_fallback_extracts_intent(self):
        result = self.router._parse_llm_response("I think the intent is data_query for this query")
        assert result.intent == "data_query"
        assert result.confidence == 0.5

    def test_json_parse_failure_no_intent_defaults(self):
        result = self.router._parse_llm_response("something completely unrelated")
        assert result.intent == "chitchat"
        assert result.confidence == 0.3

    def test_empty_string(self):
        result = self.router._parse_llm_response("")
        assert result.intent == "chitchat"
        assert result.confidence == 0.3


class TestRuleMatch:
    def setup_method(self):
        self.router = IntentRouter.__new__(IntentRouter)
        self.router.rules = [
            {"patterns": [r"箱.*在哪", r"查询.*贝位", r"箱号"], "intent": "data_query"},
            {"patterns": [r"安全.*规定", r"SOP"], "intent": "document_qa"},
            {"patterns": [r"你好", r"谢谢"], "intent": "chitchat"},
        ]

    def test_rule_matches_single_box(self):
        assert self.router._rule_match("BC-101箱在哪里")[0] == "data_query"

    def test_rule_matches_document_qa(self):
        assert self.router._rule_match("安全规定是什么")[0] == "document_qa"

    def test_rule_matches_chitchat(self):
        assert self.router._rule_match("你好啊")[0] == "chitchat"

    def test_rule_no_match_returns_none(self):
        assert self.router._rule_match("今天天气怎么样")[0] is None

    def test_rules_empty_returns_none(self):
        self.router.rules = []
        assert self.router._rule_match("箱号查询")[0] is None


class TestClassifyWithRuleFallback:
    async def test_high_confidence_uses_llm_only(self):
        router = IntentRouter.__new__(IntentRouter)
        router.rules = [{"patterns": [r"箱号"], "intent": "data_query"}]
        router.llm_client = AsyncMock()
        router.llm_client.chat.return_value = '{"intent": "document_qa", "confidence": 0.95}'
        router._load_rules = MagicMock()

        result = await router.classify("箱号BC-101在哪里")
        assert result.intent == "document_qa"

    async def test_low_confidence_falls_back_to_rules(self):
        import app.core.config as cfg
        router = IntentRouter.__new__(IntentRouter)
        router.rules = [{"patterns": [r"箱号"], "intent": "data_query"}]
        router.llm_client = AsyncMock()
        router.llm_client.chat.return_value = '{"intent": "chitchat", "confidence": 0.3}'
        router._load_rules = MagicMock()

        # confidence 0.3 < threshold 0.7, rule should override
        result = await router.classify("箱号BC-101在哪里")
        assert result.intent == "data_query"


class TestIntentResult:
    def test_dataclass_fields(self):
        r = IntentResult(intent="document_qa", confidence=0.9, reasoning="test")
        assert r.intent == "document_qa"
        assert r.confidence == 0.9
        assert r.reasoning == "test"

    def test_default_reasoning(self):
        r = IntentResult(intent="chitchat", confidence=0.5)
        assert r.reasoning == ""
