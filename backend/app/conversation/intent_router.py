import json
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from app.core.llm import OpenAICompatibleClient
from app.core.llm.prompt_templates import INTENT_CLASSIFY_SYSTEM_PROMPT
from app.core.config import settings


@dataclass
class IntentResult:
    intent: str
    confidence: float
    reasoning: str = ""
    rule_triggered: bool = False
    rule_sub_type: str | None = None


class IntentRouter:
    VALID_INTENTS = {"document_qa", "data_query", "mixed", "chitchat"}

    def __init__(self, llm_client: OpenAICompatibleClient = None,
                 rules_config_path: str = None):
        self.llm_client = llm_client or OpenAICompatibleClient()
        self.rules_config_path = rules_config_path or str(
            Path(__file__).parent.parent.parent.parent / "config" / "intent_rules.yaml"
        )
        self.rules: list[dict] = []
        self._load_rules()

    def _load_rules(self):
        try:
            with open(self.rules_config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                self.rules = config.get("rules", []) if config else []
        except FileNotFoundError:
            self.rules = []

    async def classify(self, message: str, history: list[dict] = None) -> IntentResult:
        llm_result = await self._llm_classify(message, history)

        if llm_result.confidence < settings.intent_confidence_threshold:
            rule_intent, rule_sub = self._rule_match(message)
            if rule_intent:
                return IntentResult(
                    intent=rule_intent,
                    confidence=llm_result.confidence,
                    reasoning=f"LLM({llm_result.intent}:{llm_result.confidence:.2f})→rule override→{rule_intent}",
                    rule_triggered=True,
                    rule_sub_type=rule_sub,
                )

        return llm_result

    async def _llm_classify(self, message: str, history: list[dict] = None) -> IntentResult:
        messages = [
            {"role": "system", "content": INTENT_CLASSIFY_SYSTEM_PROMPT},
        ]
        if history:
            messages.extend(history[-4:])
        messages.append({"role": "user", "content": message})

        raw = await self.llm_client.chat(messages)
        return self._parse_llm_response(raw)

    def _parse_llm_response(self, text: str) -> IntentResult:
        text = text.strip()
        # Strip markdown code fences
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            data = json.loads(text)
            intent = data.get("intent", "chitchat")
            if intent not in self.VALID_INTENTS:
                intent = "chitchat"
            confidence = float(data.get("confidence", 0.5))
            confidence = max(0.0, min(1.0, confidence))
            reasoning = data.get("reasoning", "")
            return IntentResult(intent=intent, confidence=confidence, reasoning=reasoning)
        except (json.JSONDecodeError, ValueError):
            # Fallback: attempt to extract intent from raw text
            for intent in self.VALID_INTENTS:
                if intent in text:
                    return IntentResult(intent=intent, confidence=0.5, reasoning="extracted from raw text")
            return IntentResult(intent="chitchat", confidence=0.3, reasoning="parse failed, default")

    def _rule_match(self, message: str) -> tuple[str | None, str | None]:
        for rule in self.rules:
            for pattern in rule.get("patterns", []):
                if re.search(pattern, message):
                    return rule["intent"], rule.get("sub_type")
        return None, None
