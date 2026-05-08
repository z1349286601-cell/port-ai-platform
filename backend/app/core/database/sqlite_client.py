import aiosqlite
import os
from pathlib import Path
from app.core.config import settings


class SQLiteClient:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn: aiosqlite.Connection | None = None

    async def connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = await aiosqlite.connect(self.db_path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.execute("PRAGMA journal_mode=WAL")
        await self._conn.execute("PRAGMA foreign_keys=ON")

    async def close(self):
        if self._conn:
            await self._conn.close()

    @property
    def conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self._conn

    async def execute(self, sql: str, params: tuple = ()) -> aiosqlite.Cursor:
        return await self._conn.execute(sql, params)

    async def fetch_all(self, sql: str, params: tuple = ()) -> list[dict]:
        cursor = await self._conn.execute(sql, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def fetch_one(self, sql: str, params: tuple = ()) -> dict | None:
        cursor = await self._conn.execute(sql, params)
        row = await cursor.fetchone()
        return dict(row) if row else None

    async def execute_readonly(self, sql: str, params: tuple = (), timeout: float = 5.0,
                               max_rows: int = 500) -> list[dict]:
        await self._conn.execute(f"PRAGMA query_only=ON")
        try:
            self._conn._conn.set_progress_handler(lambda: None, int(timeout * 1000))
            cursor = await self._conn.execute(f"SELECT * FROM ({sql}) LIMIT {max_rows}", params)
            rows = await cursor.fetchall()
            cols = [desc[0] for desc in cursor.description] if cursor.description else []
        finally:
            await self._conn.execute("PRAGMA query_only=OFF")

        return [dict(zip(cols, row)) for row in rows]


_db_clients: dict[str, SQLiteClient] = {}


async def get_db_client(db_name: str) -> SQLiteClient:
    if db_name not in _db_clients:
        db_path = str(Path(settings.sqlite_data_dir) / f"{db_name}.db")
        client = SQLiteClient(db_path)
        await client.connect()
        _db_clients[db_name] = client
    return _db_clients[db_name]


async def close_all_db_clients():
    for client in _db_clients.values():
        await client.close()
    _db_clients.clear()
