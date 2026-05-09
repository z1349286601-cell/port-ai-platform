"""
Fast integration checks — no LLM calls. Tests data layer, APIs, and non-LLM components.
"""
import json, os, sqlite3, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT, "backend"))

import urllib.request
import urllib.error

BASE = "http://localhost:8000/api/v1"
PASS, FAIL = 0, 0

def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  [PASS] {name} {detail}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name} {detail}")

def api_get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def api_post(path, body=None):
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

def api_delete(path):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read()), e.code

# ── 1. SQLite data ──
print("\n=== 1. SQLite Data ===")
DATA = os.path.join(PROJECT, "data", "sqlite")
for db, min_tables in [("production", 8), ("equipment", 3), ("energy", 2), ("sessions", 2)]:
    path = os.path.join(DATA, f"{db}.db")
    if not os.path.exists(path):
        check(f"{db}.db", False, "NOT FOUND")
        continue
    conn = sqlite3.connect(path)
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    conn.close()
    check(f"{db}.db", len(tables) >= min_tables, f"{len(tables)} tables")

# ── 2. ChromaDB ──
print("\n=== 2. ChromaDB ===")
try:
    from app.core.vector_store.chroma_store import ChromaVectorStore
    from app.core.config import settings

    async def chroma_test():
        store = ChromaVectorStore()
        await store.initialize()
        count = await store.count()
        check("chunk_count", count > 0, f"{count} chunks")
        results = await store.similarity_search("safety equipment", top_k=3)
        check("similarity_search", len(results) > 0, f"retrieved {len(results)} chunks")
        if results:
            excerpt = results[0].get('excerpt', '') or results[0].get('content', '') or str(results[0])
            print(f"         top excerpt: {excerpt[:100]}")

    import asyncio
    asyncio.run(chroma_test())
except Exception as e:
    check("ChromaDB", False, str(e)[:100])

# ── 3. NL2SQL Schema ──
print("\n=== 3. NL2SQL Schema ===")
try:
    from app.nl2sql.schema_extractor import SchemaExtractor

    async def schema_test():
        extractor = SchemaExtractor()
        # Extract schema from each domain DB
        domains = {}
        for domain in ["production", "equipment", "energy"]:
            db_path = os.path.join(DATA, f"{domain}.db")
            if os.path.exists(db_path):
                desc = await extractor.extract(db_path, domain)
                domains[domain] = desc
        table_count = sum(len(d.tables) for d in domains.values())
        has_device = any("device" in t.name.lower() for d in domains.values() for t in d.tables)
        check("domains >= 3", len(domains) >= 3, f"domains={list(domains.keys())}")
        check("tables > 5", table_count > 5, f"{table_count} tables total")
        check("EQUIP-001 path", has_device, "device tables exist")

    asyncio.run(schema_test())
except Exception as e:
    check("SchemaExtractor", False, str(e)[:100])

# ── 4. SQL Validator ──
print("\n=== 4. SQL Validator ===")
try:
    from app.nl2sql.sql_validator import SQLValidator
    validator = SQLValidator()
    tests = [
        ("SELECT * FROM fact_vessel_schedule", True),
        ("DROP TABLE sessions", False),
        ("DELETE FROM fact_container", False),
        ("INSERT INTO dim_berth VALUES (1,'test')", False),
        ("SELECT vsl_name, eta FROM dim_vessel", True),
    ]
    for sql, should_pass in tests:
        result = validator.validate(sql)
        check(f"{sql[:55]}...", result.is_valid == should_pass, f"valid={result.is_valid} (expected={should_pass})")
except Exception as e:
    check("SQLValidator", False, str(e)[:100])

# ── 5. Session CRUD API ──
print("\n=== 5. Session CRUD ===")
try:
    data, status = api_post("/sessions", {"channel": "web", "user_id": "tester", "title": "fast-check"})
    check("POST create", status == 200, f"sid={data.get('session_id','?')[:16]}")
    sid = data["session_id"]

    data, status = api_get("/sessions?user_id=tester")
    check(f"GET list", status == 200, f"items={len(data.get('items',[]))}")

    data, status = api_get(f"/sessions/{sid}")
    check("GET detail", status == 200, f"messages={len(data.get('messages',[]))}")

    data, status = api_delete(f"/sessions/{sid}")
    check("DELETE", status == 200, str(data))

    data, status = api_get(f"/sessions/{sid}")
    check("verify 404", status == 404)
except Exception as e:
    check("Session CRUD", False, str(e)[:100])

# ── 6. Knowledge API ──
print("\n=== 6. Knowledge API ===")
try:
    data, status = api_get("/knowledge/status")
    check("GET /knowledge/status", status == 200, f"collection={data.get('collection')}, chunks={data.get('chunk_count')}")
except Exception as e:
    check("Knowledge API", False, str(e)[:100])

# ── 7. Health ──
print("\n=== 7. Health ===")
try:
    data, status = api_get("/health")
    check("service", data.get("status") == "ok")
    for comp in ["database", "llm", "vector_store"]:
        check(f"  {comp}", data.get("checks", {}).get(comp) == "ok", data.get("checks", {}).get(comp, "?"))
except Exception as e:
    check("Health", False, str(e)[:100])

# ── 8. RAG pipeline (load check, no LLM) ──
print("\n=== 8. RAG Pipeline (load check) ===")
try:
    from app.rag.retriever import Retriever
    check("Retriever imports", True, "ok")
    from app.rag.chunker import MarkdownChunker
    check("Chunker imports", True, "ok")
    from app.rag.document_loader import DocumentLoader
    check("DocumentLoader imports", True, "ok")
    from app.rag.generator import Generator
    check("Generator imports", True, "ok")
    from app.rag.pipeline import RAGPipeline
    check("RAGPipeline imports", True, "ok")
except Exception as e:
    check("RAG imports", False, str(e)[:100])

# ── Summary ──
print(f"\n{'='*55}")
total = PASS + FAIL
pct = PASS * 100 // total if total > 0 else 0
print(f"RESULTS: {PASS}/{total} passed ({pct}%)")
if FAIL == 0:
    print("ALL CHECKS PASSED")
else:
    print(f"{FAIL} checks FAILED")
print(f"{'='*55}")
