import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.nl2sql.result_formatter import ResultFormatter, FORMATTER_SYSTEM_PROMPT
from app.nl2sql.executor import QueryResult


class TestResultFormatter:
    def setup_method(self):
        self.mock_llm = AsyncMock()
        self.formatter = ResultFormatter(llm_client=self.mock_llm)

    @pytest.mark.asyncio
    async def test_zero_rows_returns_not_found(self):
        result = QueryResult(columns=["name"], rows=[], row_count=0)
        text = await self.formatter.format(result, "查询BC-999在哪")
        assert "未找到" in text
        assert "BC-999" in text

    @pytest.mark.asyncio
    async def test_zero_rows_truncates_long_question(self):
        long_q = "查询" + "A" * 100
        result = QueryResult(columns=[], rows=[], row_count=0)
        text = await self.formatter.format(result, long_q)
        assert "未找到" in text
        # question truncated to 50 chars in output
        assert len(long_q) > 50

    @pytest.mark.asyncio
    async def test_single_row_format(self):
        result = QueryResult(
            columns=["container_code", "current_bay"],
            rows=[["BC-101", "A01"]],
            row_count=1,
        )
        text = await self.formatter.format(result, "BC-101在哪")
        assert "BC-101" in text
        assert "A01" in text

    @pytest.mark.asyncio
    async def test_single_row_skips_none_values(self):
        result = QueryResult(
            columns=["name", "status", "note"],
            rows=[["BC-101", None, "ok"]],
            row_count=1,
        )
        text = await self.formatter.format(result, "查询")
        assert "BC-101" in text
        assert "ok" in text
        assert "status" not in text  # None skipped

    @pytest.mark.asyncio
    async def test_small_list_uses_llm(self):
        self.mock_llm.chat.return_value = "共3条记录：..."
        result = QueryResult(
            columns=["code", "bay"],
            rows=[["A", "1"], ["B", "2"], ["C", "3"]],
            row_count=3,
        )
        text = await self.formatter.format(result, "查询")
        self.mock_llm.chat.assert_called_once()
        assert text == "共3条记录：..."

    @pytest.mark.asyncio
    async def test_large_list_samples_top_10(self):
        self.mock_llm.chat.return_value = "共50条记录，前10条为：..."
        result = QueryResult(
            columns=["code"],
            rows=[[f"item-{i}"] for i in range(50)],
            row_count=50,
        )
        text = await self.formatter.format(result, "查询")
        # Verify LLM got only 10 rows in its prompt
        call_data = self.mock_llm.chat.call_args[0][0]
        user_msg = call_data[1]["content"]
        # 50 rows but only 10 sent to LLM
        assert "50" in user_msg  # total_rows in JSON
        assert text == "共50条记录，前10条为：..."

    @pytest.mark.asyncio
    async def test_format_stream_yields_chunks(self):
        result = QueryResult(
            columns=["code"],
            rows=[["BC-101"]],
            row_count=1,
        )
        chunks = []
        async for chunk in self.formatter.format_stream(result, "查询"):
            chunks.append(chunk)
        full = "".join(chunks)
        assert "BC-101" in full

    def test_formatter_system_prompt_contains_rules(self):
        assert "0行" in FORMATTER_SYSTEM_PROMPT
        assert "1行" in FORMATTER_SYSTEM_PROMPT
        assert "2-10行" in FORMATTER_SYSTEM_PROMPT
        assert "11行以上" in FORMATTER_SYSTEM_PROMPT
        assert "中文" in FORMATTER_SYSTEM_PROMPT
