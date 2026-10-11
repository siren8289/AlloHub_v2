"""AlloHub AI 소스 패키지."""
import sys
from pathlib import Path

_AI_DIR = str(Path(__file__).resolve().parent.parent)
if _AI_DIR not in sys.path:
    sys.path.insert(0, _AI_DIR)

from src.main import app
from src.service.screener import screen

__all__ = ["app", "screen"]
