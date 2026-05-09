import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import setup_logging, get_logger
from app.core.middleware import setup_middleware
from app.core.exceptions import app_exception_handler, general_exception_handler, AppException
from app.core.database import close_all_db_clients
from app.core.database.schema import SESSIONS_DDL
from app.core.config import settings
from app.api.router import api_router
import aiosqlite

setup_logging()
logger = get_logger(__name__)


async def _ensure_sessions_schema():
    """Ensure sessions.db has the correct schema tables."""
    sqlite_dir = os.path.abspath(settings.sqlite_data_dir)
    db_path = os.path.join(sqlite_dir, "sessions.db")
    os.makedirs(sqlite_dir, exist_ok=True)

    conn = await aiosqlite.connect(db_path)
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    await conn.executescript(SESSIONS_DDL)
    await conn.commit()
    await conn.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Port AI Platform starting up...")
    logger.info(f"SQLite data dir: {os.path.abspath(settings.sqlite_data_dir)}")
    await _ensure_sessions_schema()
    logger.info("Sessions database schema ensured")
    yield
    logger.info("Port AI Platform shutting down...")
    await close_all_db_clients()


app = FastAPI(
    title="Port AI Intelligent Platform",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

setup_middleware(app)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "Port AI Platform", "version": "0.1.0", "status": "ok"}
