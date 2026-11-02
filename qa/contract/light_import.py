"""점수·검색 모듈만 불러온다. ai/src/__init__.py 는 torch를 당기므로 실행하지 않는다."""

from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def install() -> None:
    if "src.main" in sys.modules or "src.service.screener" in sys.modules:
        raise RuntimeError("FastAPI 앱이 이미 로드되어 가벼운 임포트를 중단합니다.")
    ai_src = ROOT / "ai" / "src"
    if "src" not in sys.modules:
        package = types.ModuleType("src")
        package.__path__ = [str(ai_src)]
        package.__package__ = "src"
        sys.modules["src"] = package
    for entry in (str(ROOT / "ai"), str(ROOT)):
        if entry not in sys.path:
            sys.path.insert(0, entry)
