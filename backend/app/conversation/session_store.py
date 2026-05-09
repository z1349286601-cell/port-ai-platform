from __future__ import annotations
import json
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from pathlib import Path
from app.core.database.sqlite_client import SQLiteClient, get_db_client
from app.core.config import settings


class Session:
    def __init__(self, session_id: str, channel: str = "web", user_id: str = "anonymous",
                 title: str = "", status: str = "active", message_count: int = 0,
                 created_at: str = "", updated_at: str = ""):
        self.session_id = session_id
        self.channel = channel
        self.user_id = user_id
        self.title = title or ""
        self.status = status
        self.message_count = message_count
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "channel": self.channel,
            "user_id": self.user_id,
            "title": self.title,
            "status": self.status,
            "message_count": self.message_count,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Message:
    def __init__(self, id: int = 0, session_id: str = "", role: str = "user",
                 content: str = "", intent: str = None, sources: list = None,
                 created_at: str = ""):
        self.id = id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.intent = intent
        self.sources = sources or []
        self.created_at = created_at

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "intent": self.intent,
            "sources": self.sources,
            "created_at": self.created_at,
        }


class SessionStore(ABC):
    @abstractmethod
    async def create(self, channel: str = "web", user_id: str = "anonymous",
                     title: str = "") -> Session: ...

    @abstractmethod
    async def get(self, session_id: str) -> Session | None: ...

    @abstractmethod
    async def list(self, user_id: str = None, limit: int = 20) -> list[Session]: ...

    @abstractmethod
    async def delete(self, session_id: str) -> bool: ...

    @abstractmethod
    async def add_message(self, session_id: str, role: str, content: str,
                          intent: str = None, sources: list = None) -> Message: ...

    @abstractmethod
    async def update_title(self, session_id: str, title: str) -> bool: ...

    @abstractmethod
    async def get_messages(self, session_id: str, limit: int = 50) -> list[Message]: ...


class SqliteSessionStore(SessionStore):
    def __init__(self):
        self._db: SQLiteClient | None = None

    async def _get_db(self) -> SQLiteClient:
        if self._db is None:
            self._db = await get_db_client("sessions")
        return self._db

    async def create(self, channel: str = "web", user_id: str = "anonymous",
                     title: str = "") -> Session:
        db = await self._get_db()
        session_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        await db.conn.execute(
            """INSERT INTO sessions (session_id, channel, user_id, title, status, message_count, created_at, updated_at)
               VALUES (?, ?, ?, ?, 'active', 0, ?, ?)""",
            (session_id, channel, user_id, title, now, now)
        )
        await db.conn.commit()
        return Session(
            session_id=session_id, channel=channel, user_id=user_id,
            title=title, status="active", created_at=now, updated_at=now
        )

    async def get(self, session_id: str) -> Session | None:
        db = await self._get_db()
        row = await db.fetch_one(
            "SELECT * FROM sessions WHERE session_id = ? AND status != 'deleted'",
            (session_id,)
        )
        if not row:
            return None
        return Session(**self._row_to_session(row))

    async def list(self, user_id: str = None, limit: int = 20) -> list[Session]:
        db = await self._get_db()
        if user_id:
            rows = await db.fetch_all(
                "SELECT * FROM sessions WHERE user_id = ? AND status != 'deleted' ORDER BY updated_at DESC LIMIT ?",
                (user_id, limit)
            )
        else:
            rows = await db.fetch_all(
                "SELECT * FROM sessions WHERE status != 'deleted' ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
        return [Session(**self._row_to_session(r)) for r in rows]

    async def delete(self, session_id: str) -> bool:
        db = await self._get_db()
        cursor = await db.conn.execute(
            "UPDATE sessions SET status = 'deleted', updated_at = ? WHERE session_id = ?",
            (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"), session_id)
        )
        await db.conn.commit()
        return cursor.rowcount > 0

    async def update_title(self, session_id: str, title: str) -> bool:
        db = await self._get_db()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        cursor = await db.conn.execute(
            "UPDATE sessions SET title = ?, updated_at = ? WHERE session_id = ? AND status != 'deleted'",
            (title[:20], now, session_id)
        )
        await db.conn.commit()
        return cursor.rowcount > 0

    async def add_message(self, session_id: str, role: str, content: str,
                          intent: str = None, sources: list = None) -> Message:
        db = await self._get_db()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
        cursor = await db.conn.execute(
            """INSERT INTO messages (session_id, role, content, intent, sources, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, role, content, intent, sources_json, now)
        )
        await db.conn.execute(
            "UPDATE sessions SET message_count = message_count + 1, updated_at = ? WHERE session_id = ?",
            (now, session_id)
        )
        await db.conn.commit()
        return Message(
            id=cursor.lastrowid, session_id=session_id, role=role,
            content=content, intent=intent, sources=sources, created_at=now
        )

    async def get_messages(self, session_id: str, limit: int = 50) -> list[Message]:
        db = await self._get_db()
        rows = await db.fetch_all(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC LIMIT ?",
            (session_id, limit)
        )
        messages = []
        for r in rows:
            sources = None
            if r.get("sources"):
                try:
                    sources = json.loads(r["sources"])
                except (json.JSONDecodeError, TypeError):
                    sources = []
            messages.append(Message(
                id=r["id"], session_id=r["session_id"], role=r["role"],
                content=r["content"], intent=r.get("intent"),
                sources=sources, created_at=r.get("created_at", "")
            ))
        return messages

    @staticmethod
    def _row_to_session(row: dict) -> dict:
        return {
            "session_id": row["session_id"],
            "channel": row.get("channel", "web"),
            "user_id": row.get("user_id", "anonymous"),
            "title": row.get("title", ""),
            "status": row.get("status", "active"),
            "message_count": row.get("message_count", 0),
            "created_at": row.get("created_at", ""),
            "updated_at": row.get("updated_at", ""),
        }
