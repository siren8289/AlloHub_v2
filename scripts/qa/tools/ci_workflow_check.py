"""CI 워크플로를 도구 A/B로 교차 확인한다."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def tool_a() -> dict[str, str]:
    if not WORKFLOW.is_file():
        return {"status": "FAIL", "detail": ".github/workflows/ci.yml 없음"}
    text = WORKFLOW.read_text(encoding="utf-8")
    if "jobs:" not in text:
        return {"status": "FAIL", "detail": "jobs 키 없음"}
    if "qa:" not in text and "\n  qa:" not in text:
        return {"status": "FAIL", "detail": "qa 잡 없음"}
    return {"status": "PASS", "detail": "ci.yml 존재, jobs·qa 확인"}


def tool_b() -> dict[str, str]:
    if not WORKFLOW.is_file():
        return {"status": "FAIL", "detail": ".github/workflows/ci.yml 없음"}
    text = WORKFLOW.read_text(encoding="utf-8")
    if "python3 scripts/qa/run_qa.py" not in text and "scripts/qa/run_qa.py" not in text:
        return {"status": "FAIL", "detail": "run_qa.py 실행 단계 없음"}
    if "--with-regression" not in text:
        return {"status": "FAIL", "detail": "회귀 플래그 없음"}
    if "name: QA cross-check" not in text and "QA cross-check" not in text:
        return {"status": "FAIL", "detail": "QA cross-check 잡 이름 없음"}
    return {"status": "PASS", "detail": "qa 잡이 run_qa.py --with-regression 을 실행"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tool", choices=("a", "b"), required=True)
    args = parser.parse_args()
    payload = tool_a() if args.tool == "a" else tool_b()
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
