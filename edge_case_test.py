"""
Phase 1a Edge Case Verification (15 items from plan §8.5 Day 48)
Tests boundary conditions for the chat API.
"""
import asyncio
import io
import json
import os
import sys
import time

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))

EDGE_CASES = []


def record(scenario, passed, detail=""):
    EDGE_CASES.append({"scenario": scenario, "passed": passed, "detail": str(detail)[:200]})


async def run():
    import httpx

    BASE = "http://localhost:8000/api/v1"

    async with httpx.AsyncClient(base_url=BASE, timeout=30) as client:
        # 1. 空消息
        try:
            r = await client.post("/chat/stream", json={"message": "", "channel": "web", "user_id": "edge-test"})
            record("空消息", r.status_code >= 400, f"status={r.status_code}")
        except Exception as e:
            record("空消息", False, str(e))

        # 2. 超长消息 (> 4000 字)
        try:
            long_msg = "测试" * 2001  # 4002 chars
            r = await client.post("/chat/stream", json={"message": long_msg, "channel": "web", "user_id": "edge-test"})
            # Should still work but may truncate
            record("超长消息", r.status_code in (200, 422), f"status={r.status_code}")
        except Exception as e:
            record("超长消息", False, str(e))

        # 3. 不存在会话（查询不存在的 session_id）
        try:
            r = await client.get("/sessions/nonexistent-session-12345")
            record("不存在会话", r.status_code == 404, f"status={r.status_code}")
        except Exception as e:
            record("不存在会话", False, str(e))

        # 4. 特殊字符 (SQL injection attempt)
        try:
            sql_injection = "'; DROP TABLE sessions; --"
            r = await client.post("/chat/stream", json={"message": sql_injection, "channel": "web", "user_id": "edge-test"})
            record("特殊字符-SQL注入", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            record("特殊字符-SQL注入", False, str(e))

        # 5. 特殊字符 (XSS)
        try:
            xss = "<script>alert('xss')</script>"
            r = await client.post("/chat/stream", json={"message": xss, "channel": "web", "user_id": "edge-test"})
            record("特殊字符-XSS", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            record("特殊字符-XSS", False, str(e))

        # 6. 0 结果查询（查询不存在的数据）
        try:
            r = await client.post("/chat/stream", json={
                "message": "查询箱号为XYZ-99999的集装箱位置",
                "channel": "web", "user_id": "edge-test"
            })
            record("0结果查询", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            record("0结果查询", False, str(e))

        # 7. 时间范围无匹配
        try:
            r = await client.post("/chat/stream", json={
                "message": "2020年1月1日的船舶到港情况",
                "channel": "web", "user_id": "edge-test"
            })
            record("时间范围无匹配", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            record("时间范围无匹配", False, str(e))

        # 8. 并发请求（10 并发）
        try:
            async def send_one(i):
                try:
                    async with httpx.AsyncClient(base_url=BASE, timeout=60) as c2:
                        r2 = await c2.post("/chat/stream", json={
                            "message": f"测试并发请求{i}", "channel": "web", "user_id": "edge-test-concurrent"
                        })
                        return r2.status_code
                except Exception:
                    return 0

            tasks = [send_one(i) for i in range(10)]
            statuses = await asyncio.gather(*tasks)
            successes = sum(1 for s in statuses if s == 200)
            record("并发10请求", successes >= 8, f"{successes}/10 succeeded")
        except Exception as e:
            record("并发10请求", False, str(e))

        # 9. 空 body
        try:
            r = await client.post("/chat/stream", content="", headers={"Content-Type": "application/json"})
            record("空请求体", r.status_code >= 400, f"status={r.status_code}")
        except Exception as e:
            record("空请求体", False, str(e))

        # 10. 缺少 message 字段
        try:
            r = await client.post("/chat/stream", json={"channel": "web", "user_id": "edge-test"})
            record("缺少message字段", r.status_code == 422, f"status={r.status_code}")
        except Exception as e:
            record("缺少message字段", False, str(e))

        # 11. 健康检查
        try:
            r = await client.get("/health")
            record("健康检查", r.status_code == 200, f"status={r.status_code}")
        except Exception as e:
            record("健康检查", False, str(e))

        # 12. 知识库状态
        try:
            r = await client.get("/knowledge/status")
            data = r.json()
            has_chunks = data.get("chunk_count", 0) > 0
            record("知识库有数据", has_chunks, f"chunks={data.get('chunk_count', 0)}")
        except Exception as e:
            record("知识库有数据", False, str(e))

        # 13. CORS headers
        try:
            r = await client.options("/chat/stream", headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            })
            record("CORS预检", r.status_code in (200, 204, 405), f"status={r.status_code}")
        except Exception as e:
            record("CORS预检", False, str(e))

        # 14. 无效JSON
        try:
            r = await client.post("/chat/stream", content="not json", headers={"Content-Type": "application/json"})
            record("无效JSON", r.status_code >= 400, f"status={r.status_code}")
        except Exception as e:
            record("无效JSON", False, str(e))

    # 15. SQLite 数据库文件完整性
    try:
        import sqlite3
        dbs = ["production", "equipment", "energy", "sessions"]
        base = os.path.join("data", "sqlite")
        all_ok = True
        for db in dbs:
            path = os.path.join(base, f"{db}.db")
            if not os.path.exists(path):
                all_ok = False
                break
            conn = sqlite3.connect(path)
            conn.execute("SELECT 1").fetchone()
            conn.close()
        record("SQLite文件完整性", all_ok, f"checked {len(dbs)} dbs")
    except Exception as e:
        record("SQLite文件完整性", False, str(e))

    # Print results
    print("=" * 60)
    print("Phase 1a Edge Case Verification (15 items)")
    print("=" * 60)
    passed = sum(1 for e in EDGE_CASES if e["passed"])
    total = len(EDGE_CASES)
    for i, e in enumerate(EDGE_CASES):
        status = "PASS" if e["passed"] else "FAIL"
        print(f"  {i+1:2d}. [{status}] {e['scenario']}: {e['detail']}")
    print("=" * 60)
    print(f"RESULTS: {passed}/{total} passed ({passed*100//total if total else 0}%)")


if __name__ == "__main__":
    asyncio.run(run())
