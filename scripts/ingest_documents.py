"""Batch ingest all documents from data/documents/ into ChromaDB."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.dependencies import get_rag_pipeline


async def main():
    pipeline = get_rag_pipeline()
    docs_dir = Path(__file__).parent.parent / "data" / "documents"

    if not docs_dir.exists():
        print(f"Documents directory not found: {docs_dir}")
        return

    md_files = sorted(docs_dir.glob("*.md"))
    if not md_files:
        print("No .md files found in documents directory.")
        return

    total_chunks = 0
    for f in md_files:
        chunks = await pipeline.ingest_file(str(f))
        print(f"  {f.name}: {chunks} chunks")
        total_chunks += chunks

    print(f"\nTotal: {len(md_files)} documents, {total_chunks} chunks indexed to ChromaDB")


if __name__ == "__main__":
    asyncio.run(main())
