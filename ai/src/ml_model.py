"""ML 모델: scikit-learn 랜덤포레스트로 '위험 확률'을 예측한다.

결과는 0~100 점이다. 높을수록 부도·영업정지·회생이 있었던 회사와 비슷하다는 뜻이다.
"""
from pathlib import Path

import joblib

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "risk_rf.joblib"

# 서버가 켜진 뒤 처음 한 번만 파일을 읽고, 이후에는 메모리에 있는 모델을 쓴다.
_model = None


def load_ml_model():
    global _model
    if _model is None:
        _model = joblib.load(MODEL_PATH)
    return _model


def predict_ml(input_frame):
    """입력 표(1행)를 받아 위험 점수(0~100)를 돌려준다."""
    model = load_ml_model()
    # predict_proba 의 두 번째 열이 "위험(1)" 확률이다.
    probability = model.predict_proba(input_frame)[0][1]
    return round(float(probability) * 100, 1)
