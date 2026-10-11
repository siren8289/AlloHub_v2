"""ML 추론: scikit-learn RandomForest 기반 위험 확률 예측."""
from typing import Optional

import joblib
import pandas as pd

from src.core.config import MODEL_RF_PATH

_model = None


def load_ml_model(force_reload: bool = False):
    """RandomForest 파이프라인 모델을 로드합니다 (지연 로딩 및 캐싱 적용)."""
    global _model
    if _model is None or force_reload:
        if not MODEL_RF_PATH.exists():
            raise FileNotFoundError(f"ML 모델 파일이 없습니다: {MODEL_RF_PATH}")
        _model = joblib.load(MODEL_RF_PATH)
    return _model


def predict_ml(input_frame: pd.DataFrame) -> float:
    """입력 DataFrame(1행)을 받아 위험 점수(0~100)를 반환합니다."""
    model = load_ml_model()
    # predict_proba의 인덱스 1이 위험(1) 클래스 확률
    probability = model.predict_proba(input_frame)[0][1]
    return round(float(probability) * 100, 1)
