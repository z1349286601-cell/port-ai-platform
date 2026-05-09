import os
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.dependencies import get_rag_pipeline, get_vector_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")

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
    store = get_vector_store()
    count = await store.count()
    docs = await store.list_documents() if hasattr(store, 'list_documents') else []
    return {
        "collection": "port_docs",
        "chunk_count": count,
        "documents": docs,
    }


@router.delete("/documents/{doc_name:path}")
async def delete_document(doc_name: str):
    store = get_vector_store()
    if not hasattr(store, 'delete_by_doc_name'):
        raise HTTPException(status_code=501, detail="操作不支持")
    deleted = await store.delete_by_doc_name(doc_name)
    # Also try to remove the file on disk
    file_path = f"data/documents/{os.path.basename(doc_name)}"
    if os.path.exists(file_path):
        os.remove(file_path)
    return {"doc_name": doc_name, "deleted_chunks": deleted}


@router.post("/search")
async def search_knowledge(query: str = Form(""), top_k: int = Form(5)):
    rag = get_rag_pipeline()
    result = await rag.query(query, top_k=top_k)
    return result
