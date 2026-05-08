from fastapi import APIRouter, Header

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("")
async def list_sessions(
    x_demo_user: str = Header(None, alias="X-Demo-User"),
    user_id: str = "anonymous",
    limit: int = 20,
):
    uid = x_demo_user or user_id
    return {"items": [], "total": 0, "user_id": uid}


@router.post("")
async def create_session():
    import uuid
    return {
        "session_id": uuid.uuid4().hex,
        "channel": "web",
        "user_id": "anonymous",
        "title": "",
        "status": "active",
        "created_at": "",
    }


@router.get("/{session_id}")
async def get_session(session_id: str):
    return {"session_id": session_id, "messages": []}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    return {"session_id": session_id, "deleted": True}
