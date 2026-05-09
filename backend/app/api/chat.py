import json
import uuid
import time
import asyncio
from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from app.core.context import generate_trace_id, sanitize_input
from app.core.logging import get_logger
from app.schemas.chat import ChatRequest
from app.dependencies import (
    get_rag_pipeline, get_nl2sql_pipeline, get_intent_router,
    get_session_store, get_context_manager, get_history_manager,
)

router = APIRouter(prefix="/chat", tags=["chat"])
logger = get_logger(__name__)

MAX_SSE_CONNECTIONS = 50
SSE_IDLE_TIMEOUT = 120
SSE_MAX_DURATION = 300


def _build_thinking_event(intent_result, rag_meta: dict = None, nl2sql_meta: dict = None) -> dict:
    thinking = {
        "intent": intent_result.intent,
        "confidence": intent_result.confidence,
        "reasoning": intent_result.reasoning,
        "rule_triggered": intent_result.rule_triggered,
    }
    if intent_result.rule_sub_type:
        thinking["rule_sub_type"] = intent_result.rule_sub_type
    if rag_meta:
        thinking.update(rag_meta)
    if nl2sql_meta:
        thinking.update(nl2sql_meta)
    return thinking


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
    start_time = time.time()

    session_store = get_session_store()
    context_mgr = get_context_manager()
    history_mgr = get_history_manager()
    intent_router = get_intent_router()
    rag = get_rag_pipeline()
    nl2sql = get_nl2sql_pipeline()

    # Resolve session (fast — SQLite lookup, do it before streaming)
    current_session_id = req.session_id
    if current_session_id:
        session = await session_store.get(current_session_id)
        if session is None:
            current_session_id = None

    if current_session_id is None:
        session = await session_store.create(channel=req.channel, user_id=user_id)
        current_session_id = session.session_id

    # Build context (fast — SQLite lookup)
    ctx = await context_mgr.build(current_session_id, sanitized, session_store)

    async def event_stream():
        try:
            # Send immediate connected event so client knows we're alive
            yield f"event: connected\ndata: {json.dumps({'session_id': current_session_id, 'trace_id': trace_id})}\n\n"

            # Intent classification (first slow LLM call)
            intent_result = await intent_router.classify(
                sanitized, history=ctx.messages
            )
            log.info(f"intent={intent_result.intent} confidence={intent_result.confidence:.2f}")

            yield f"event: intent\ndata: {json.dumps({'intent': intent_result.intent, 'confidence': intent_result.confidence, 'reasoning': intent_result.reasoning})}\n\n"

            rag_answer = ""
            nl2sql_answer = ""
            all_sources = []
            rag_meta = None
            nl2sql_meta = None

            # Route by intent — three-phase: execute → thinking → stream
            if intent_result.intent == "document_qa":
                # Phase 1: retrieve
                rag_meta = await rag.retrieve(sanitized, top_k=5)

                # Phase 2: emit thinking
                yield f"event: thinking\ndata: {json.dumps(_build_thinking_event(intent_result, rag_meta=rag_meta))}\n\n"

                # Phase 3: stream tokens
                async for token in rag.stream_from_pending(sanitized, history=ctx.messages):
                    rag_answer += token
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
                all_sources = rag.get_last_sources()

            elif intent_result.intent == "data_query":
                # Phase 1: execute full pipeline (generate SQL + validate + execute + format)
                result = await nl2sql.query(sanitized, history=ctx.messages)
                nl2sql_answer = result["answer"]
                nl2sql_meta = nl2sql.get_last_thinking()

                # Phase 2: emit thinking
                yield f"event: thinking\ndata: {json.dumps(_build_thinking_event(intent_result, nl2sql_meta=nl2sql_meta))}\n\n"

                # Phase 3: stream tokens
                for i in range(0, len(nl2sql_answer), 2):
                    yield f"event: token\ndata: {json.dumps({'token': nl2sql_answer[i:i+2]})}\n\n"

            elif intent_result.intent == "mixed":
                # Phase 1: execute both pipelines in parallel
                rag_task = asyncio.create_task(_collect_rag(rag, sanitized, ctx.messages))
                nl2sql_task = asyncio.create_task(_collect_nl2sql(nl2sql, sanitized, ctx.messages))

                rag_answer, rag_sources, rag_meta = await rag_task
                nl2sql_answer, nl2sql_meta = await nl2sql_task

                # Phase 2: emit thinking
                yield f"event: thinking\ndata: {json.dumps(_build_thinking_event(intent_result, rag_meta=rag_meta, nl2sql_meta=nl2sql_meta))}\n\n"

                # Phase 3: stream tokens
                for i in range(0, len(rag_answer), 2):
                    yield f"event: token\ndata: {json.dumps({'token': rag_answer[i:i+2]})}\n\n"

                if nl2sql_answer:
                    separator = "\n\n---\n**数据查询结果：**\n"
                    yield f"event: token\ndata: {json.dumps({'token': separator})}\n\n"
                    for i in range(0, len(nl2sql_answer), 2):
                        yield f"event: token\ndata: {json.dumps({'token': nl2sql_answer[i:i+2]})}\n\n"

                all_sources = rag_sources

            elif intent_result.intent == "chitchat":
                # Phase 1+2: emit thinking (chitchat has no pipeline metadata)
                yield f"event: thinking\ndata: {json.dumps(_build_thinking_event(intent_result))}\n\n"

                # Phase 3: generate and stream
                from app.core.llm import OpenAICompatibleClient
                from app.core.llm.prompt_templates import CHITCHAT_SYSTEM_PROMPT
                llm = OpenAICompatibleClient()
                rag_answer = await llm.chat([
                    {"role": "system", "content": CHITCHAT_SYSTEM_PROMPT},
                    {"role": "user", "content": sanitized},
                ])
                for i in range(0, len(rag_answer), 2):
                    yield f"event: token\ndata: {json.dumps({'token': rag_answer[i:i+2]})}\n\n"

            # Emit sources
            if all_sources:
                yield f"event: sources\ndata: {json.dumps({'sources': all_sources})}\n\n"

            # Persist messages
            if intent_result.intent == "mixed":
                full_answer = rag_answer
                if nl2sql_answer:
                    full_answer += "\n\n---\n**数据查询结果：**\n" + nl2sql_answer
            else:
                full_answer = rag_answer or nl2sql_answer
            await history_mgr.save_turn(
                session_id=current_session_id,
                user_msg=req.message,
                assistant_msg=full_answer,
                intent=intent_result.intent,
                sources=all_sources,
                session_store=session_store,
            )
            await history_mgr.maybe_compress(current_session_id, session_store)

            # Done
            elapsed = int((time.time() - start_time) * 1000)
            yield f"event: done\ndata: {json.dumps({'session_id': current_session_id, 'message_id': 1, 'intent': intent_result.intent, 'latency_ms': elapsed})}\n\n"

        except Exception as e:
            log.error(f"Stream error: {e}")
            yield f"event: error\ndata: {json.dumps({'code': 'INTERNAL_ERROR', 'detail': str(e), 'trace_id': trace_id})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _collect_rag(rag, query: str, history: list[dict]) -> tuple[str, list[dict], dict]:
    rag_meta = await rag.retrieve(query, top_k=5)
    answer = ""
    async for token in rag.stream_from_pending(query, history=history):
        answer += token
    return answer, rag.get_last_sources(), rag_meta


async def _collect_nl2sql(nl2sql, query: str, history: list[dict]) -> tuple[str, dict]:
    result = await nl2sql.query(query, history)
    return result["answer"], nl2sql.get_last_thinking()
