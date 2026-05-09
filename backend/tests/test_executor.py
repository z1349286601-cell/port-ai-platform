import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.nl2sql.executor import Executor, QueryResult, ExecutorError


class TestQueryResult:
    def test_default_values(self):
        r = QueryResult()
        assert r.columns == []
        assert r.rows == []
        assert r.row_count == 0
        assert r.elapsed_ms == 0.0

    def test_custom_values(self):
        r = QueryResult(
            columns=["name", "count"],
            rows=[["A01", 5], ["A02", 3]],
            row_count=2,
            elapsed_ms=15.5,
        )
        assert r.columns == ["name", "count"]
        assert len(r.rows) == 2
        assert r.row_count == 2
        assert r.elapsed_ms == 15.5


class TestExecutorError:
    def test_basic_error(self):
        err = ExecutorError("timeout", elapsed_ms=5000)
        assert err.message == "timeout"
        assert err.elapsed_ms == 5000
        assert isinstance(err, Exception)
        assert str(err) == "timeout"

    def test_default_elapsed(self):
        err = ExecutorError("error")
        assert err.elapsed_ms == 0


class TestExecutor:
    def test_init_defaults(self):
        executor = Executor()
        assert executor.timeout == 5.0
        assert executor.max_rows == 500

    def test_init_custom(self):
        executor = Executor(timeout=3.0, max_rows=100)
        assert executor.timeout == 3.0
        assert executor.max_rows == 100

    @pytest.mark.asyncio
    async def test_execute_with_results(self):
        executor = Executor()

        mock_client = AsyncMock()
        mock_client.execute_readonly.return_value = [
            {"name": "A01", "cnt": 5},
            {"name": "A02", "cnt": 3},
        ]

        with patch("app.nl2sql.executor.SQLiteClient", return_value=mock_client):
            result = await executor.execute("SELECT * FROM t", "test.db")

        assert result.row_count == 2
        assert result.columns == ["name", "cnt"]
        assert result.rows == [["A01", 5], ["A02", 3]]
        assert result.elapsed_ms > 0
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_empty_results(self):
        executor = Executor()

        mock_client = AsyncMock()
        mock_client.execute_readonly.return_value = []

        with patch("app.nl2sql.executor.SQLiteClient", return_value=mock_client):
            result = await executor.execute("SELECT * FROM t WHERE 1=0", "test.db")

        assert result.row_count == 0
        assert result.columns == []
        assert result.rows == []

    @pytest.mark.asyncio
    async def test_execute_raises_executor_error(self):
        executor = Executor()

        mock_client = AsyncMock()
        mock_client.execute_readonly.side_effect = Exception("syntax error")

        with patch("app.nl2sql.executor.SQLiteClient", return_value=mock_client):
            with pytest.raises(ExecutorError) as exc_info:
                await executor.execute("BAD SQL", "test.db")
            assert "syntax error" in str(exc_info.value)
            assert exc_info.value.elapsed_ms > 0

    @pytest.mark.asyncio
    async def test_executor_closes_client_on_error(self):
        executor = Executor()

        mock_client = AsyncMock()
        mock_client.execute_readonly.side_effect = Exception("error")

        with patch("app.nl2sql.executor.SQLiteClient", return_value=mock_client):
            with pytest.raises(ExecutorError):
                await executor.execute("SELECT * FROM t", "test.db")
            mock_client.close.assert_called_once()
