from fastapi import APIRouter, UploadFile, File, HTTPException
from app.dependencies import get_rag_pipeline

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

    import os
    os.makedirs("data/documents", exist_ok=True)

    content = await file.read()
    file_path = f"data/documents/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(content)

    rag = get_rag_pipeline()
    chunk_count = await rag.ingest_file(file_path)

    return {"status": "ok", "filename": file.filename, "chunks": chunk_count}


@router.get("/status")
async def knowledge_status():
    from app.dependencies import get_vector_store
    store = get_vector_store()
    count = await store.count()
    return {"collection": "port_docs", "chunk_count": count}


@router.post("/search")
async def search_knowledge(query: str = "", top_k: int = 5):
    rag = get_rag_pipeline()
    result = await rag.query(query, top_k=top_k)
    return result
