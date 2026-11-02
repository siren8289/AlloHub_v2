"""compose.yaml 필수 서비스를 독립 검증한다. docker 없이 파일만 본다."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
COMPOSE = ROOT / "compose.yaml"
REQUIRED = ("back", "ai", "front", "db")


def main() -> int:
    if not COMPOSE.is_file():
        print(json.dumps({"status": "FAIL", "detail": "compose.yaml 없음"}, ensure_ascii=False))
        return 1
    text = COMPOSE.read_text(encoding="utf-8")
    missing = [name for name in REQUIRED if f"{name}:" not in text and f"{name} :" not in text]
    # services 블록 안의 키만 대략 확인: "  name:" 형태
    present = []
    for name in REQUIRED:
        if f"\n  {name}:" in text or text.startswith(f"  {name}:") or f"\n  {name} :" in text:
            present.append(name)
        elif f"\n{name}:" in text:
            # top-level 오탐 방지보다 누락 FAIL이 낫다. services 하위를 재검사한다.
            pass
    missing = [name for name in REQUIRED if name not in present]
    if "services:" not in text:
        print(json.dumps({"status": "FAIL", "detail": "services 키 없음"}, ensure_ascii=False))
        return 1
    if missing:
        print(
            json.dumps(
                {"status": "FAIL", "detail": f"필수 서비스 누락: {','.join(missing)}"},
                ensure_ascii=False,
            )
        )
        return 1
    print(
        json.dumps(
            {"status": "PASS", "detail": f"필수 서비스 확인: {','.join(REQUIRED)}"},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
