"""pytest 설정: ai 디렉토리를 sys.path에 추가하여 어디서 실행해도 src import가 가능하도록 지원."""
import sys
from pathlib import Path

AI_DIR = str(Path(__file__).resolve().parent)
if AI_DIR not in sys.path:
    sys.path.insert(0, AI_DIR)
