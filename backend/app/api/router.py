from fastapi import APIRouter
from app.api.chat import router as chat_router
from app.api.knowledge import router as knowledge_router
from app.api.session import router as session_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(knowledge_router)
api_router.include_router(session_router)
api_router.include_router(health_router)
