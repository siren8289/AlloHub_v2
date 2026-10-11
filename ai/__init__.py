"""AlloHub AI 모듈 루트 패키지."""
import sys
from pathlib import Path

# 루트에서 python -m ai.train... 실행 시 ai/ 디렉토리를 sys.path에 자동 추가
_AI_DIR = str(Path(__file__).resolve().parent)
if _AI_DIR not in sys.path:
    sys.path.insert(0, _AI_DIR)

from src.main import app
from src.service.screener import screen

__all__ = ["app", "screen"]
