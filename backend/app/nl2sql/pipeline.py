from collections.abc import AsyncIterator
from pathlib import Path
from app.core.database.schema import DOMAIN_DDL_MAP
from app.core.llm import OpenAICompatibleClient
from app.core.config import settings
from app.nl2sql.schema_extractor import SchemaExtractor
from app.nl2sql.sql_generator import SQLGenerator
from app.nl2sql.sql_validator import SQLValidator
from app.nl2sql.executor import Executor, ExecutorError
from app.nl2sql.result_formatter import ResultFormatter


DOMAIN_TO_DB = {
    "production": "production",
    "equipment": "equipment",
    "energy": "energy",
}

# Resolve db_path against project root (same as config.py)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class NL2SQLPipeline:
    MAX_RETRIES = 3

    SQL_KEYWORDS_CN = {
        "集装箱": "production",
        "箱号": "production",
        "船舶": "production",
        "泊位": "production",
        "堆场": "production",
        "闸口": "production",
        "工班": "production",
        "吞吐量": "production",
        "作业量": "production",
        "设备": "equipment",
        "岸桥": "equipment",
        "门机": "equipment",
        "故障": "equipment",
        "维修": "equipment",
        "能耗": "energy",
        "用电": "energy",
        "发电": "energy",
        "碳排放": "energy",
    }

    def __init__(self, llm_client: OpenAICompatibleClient = None):
        self.llm_client = llm_client or OpenAICompatibleClient()
        self.schema_extractor = SchemaExtractor()
        self.sql_generator = SQLGenerator(self.llm_client)
        self.sql_validator = SQLValidator()
        self.executor = Executor()
        self.formatter = ResultFormatter(self.llm_client)

    def _detect_domain(self, question: str) -> str:
        for keyword, domain in self.SQL_KEYWORDS_CN.items():
            if keyword in question:
                return domain
        return "production"

    async def query(self, question: str, history: list[dict] = None) -> dict:
        domain = self._detect_domain(question)
        db_name = DOMAIN_TO_DB.get(domain, "production")
        db_path = str(_PROJECT_ROOT / "data" / "sqlite" / f"{db_name}.db")

        schema = await self.schema_extractor.extract(db_path, domain)

        sql = None
        last_errors = ""
        retry_count = 0
        for attempt in range(self.MAX_RETRIES):
            error_ctx = last_errors if attempt > 0 else None
            sql = await self.sql_generator.generate(question, schema, history, error_ctx)
            retry_count = attempt

            validation = await self.sql_validator.explain_validate(sql, db_path)
            if validation.is_valid:
                break
            last_errors = "; ".join(validation.errors)

        self._last_thinking = {
            "domain": domain,
            "sql": sql,
            "row_count": 0,
            "execution_ms": 0,
            "retry_count": retry_count,
            "cache_hit": self.sql_generator.last_cache_hit,
        }

        if sql is None or (last_errors and not validation.is_valid):
            return {"answer": f"抱歉，无法为此查询生成有效的SQL语句。请尝试更具体的查询条件。", "sources": []}

        try:
            result = await self.executor.execute(sql, db_path)
        except ExecutorError as e:
            self._last_thinking["execution_ms"] = e.elapsed_ms
            return {"answer": f"数据查询失败：{e.message}", "sources": []}

        self._last_thinking["row_count"] = result.row_count
        self._last_thinking["execution_ms"] = result.elapsed_ms

        answer = await self.formatter.format(result, question)
        return {
            "answer": answer,
            "sources": [],
            "sql": sql,
            "row_count": result.row_count,
            "elapsed_ms": result.elapsed_ms,
        }

    def get_last_thinking(self) -> dict:
        return getattr(self, "_last_thinking", {})

    async def query_stream(self, question: str, history: list[dict] = None) -> AsyncIterator[str]:
        result = await self.query(question, history)
        answer = result["answer"]
        for i in range(0, len(answer), 2):
            yield answer[i:i + 2]

    def get_last_sources(self) -> list[dict]:
        return []
