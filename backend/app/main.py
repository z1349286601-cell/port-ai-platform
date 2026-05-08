from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.logging import setup_logging, get_logger
from app.core.middleware import setup_middleware
from app.core.exceptions import app_exception_handler, general_exception_handler, AppException
from app.core.database import close_all_db_clients
from app.api.router import api_router

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Port AI Platform starting up...")
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
