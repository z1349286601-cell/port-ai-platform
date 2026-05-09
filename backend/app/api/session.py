from pydantic import BaseModel
from fastapi import APIRouter, Header, HTTPException
from app.dependencies import get_session_store

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    channel: str = "web"
    user_id: str = "anonymous"
    title: str = ""


@router.get("")
async def list_sessions(
    x_demo_user: str = Header(None, alias="X-Demo-User"),
    user_id: str = "anonymous",
    limit: int = 20,
):
    uid = x_demo_user or user_id
    store = get_session_store()
    sessions = await store.list(user_id=uid, limit=limit)
    return {
        "items": [s.to_dict() for s in sessions],
        "total": len(sessions),
        "user_id": uid,
    }


@router.post("")
async def create_session(
    body: CreateSessionRequest,
    x_demo_user: str = Header(None, alias="X-Demo-User"),
):
    uid = x_demo_user or body.user_id
    store = get_session_store()
    session = await store.create(channel=body.channel, user_id=uid, title=body.title)
    return session.to_dict()


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    x_demo_user: str = Header(None, alias="X-Demo-User"),
):
    store = get_session_store()
    session = await store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = await store.get_messages(session_id, limit=50)
    return {
        "session": session.to_dict(),
        "messages": [m.to_dict() for m in messages],
    }


class UpdateSessionRequest(BaseModel):
    title: str = ""


@router.patch("/{session_id}")
async def update_session(session_id: str, body: UpdateSessionRequest):
    store = get_session_store()
    title = body.title.strip()[:20]
    if not title:
        raise HTTPException(status_code=400, detail="标题不能为空")
    ok = await store.update_title(session_id, title)
    if not ok:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"session_id": session_id, "title": title}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    store = get_session_store()
    deleted = await store.delete(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="会话不存在")
    return {"session_id": session_id, "deleted": True}
