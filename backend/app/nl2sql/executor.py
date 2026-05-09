import time
from dataclasses import dataclass, field
from pathlib import Path
from app.core.database.sqlite_client import SQLiteClient


@dataclass
class QueryResult:
    columns: list[str] = field(default_factory=list)
    rows: list[list] = field(default_factory=list)
    row_count: int = 0
    elapsed_ms: float = 0.0


class Executor:
    def __init__(self, timeout: float = 5.0, max_rows: int = 500):
        self.timeout = timeout
        self.max_rows = max_rows

    async def execute(self, sql: str, db_path: str) -> QueryResult:
        client = SQLiteClient(db_path)
        await client.connect()

        start = time.time()
        try:
            rows_dict = await client.execute_readonly(
                sql, timeout=self.timeout, max_rows=self.max_rows
            )
            elapsed_ms = (time.time() - start) * 1000

            if not rows_dict:
                return QueryResult(columns=[], rows=[], row_count=0, elapsed_ms=elapsed_ms)

            columns = list(rows_dict[0].keys())
            rows = [list(d.values()) for d in rows_dict]

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                elapsed_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = (time.time() - start) * 1000
            raise ExecutorError(str(e), elapsed_ms)
        finally:
            await client.close()


class ExecutorError(Exception):
    def __init__(self, message: str, elapsed_ms: float = 0):
        self.message = message
        self.elapsed_ms = elapsed_ms
        super().__init__(message)
