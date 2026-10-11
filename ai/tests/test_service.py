"""Service 계층(기업 위험 진단 오케스트레이션) 단위 테스트."""
from src.service.screener import screen


def test_screen_service_pipeline():
    result = screen("삼성전자")

    assert result["company_name"] == "삼성전자"
    assert result["stock_code"] == "A005930"
    assert result["market"] == "KOSPI"
    assert "ml_score" in result
    assert "dl_score" in result
    assert "score" in result
    assert result["grade"] in ("stable", "warning", "danger")
    assert result["score"] == round((result["ml_score"] + result["dl_score"]) / 2, 1)
    assert result["explanation_source"] in ("basic", "gemini")
    assert len(result["explanation"]) > 0
    assert "삼성전자" in result["explanation"]
