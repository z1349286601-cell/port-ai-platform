import re
from datetime import date
from app.core.llm import OpenAICompatibleClient
from app.nl2sql.prompt_templates import NL2SQL_SYSTEM_PROMPT, FEW_SHOT_EXAMPLES, CORRECT_ERROR_PROMPT
from app.nl2sql.schema_extractor import SchemaDescription


def _normalize(text: str) -> str:
    """Remove whitespace for fuzzy matching."""
    return re.sub(r'\s+', '', text).lower()


# Pre-parse few-shot Q/A pairs for cache lookup
def _parse_few_shot_pairs() -> list[tuple[str, str]]:
    pairs = []
    for block in FEW_SHOT_EXAMPLES.strip().split('\n\n'):
        lines = block.strip().split('\n')
        q = a = None
        for line in lines:
            if line.startswith('Q:'):
                q = line[2:].strip()
            elif line.startswith('A:'):
                a = line[2:].strip()
        if q and a:
            pairs.append((q, a))
    return pairs


FEW_SHOT_PAIRS: list[tuple[str, str]] = _parse_few_shot_pairs()


class SQLGenerator:
    def __init__(self, llm_client: OpenAICompatibleClient = None):
        self.llm_client = llm_client or OpenAICompatibleClient()
        self._last_cache_hit = False

    @property
    def last_cache_hit(self) -> bool:
        return self._last_cache_hit

    def _match_few_shot(self, question: str) -> str | None:
        """Return cached SQL if question closely matches a few-shot example."""
        norm_q = _normalize(question)
        best_sql = None
        best_len = 0
        for q, sql in FEW_SHOT_PAIRS:
            norm_example = _normalize(q)
            if norm_example in norm_q or norm_q in norm_example:
                if len(norm_example) > best_len:
                    best_sql = sql
                    best_len = len(norm_example)
        self._last_cache_hit = best_sql is not None
        return best_sql

    async def generate(self, question: str, schema: SchemaDescription,
                       history: list[dict] = None,
                       error_context: str = None) -> str:
        # Quick path: exact or near-exact match against few-shot examples
        if not error_context:
            cached = self._match_few_shot(question)
            if cached:
                return self._clean_sql(cached)

        if error_context:
            prompt = CORRECT_ERROR_PROMPT.format(errors=error_context)
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ]
            raw = await self.llm_client.chat(messages)
        else:
            system = (NL2SQL_SYSTEM_PROMPT
                .replace("__SCHEMA_DESC__", schema.to_prompt_text())
                .replace("__CURRENT_DATE__", date.today().isoformat())
                .replace("__FEW_SHOT_EXAMPLES__", FEW_SHOT_EXAMPLES)
                .replace("__USER_QUERY__", question))

            messages = [{"role": "system", "content": system}]
            if history:
                messages = [messages[0]] + history[-6:] + [{"role": "user", "content": question}]
            else:
                messages.append({"role": "user", "content": question})
            raw = await self.llm_client.chat(messages)

        return self._clean_sql(raw)

    def _clean_sql(self, text: str) -> str:
        text = text.strip()
        if text.startswith("```sql"):
            text = text[6:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip().rstrip(";")
        return text
