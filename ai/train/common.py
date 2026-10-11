"""학습 스크립트가 같이 쓰는 함수."""
from pathlib import Path

import numpy as np
import pandas as pd

from ai.src.scoring.features import FEATURE_COLUMNS, TARGET_COLUMN

ROOT = Path(__file__).resolve().parents[2]
DATA_CSV = ROOT / "data" / "processed" / "companies.csv"
MODELS_DIR = Path(__file__).resolve().parent.parent / "models"


def load_companies():
    """전처리 CSV를 읽고, 모델 입력에 필요한 열만 확인한다."""
    if not DATA_CSV.exists():
        raise FileNotFoundError("data/processed/companies.csv 가 없습니다. 먼저 python -m data.etl.run 을 실행하세요.")

    frame = pd.read_csv(DATA_CSV)
    missing = [column for column in FEATURE_COLUMNS + [TARGET_COLUMN, "net_profit"] if column not in frame.columns]
    if missing:
        raise RuntimeError(f"CSV에 필요한 열이 없습니다: {missing}")

    # 학습 입력의 감자 건수는 10으로 자른다. (예측 코드와 같게)
    frame = frame.copy()
    frame["reduction_count"] = np.minimum(frame["reduction_count"].astype(int), 10)
    return frame


def copy_companies_for_server():
    """AI 서버(Docker 포함)가 회사 표를 찾을 수 있게 models/ 로 복사한다."""
    MODELS_DIR.mkdir(exist_ok=True)
    target = MODELS_DIR / "companies.csv"
    target.write_bytes(DATA_CSV.read_bytes())
    print("회사 표 복사:", target)
