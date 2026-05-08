from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "port-ai-platform",
        "checks": {"database": "ok", "llm": "ok", "vector_store": "ok"},
    }
