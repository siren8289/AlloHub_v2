"""DL 모델: PyTorch 다층 퍼셉트론(MLP)으로 '위험 확률'을 예측한다.

입력 전처리(원-핫 인코딩, 표준화)는 scikit-learn 으로 하고,
숫자 배열이 된 입력을 PyTorch 신경망에 넣는다.
출력은 0~1 확률이고, 점수로는 0~100 으로 바꿔 돌려준다.
"""
from pathlib import Path

import joblib
import numpy as np
import torch
from torch import nn

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODEL_PATH = MODELS_DIR / "risk_mlp.pt"
PREPROCESSOR_PATH = MODELS_DIR / "risk_mlp_preprocessor.joblib"


class RiskMLP(nn.Module):
    """입력 → 32 → 16 → 1 (위험 로짓). 학습 코드와 구조가 똑같아야 한다."""

    def __init__(self, input_size):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x):
        return self.layers(x)


_model = None
_preprocessor = None


def load_dl_model():
    global _model, _preprocessor
    if _model is None:
        _preprocessor = joblib.load(PREPROCESSOR_PATH)
        checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
        _model = RiskMLP(input_size=checkpoint["input_size"])
        _model.load_state_dict(checkpoint["model_state_dict"])
        _model.eval()  # 예측 모드 (Dropout 끄기)
    return _model, _preprocessor


def predict_dl(input_frame):
    """입력 표(1행)를 받아 위험 점수(0~100)를 돌려준다."""
    model, preprocessor = load_dl_model()
    x = preprocessor.transform(input_frame).astype(np.float32)

    with torch.no_grad():
        logit = model(torch.from_numpy(x)).squeeze()
        probability = torch.sigmoid(logit).item()  # 로짓 → 0~1 확률

    return round(float(probability) * 100, 1)
