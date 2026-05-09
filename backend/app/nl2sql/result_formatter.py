import json
from collections.abc import AsyncIterator
from app.nl2sql.executor import QueryResult
from app.nl2sql.schema_extractor import SchemaExtractor
from app.core.llm import OpenAICompatibleClient

# Reuse the column name → Chinese description mapping from schema_extractor
COLUMN_NAMES_CN = SchemaExtractor.COLUMN_DESC_OVERRIDES


def _translate_columns(columns: list[str]) -> list[str]:
    """Translate English column names to Chinese display names."""
    return [COLUMN_NAMES_CN.get(c, c) for c in columns]


def _translate_row(row: list, columns: list[str]) -> list[dict]:
    """Convert a raw row into a list of {name_cn, value} dicts."""
    cn_cols = _translate_columns(columns)
    return [{"name": cn, "value": val} for cn, val in zip(cn_cols, row)]


FORMATTER_SYSTEM_PROMPT = """你是港口AI平台的数据格式化助手。将数据库查询结果转换为清晰的中文自然语言。

格式化规则：
- 0行结果：表达"未找到匹配结果"，简要说明可能原因
- 1行结果：用自然语言逐字段描述
- 2-10行结果：先一句话汇总总数，然后用Markdown表格展示全部数据
- 11行以上：先总数+代表性样本说明，然后用Markdown表格展示前10条样本

输出要求：
- 使用中文
- **必须使用Markdown表格**展示多行数据，列名使用提供的中文名称
- 数字保留原始精度，日期时间保持原始格式
- 表格列对齐清晰，适合在聊天界面阅读
- 简洁直接，不要客套话"""


class ResultFormatter:
    def __init__(self, llm_client: OpenAICompatibleClient = None):
        self.llm_client = llm_client or OpenAICompatibleClient()

    async def format(self, result: QueryResult, question: str) -> str:
        if result.row_count == 0:
            return f"未找到与「{question[:50]}」相关的匹配结果。"

        if result.row_count == 1:
            return self._format_single_row(result, question)

        return await self._llm_format(result, question)

    async def format_stream(self, result: QueryResult, question: str) -> AsyncIterator[str]:
        text = await self.format(result, question)
        chunk_size = 2
        for i in range(0, len(text), chunk_size):
            yield text[i:i + chunk_size]

    def _format_single_row(self, result: QueryResult, question: str) -> str:
        row = result.rows[0]
        parts = []
        cn_cols = _translate_columns(result.columns)
        for col_cn, val in zip(cn_cols, row):
            if val is not None:
                parts.append(f"**{col_cn}**：{val}")
        return f"查询结果：\n\n" + "\n".join(f"- {p}" for p in parts)

    async def _llm_format(self, result: QueryResult, question: str) -> str:
        # Build human-readable data with Chinese column names
        cn_cols = _translate_columns(result.columns)
        rows_cn = []
        for row in result.rows:
            row_dict = {}
            for cn, val in zip(cn_cols, row):
                row_dict[cn] = val
            rows_cn.append(row_dict)

        data_text = json.dumps({
            "columns_cn": cn_cols,
            "columns_en": result.columns,
            "rows": rows_cn,
            "total_rows": result.row_count,
        }, ensure_ascii=False, indent=2)

        messages = [
            {"role": "system", "content": FORMATTER_SYSTEM_PROMPT},
            {"role": "user", "content": f"用户问题：{question}\n\n查询结果（列名已翻译为中文，请使用中文列名展示）：\n{data_text}"},
        ]
        return await self.llm_client.chat(messages)
