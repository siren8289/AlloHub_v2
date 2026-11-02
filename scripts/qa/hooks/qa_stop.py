"""Stop 훅. 소스 지문이 마지막 QA 실행과 다를 때만 종료를 막는다.

세션 종료(reason이 end_turn이 아님)에서는 아무 것도 출력하지 않는다.
과거 HIGH를 이유로 반복 차단하지 않는다. HIGH 차단은 CI가 담당한다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "qa"))

from fingerprint import source_fingerprint  # noqa: E402


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}
    if event.get("reason") != "end_turn":
        return 0
    latest_path = ROOT / "scripts" / "qa" / "latest.json"
    current = source_fingerprint(ROOT)
    stored = ""
    if latest_path.is_file():
        try:
            stored = str(json.loads(latest_path.read_text(encoding="utf-8")).get("source_fingerprint", ""))
        except json.JSONDecodeError:
            stored = ""
    if stored and stored == current:
        return 0
    reason = (
        "소스 지문이 마지막 QA 실행과 다릅니다. "
        "qa-policy.md에 따라 python3 scripts/qa/run_qa.py 를 실행하고, "
        "FAIL과 미해결 HIGH/CRITICAL을 보고하기 전에는 작업을 마치지 마세요."
    )
    if not stored:
        reason = "QA 실행 기록이 없습니다. python3 scripts/qa/run_qa.py 를 실행하세요. " + reason
    sys.stdout.write(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
