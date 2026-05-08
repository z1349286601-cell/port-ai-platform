from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    return {"status": "ok", "filename": file.filename, "chunks": 0}


@router.get("/status")
async def knowledge_status():
    return {"collection": "port_docs", "chunk_count": 0, "doc_count": 0}


@router.post("/search")
async def search_knowledge(query: str = "", top_k: int = 5):
    return {"query": query, "results": []}
