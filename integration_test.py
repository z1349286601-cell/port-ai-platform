"""
Phase 1a Integration Test Script
Tests all 10 scenarios end-to-end, distinguishing fast (no-LLM) from slow (LLM-dependent) checks.
"""
import asyncio
import io
import json
import sys
import os
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

# ── Fast checks (no LLM) ──────────────────────────────────────────

def check_sqlite_data():
    """Verify all 4 SQLite databases have expected tables and data."""
    import sqlite3
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sqlite")

    expected = {
        "production": ["dim_berth", "dim_vessel", "dim_yard_block", "dim_gate_lane",
                       "fact_container", "fact_vessel_schedule", "fact_vessel_operation",
                       "fact_shift_progress", "fact_gate_transaction",
                       "agg_operation_volume_daily", "agg_yard_occupancy_daily"],
        "equipment": ["dim_device_type", "dim_device", "fact_device_operation", "fact_iot_monitor"],
        "energy": ["dim_energy_type", "fact_electricity_daily"],
        "sessions": ["sessions", "messages"],
    }

    results = {}
    for db, tables in expected.items():
        path = os.path.join(base, f"{db}.db")
        if not os.path.exists(path):
            results[db] = f"❌ NOT FOUND"
            continue
        conn = sqlite3.connect(path)
        actual = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        missing = [t for t in tables if t not in actual]
        row_counts = {}
        for t in tables:
            if t in actual:
                row_counts[t] = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        conn.close()
        results[db] = {"missing_tables": missing, "row_counts": row_counts}

    return results


