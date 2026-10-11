"""Inference 계층(ML 및 DL 모델 추론) 단위 테스트."""
import pandas as pd
import torch

from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
from src.inference.ml_risk import load_ml_model, predict_ml
from src.scoring.company import find_company
from src.scoring.features import make_input_frame


def test_ml_inference():
    model = load_ml_model()
    assert model is not None

    company = find_company("삼성전자")
    features = make_input_frame(company)
    score = predict_ml(features)

    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0


def test_dl_inference():
    model, preprocessor = load_dl_model()
    assert model is not None
    assert preprocessor is not None

    company = find_company("삼성전자")
    features = make_input_frame(company)
    score = predict_dl(features)

    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0


def test_risk_mlp_architecture():
    mlp = RiskMLP(input_size=10)
    dummy_input = torch.randn(4, 10)
    output = mlp(dummy_input)
    assert output.shape == (4, 1)
