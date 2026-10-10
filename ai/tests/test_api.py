"""AI 서버 테스트. 실행: cd ai && python -m pytest

GEMINI_API_KEY 를 비워서 LLM 대신 기본 설명이 나오는지 확인한다.
"""
from fastapi.testclient import TestClient

from src.main import app
from src.service import grade_of

client = TestClient(app)


def test_grade_rules():
    # 부도 공시가 있으면 모델 점수가 낮아도 '위험'
    danger = {"default_count": 1, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}
    assert grade_of(5, danger) == "danger"

    # 공시가 없고 점수가 낮으면 '안정'
    calm = {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}
    assert grade_of(10, calm) == "stable"

    # 감자만 있어도 '주의'
    reduced = {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 2}
    assert grade_of(10, reduced) == "warning"


def test_screen_samsung(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.post("/api/v1/screen", json={"company_name": "삼성전자"})
    assert response.status_code == 200
    body = response.json()
    assert body["company_name"] == "삼성전자"
    assert body["market"] == "KOSPI"
    assert 0 <= body["ml_score"] <= 100
    assert 0 <= body["dl_score"] <= 100
    assert body["grade"] in ("stable", "warning", "danger")
    assert body["explanation_source"] == "basic"
    assert "삼성전자" in body["explanation"]


def test_unknown_company():
    response = client.post("/api/v1/screen", json={"company_name": "없는회사XYZ"})
    assert response.status_code == 404


def test_empty_name():
    response = client.post("/api/v1/screen", json={"company_name": ""})
    assert response.status_code == 422