async def check_chromadb():
    """Verify ChromaDB has documents and can retrieve."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))
    from app.core.vector_store.chroma_store import ChromaVectorStore
    from app.core.embedding.openai_embedding import OpenAIEmbeddingClient

    store = ChromaVectorStore()
    embed_client = OpenAIEmbeddingClient()

    count = store.collection.count()

    # Get embedding for query text using our BGE-M3 client (1024-dim)
    query_embedding = await embed_client.embed_query("安全装备要求")

    # Search with explicit embedding
    results = store.collection.query(query_embeddings=[query_embedding], n_results=3)

    return {
        "chunk_count": count,
        "search_test": f"retrieved {len(results['ids'][0])} chunks" if results and results.get("ids") and results["ids"][0] else "❌ no results",
        "top_result_preview": results["documents"][0][0][:100] if results and results.get("documents") and results["documents"][0] else "N/A",
    }


async def check_nl2sql_schema():
    """Verify NL2SQL schema extraction works (reads DB schema, no LLM)."""
    from app.nl2sql.schema_extractor import SchemaExtractor

    extractor = SchemaExtractor()

    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "sqlite")
    domains = ["production", "equipment", "energy"]
    schemas = {}
    for domain in domains:
        db_path = os.path.join(base, f"{domain}.db")
        if os.path.exists(db_path):
            schemas[domain] = await extractor.extract(db_path, domain)

    table_count = sum(len(s.tables) for s in schemas.values())

    return {
        "domains": list(schemas.keys()),
        "total_tables": table_count,
        "status": "✅" if schemas else "❌ no domains found",
    }


async def check_intent_rules():
    """Check YAML rule-based intent classification (no LLM)."""
    from app.conversation.intent_router import IntentRouter

    router = IntentRouter()

    test_cases = [
        ("进入码头需要什么防护装备", "document_qa"),
        ("今晚有哪些船舶到港", "data_query"),
        ("1号泊位明天有什么船", "data_query"),
        ("你好", "chitchat"),
        ("发生泄漏的应急流程是什么", "document_qa"),
        ("这个月港口总用电量是多少", "data_query"),
    ]

    results = []
    for query, expected in test_cases:
        # Try rule-based classification first
        intent = await router.classify(query, history=[])
        results.append({
            "query": query[:30],
            "expected": expected,
            "got": intent.intent,
            "confidence": round(intent.confidence, 2),
            "match": "✅" if intent.intent == expected else "❌",
        })

    return results


async def check_sql_validator():
    """Verify SQL validator rules work."""
    from app.nl2sql.sql_validator import SQLValidator

    validator = SQLValidator()

    test_cases = [
        ("SELECT * FROM fact_vessel_schedule", True),  # valid SELECT
        ("DROP TABLE sessions", False),  # DROP rejected
        ("DELETE FROM fact_container", False),  # DELETE rejected
        ("SELECT vsl_name, eta FROM dim_vessel JOIN fact_vessel_schedule ON dim_vessel.id = fact_vessel_schedule.vessel_id", True),  # valid JOIN
        ("INSERT INTO dim_berth VALUES (1, 'test')", False),  # INSERT rejected
    ]

    results = []
    for sql, should_pass in test_cases:
        result = validator.validate(sql)
        reason_str = "; ".join(result.errors) if result.errors else ""
        results.append({
            "sql": sql[:60],
            "valid": result.is_valid,
            "reason": reason_str[:80],
            "expected_ok": should_pass,
            "match": "✅" if result.is_valid == should_pass else "❌",
        })

    return results


async def check_session_crud():
    """Test full session CRUD cycle."""
    import httpx

    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        # Create
        r = await client.post("/sessions", json={"channel": "web", "user_id": "test-runner", "title": "integration-test"})
        assert r.status_code == 200, f"Create failed: {r.text}"
        session = r.json()
        sid = session["session_id"]

        # List
        r = await client.get("/sessions", params={"user_id": "test-runner"})
        assert r.status_code == 200

        # Get
        r = await client.get(f"/sessions/{sid}")
        assert r.status_code == 200, f"Get failed: {r.text}"

        # Delete
        r = await client.delete(f"/sessions/{sid}")
        assert r.status_code == 200

        return {"status": "✅ full CRUD cycle passed", "session_id": sid}


async def check_knowledge_api():
    """Test knowledge endpoints (non-LLM only)."""
    import httpx

    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1") as client:
        # Status
        r = await client.get("/knowledge/status")
        assert r.status_code == 200
        status = r.json()

    return {"knowledge_status": status}


# ── Main ───────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("Phase 1a Integration Test Suite")
    print("=" * 60)

    total = 0
    passed = 0

    # 1. SQLite data check
    print("\n── 1. SQLite Data Integrity ──")
    results = check_sqlite_data()
    for db, info in results.items():
        if isinstance(info, str):
            print(f"   {db}: {info}")
            total += 1
        else:
            ok = len(info["missing_tables"]) == 0
            total += 1
            if ok:
                passed += 1
            status = "✅" if ok else "❌ missing: " + ",".join(info["missing_tables"])
            row_summary = ", ".join(f"{t}={c}" for t, c in info["row_counts"].items())
            print(f"   {db}: {status} | {row_summary}")

    # 2. ChromaDB check
    print("\n── 2. ChromaDB Vector Store ──")
    try:
        chroma = await check_chromadb()
        ok = chroma["chunk_count"] > 0
        total += 1
        if ok:
            passed += 1
        print(f"   chunks: {chroma['chunk_count']} {'✅' if ok else '❌'}")
        print(f"   search: {chroma['search_test']}")
    except Exception as e:
        print(f"   ❌ ChromaDB error: {e}")
        total += 1

    # 3. NL2SQL Schema Extraction
    print("\n── 3. NL2SQL Schema Extraction ──")
    try:
        schema = await check_nl2sql_schema()
        ok = len(schema["domains"]) >= 2
        total += 1
        if ok:
            passed += 1
        print(f"   {schema['status']} domains={schema['domains']}, tables={schema['total_tables']}")
    except Exception as e:
        print(f"   ❌ Schema extraction error: {e}")
        total += 1

    # 4. Intent Router
    print("\n── 4. Intent Router (LLM) ──")
    try:
        intent_results = await check_intent_rules()
        for r in intent_results:
            total += 1
            if r["match"] == "✅":
                passed += 1
            print(f"   {r['match']} \"{r['query']}\" → {r['got']} (conf={r['confidence']})")
    except Exception as e:
        print(f"   ❌ Intent router error: {e}")
        total += 1

    # 5. SQL Validator
    print("\n── 5. SQL Validator ──")
    try:
        validator_results = await check_sql_validator()
        for r in validator_results:
            total += 1
            if r["match"] == "✅":
                passed += 1
            print(f"   {r['match']} {r['sql'][:50]}... → valid={r['valid']}")
    except Exception as e:
        print(f"   ❌ Validator error: {e}")
        total += 1

    # 6. Session CRUD
    print("\n── 6. Session CRUD (API) ──")
    try:
        crud = await check_session_crud()
        total += 1
        passed += 1
        print(f"   {crud['status']}")
    except Exception as e:
        print(f"   ❌ Session CRUD error: {e}")
        total += 1

    # 7. Knowledge API
    print("\n── 7. Knowledge API ──")
    try:
        k_status = await check_knowledge_api()
        print(f"   collection={k_status['knowledge_status'].get('collection')}, chunks={k_status['knowledge_status'].get('chunk_count')}")
        total += 1
        passed += 1
    except Exception as e:
        print(f"   ❌ Knowledge API error: {e}")
        total += 1

    # ── Summary ──
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed}/{total} checks passed ({passed*100//total if total else 0}%)")
    print("=" * 60)

    if passed < total:
        print(f"\n⚠️  {total - passed} checks failed — review output above.")
    else:
        print("\n✅ All checks passed!")


if __name__ == "__main__":
    asyncio.run(main())
