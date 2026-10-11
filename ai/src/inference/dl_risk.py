"""DL 추론: PyTorch MLP 기반 위험 확률 예측."""
from typing import Any, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn

from src.core.config import MODEL_MLP_PATH, PREPROCESSOR_MLP_PATH


class RiskMLP(nn.Module):
    """위험 확률 예측 다층 퍼셉트론 (Input -> 32 -> ReLU -> Dropout(0.1) -> 16 -> ReLU -> 1)."""

    def __init__(self, input_size: int):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(input_size, 32),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.layers(x)


_model: Optional[RiskMLP] = None
_preprocessor = None


def load_dl_model(force_reload: bool = False) -> Tuple[RiskMLP, Any]:
    """PyTorch MLP 모델과 전처리기(ColumnTransformer)를 로드합니다 (지연 로딩 적용)."""
    global _model, _preprocessor
    if _model is None or _preprocessor is None or force_reload:
        if not PREPROCESSOR_MLP_PATH.exists():
            raise FileNotFoundError(f"DL 전처리기 파일이 없습니다: {PREPROCESSOR_MLP_PATH}")
        if not MODEL_MLP_PATH.exists():
            raise FileNotFoundError(f"DL 모델 가중치 파일이 없습니다: {MODEL_MLP_PATH}")

        _preprocessor = joblib.load(PREPROCESSOR_MLP_PATH)
        checkpoint = torch.load(MODEL_MLP_PATH, map_location="cpu", weights_only=True)
        _model = RiskMLP(input_size=checkpoint["input_size"])
        _model.load_state_dict(checkpoint["model_state_dict"])
        _model.eval()

    return _model, _preprocessor


def predict_dl(input_frame: pd.DataFrame) -> float:
    """입력 DataFrame(1행)을 전처리 후 MLP 모델에 주입하여 위험 점수(0~100)를 반환합니다."""
    model, preprocessor = load_dl_model()
    x = preprocessor.transform(input_frame).astype(np.float32)

    with torch.no_grad():
        logit = model(torch.from_numpy(x)).squeeze()
        probability = torch.sigmoid(logit).item()

    return round(float(probability) * 100, 1)
