"""전역 설정, 경로 상수, 기본값 중앙 관리."""
import os
from pathlib import Path

# 디렉토리 경로
SRC_DIR = Path(__file__).resolve().parents[1]
AI_DIR = SRC_DIR.parent
ROOT_DIR = AI_DIR.parent

MODELS_DIR = AI_DIR / "models"
DATA_DIR = ROOT_DIR / "data"

# 데이터 파일 경로
MODELS_CSV = MODELS_DIR / "companies.csv"
DATA_CSV = DATA_DIR / "processed" / "companies.csv"

# 모델 아티팩트 경로
MODEL_RF_PATH = MODELS_DIR / "risk_rf.joblib"
MODEL_MLP_PATH = MODELS_DIR / "risk_mlp.pt"
PREPROCESSOR_MLP_PATH = MODELS_DIR / "risk_mlp_preprocessor.joblib"
METRICS_ML_PATH = MODELS_DIR / "metrics_ml.json"
METRICS_DL_PATH = MODELS_DIR / "metrics_dl.json"

# 환경변수 파일 경로
ENV_PATH = AI_DIR / ".env"

# 진단 등급 및 임계값
GRADE_NAMES = {
    "stable": "안정",
    "warning": "주의",
    "danger": "위험",
}
SCORE_THRESHOLD_WARNING = 40.0
MAX_REDUCTION_COUNT_INPUT = 10

# LLM 설정
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_TIMEOUT_MS = 15000


def get_gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def get_gemini_model() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()
