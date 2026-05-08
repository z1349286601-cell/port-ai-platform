import json
import uuid
import time
from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from app.core.context import generate_trace_id, sanitize_input
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest
from app.dependencies import get_rag_pipeline

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

MAX_SSE_CONNECTIONS = 50
SSE_IDLE_TIMEOUT = 120
SSE_MAX_DURATION = 300


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    x_demo_user: str = Header(None, alias="X-Demo-User"),
):
    user_id = x_demo_user or req.user_id
    trace_id = generate_trace_id()
    log = logger.bind(trace_id=trace_id)
    log.info(f"[{user_id}] message={req.message[:100]}")

    sanitized = sanitize_input(req.message)

    current_session_id = req.session_id or uuid.uuid4().hex
    start_time = time.time()

    async def event_stream():
        try:
            yield f"event: intent\ndata: {json.dumps({'intent': 'document_qa', 'confidence': 0.95, 'reasoning': 'Phase 1 default RAG'})}\n\n"

            rag = get_rag_pipeline()
            async for token in rag.query_stream(sanitized, top_k=5):
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            sources = rag.get_last_sources()
            if sources:
                yield f"event: sources\ndata: {json.dumps({'sources': sources})}\n\n"

            elapsed = int((time.time() - start_time) * 1000)
            yield f"event: done\ndata: {json.dumps({'session_id': current_session_id, 'message_id': 1, 'intent': 'document_qa', 'latency_ms': elapsed})}\n\n"

        except Exception as e:
            log.error(f"Stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'code': 'INTERNAL_ERROR', 'detail': str(e), 'trace_id': trace_id})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
