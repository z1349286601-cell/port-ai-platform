"""
Batch test all 10 Phase 1a scenarios via SSE API.
Prints intent, latency, and answer preview for each.
"""
import asyncio, io, json, os, sys, time, urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
BASE = "http://localhost:8000/api/v1"

SCENARIOS = [
    ("SAFE-001", "进入码头作业区需要什么防护装备？", "document_qa"),
    ("SAFE-002", "危险品泄漏的应急处理流程是什么？", "document_qa"),
    ("PROD-001", "今晚有哪些船舶到港？", "data_query"),
    ("PROD-002", "在场超过7天的进口重箱有哪些？", "data_query"),
    ("PROD-003", "未来3天泊位占用情况？", "data_query"),
    ("PROD-004", "堆场现在还剩多少空位？", "data_query"),
    ("PROD-005", "1号泊位BC-102船的工班进度怎么样？", "data_query"),
    ("PROD-015", "今天闸口通行了多少车？", "data_query"),
    ("EQUIP-001", "1号岸桥目前状态怎么样？", "data_query"),
    ("ENERGY-001", "这个月港口总用电量是多少？", "data_query"),
]

def test_one(scenario_id, question, expected_intent):
    """Run one SSE query and return results."""
    start = time.time()
    result = {"id": scenario_id, "question": question[:40], "expected_intent": expected_intent}

    try:
        body = json.dumps({"message": question, "channel": "web", "user_id": "batch-test"}).encode()
        req = urllib.request.Request(f"{BASE}/chat/stream", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=180) as resp:
            result["status"] = resp.status
            raw = b""
            answer = ""

            # Buffer and parse SSE
            buffer = b""
            while True:
                chunk = resp.read(4096)
                if not chunk:
                    break
                buffer += chunk
                while b"\n\n" in buffer:
                    event_raw, buffer = buffer.split(b"\n\n", 1)
                    lines = event_raw.decode("utf-8", errors="replace").split("\n")
                    event_type = ""
                    for line in lines:
                        if line.startswith("event: "):
                            event_type = line[7:]
                        elif line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                if event_type == "intent":
                                    result["intent"] = data.get("intent", "")
                                    result["confidence"] = data.get("confidence", 0)
                                elif event_type == "token":
                                    answer += data.get("token", "")
                                elif event_type == "sources":
                                    result["source_count"] = len(data.get("sources", []))
                                elif event_type == "done":
                                    result["latency_ms"] = data.get("latency_ms", 0)
                                elif event_type == "error":
                                    result["error"] = data.get("detail", "")
                            except json.JSONDecodeError:
                                pass

            result["answer_preview"] = answer[:120].replace("\n", " ")
            result["answer_length"] = len(answer)

    except urllib.error.HTTPError as e:
        result["status"] = e.code
        result["error"] = str(e)
    except Exception as e:
        result["status"] = -1
        result["error"] = str(e)[:100]

    result["wall_time"] = round(time.time() - start, 1)
    return result


def main():
    print("=" * 70)
    print("Phase 1a — 10 Scenario Integration Test")
    print("=" * 70)

    passed = 0
    failed = 0
    total_time = 0

    for sid, question, expected_intent in SCENARIOS:
        print(f"\n[{sid}] {question[:50]}...")
        result = test_one(sid, question, expected_intent)

        intent_match = result.get("intent") == expected_intent
        has_answer = result.get("answer_length", 0) > 5
        no_error = "error" not in result

        ok = intent_match and has_answer and no_error
        if ok:
            passed += 1
            status = "PASS"
        else:
            failed += 1
            status = "FAIL"

        print(f"  {status} | intent={result.get('intent','?')} (expected={expected_intent}) "
              f"| latency={result.get('latency_ms','?')}ms "
              f"| answer_len={result.get('answer_length',0)} "
              f"| sources={result.get('source_count','-')}")

        preview = result.get("answer_preview", "")
        if preview:
            print(f"  → {preview}")
        if "error" in result:
            print(f"  ✗ ERROR: {result['error']}")

        total_time += result.get("wall_time", 0)

    print(f"\n{'=' * 70}")
    print(f"RESULTS: {passed}/{passed + failed} passed | Total time: {total_time:.0f}s")
    if failed > 0:
        print(f"{failed} scenarios FAILED — review above")
    print("=" * 70)

if __name__ == "__main__":
    main()
