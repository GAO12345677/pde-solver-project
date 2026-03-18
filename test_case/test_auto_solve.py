"""Tests for /api/parse_question and /api/auto_solve.

This test suite is designed to be runnable without real Baidu credentials by using:
  BAIDU_QIANFAN_MOCK=1

It covers three scenarios:
1) Key not configured -> rule-based fallback
2) Key configured but invalid -> API call error -> fallback
3) Key configured (mock) -> treated as "baidu_llm" mode (mocked)

Run:
  python -m test_case.test_auto_solve
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, List

from fastapi.testclient import TestClient

import main


def _post(client: TestClient, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    r = client.post(path, json=payload)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "success" in body, body
    return body


def _run_case(client: TestClient, question: str) -> Dict[str, Any]:
    start = time.perf_counter()
    parsed = _post(client, "/api/parse_question", {"question": question})
    solved = _post(client, "/api/auto_solve", {"question": question})
    elapsed = time.perf_counter() - start
    return {"question": question, "parse": parsed, "auto_solve": solved, "elapsed_s": elapsed}


def test_auto_solve_full() -> Dict[str, Any]:
    client = TestClient(main.app)

    cases: List[Dict[str, Any]] = []

    # Case 1: no key -> fallback
    os.environ.pop("BAIDU_QIANFAN_API_KEY", None)
    os.environ.pop("BAIDU_QIANFAN_SECRET_KEY", None)
    os.environ["BAIDU_QIANFAN_MOCK"] = "0"  # force real path (but no key) -> fallback
    cases.append(
        _run_case(client, "我要算一个一维的线性定常热传导方程，精度要求90%，别太耗资源")
    )

    # Case 2: key configured but invalid -> mock + bad key -> fallback
    os.environ["BAIDU_QIANFAN_MOCK"] = "1"
    os.environ["BAIDU_QIANFAN_API_KEY"] = "bad"
    os.environ["BAIDU_QIANFAN_SECRET_KEY"] = "bad"
    cases.append(
        _run_case(client, "求解2维非线性非定常泊松方程，要算得快一点，精度不用太高")
    )

    # Case 3: key configured (mock ok) -> baidu_llm mode (mocked)
    os.environ["BAIDU_QIANFAN_MOCK"] = "1"
    os.environ["BAIDU_QIANFAN_API_KEY"] = "ok"
    os.environ["BAIDU_QIANFAN_SECRET_KEY"] = "ok"
    cases.append(
        _run_case(client, "我要算一个一维的线性定常热传导方程，精度要求90%，别太耗资源")
    )

    # Build report
    report = {
        "timestamp": time.time(),
        "cases": [],
        "notes": [
            "本测试默认使用 MOCK 模式模拟 ERNIE-Speed-8K 输出，以保证无需真实 Key 也可运行。",
            "如需真实调用，请设置 BAIDU_QIANFAN_API_KEY / BAIDU_QIANFAN_SECRET_KEY 并关闭 BAIDU_QIANFAN_MOCK。",
        ],
    }

    for c in cases:
        parse_body = c["parse"]
        auto_body = c["auto_solve"]
        report["cases"].append(
            {
                "question": c["question"],
                "elapsed_s": c["elapsed_s"],
                "parse_success": bool(parse_body.get("success")),
                "auto_solve_success": bool(auto_body.get("success")),
                "parser_message": (parse_body.get("data") or {}).get("message"),
                "selected_algorithm": ((auto_body.get("data") or {}).get("selected") or {}).get("algorithm_key"),
                "total_score": (((auto_body.get("data") or {}).get("evaluated") or {}).get("report") or {}).get("metrics", {}).get("total"),
            }
        )

        # Print step outputs for visibility
        print("\n=== QUESTION ===\n", c["question"])
        print("\n--- PARSED JSON ---\n", json.dumps(parse_body.get("data", {}), ensure_ascii=False, indent=2))
        print("\n--- AUTO SOLVE ---\n", json.dumps(auto_body.get("data", {}), ensure_ascii=False, indent=2)[:2000], "\n... (truncated)")

    os.makedirs("result", exist_ok=True)
    path = os.path.join("result", f"test_auto_solve_report_{int(report['timestamp'])}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print("\n[test_auto_solve] report saved to:", path)
    return report


if __name__ == "__main__":
    test_auto_solve_full()

