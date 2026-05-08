from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)


@router.post("/stream")
async def chat_stream(
    req: ChatRequest,
    x_demo_user: str = Header(None, alias="X-Demo-User"),
):
    user_id = x_demo_user or req.user_id

    async def event_stream():
        import json
        from app.core.context import generate_trace_id
        trace_id = generate_trace_id()
        logger.bind(trace_id=trace_id).info(f"[{user_id}] {req.message}")

        # Phase 1 stub: echo response as SSE
        yield f"event: intent\ndata: {json.dumps({'intent': 'chitchat', 'confidence': 0.95, 'reasoning': 'stub'})}\n\n"
        for token in f"收到消息: {req.message}":
            yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        import uuid
        yield f"event: done\ndata: {json.dumps({'session_id': req.session_id or uuid.uuid4().hex, 'message_id': 1, 'intent': 'chitchat', 'latency_ms': 0})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
