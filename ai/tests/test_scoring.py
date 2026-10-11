"""Scoring 계층(피처 엔지니어링, 등급 규칙, 종목 검색) 단위 테스트."""
import pytest
from fastapi import HTTPException

from src.scoring.company import find_company, normalize_name
from src.scoring.features import (
    CATEGORY_COLUMNS,
    FEATURE_COLUMNS,
    NUMBER_COLUMNS,
    TARGET_COLUMN,
    make_input_frame,
)
from src.scoring.rules import grade_of


def test_feature_columns_definition():
    assert "market" in CATEGORY_COLUMNS
    assert "has_dividend" in NUMBER_COLUMNS
    assert "dividend_rate" in NUMBER_COLUMNS
    assert "profit_negative" in NUMBER_COLUMNS
    assert "log_profit" in NUMBER_COLUMNS
    assert "par_price" in NUMBER_COLUMNS
    assert "reduction_count" in NUMBER_COLUMNS
    assert TARGET_COLUMN == "distress"
    assert len(FEATURE_COLUMNS) == 7


def test_make_input_frame_reduction_cap():
    row = {
        "market": "KOSPI",
        "has_dividend": 1,
        "dividend_rate": 3.5,
        "profit_negative": 0,
        "log_profit": 15.2,
        "par_price": 500,
        "reduction_count": 25,  # 10보다 큰 경우
    }
    df = make_input_frame(row)
    assert df.shape == (1, 7)
    assert df["reduction_count"].iloc[0] == 10  # max 10으로 클리핑되어야 함


def test_grade_rules_comprehensive():
    # 1. 부도/영업정지/회생 공시가 1건이라도 있으면 점수 무관하게 danger
    assert grade_of(0.0, {"default_count": 1, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}) == "danger"
    assert grade_of(10.0, {"default_count": 0, "suspend_count": 1, "rehab_count": 0, "reduction_count": 0}) == "danger"
    assert grade_of(20.0, {"default_count": 0, "suspend_count": 0, "rehab_count": 1, "reduction_count": 0}) == "danger"

    # 2. 감자 공시가 있거나 점수가 40 이상이면 warning
    assert grade_of(15.0, {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 1}) == "warning"
    assert grade_of(40.0, {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}) == "warning"
    assert grade_of(75.5, {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}) == "warning"

    # 3. 점수가 40 미만이고 모든 부정 공시가 0건이면 stable
    assert grade_of(39.9, {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}) == "stable"
    assert grade_of(5.0, {"default_count": 0, "suspend_count": 0, "rehab_count": 0, "reduction_count": 0}) == "stable"


def test_normalize_name():
    assert normalize_name("삼성전자 주식회사") == "삼성전자"
    assert normalize_name("(주)카카오") == "카카오"
    assert normalize_name(" ㈜ 네이버 ") == "네이버"


def test_find_company_search():
    samsung = find_company("삼성전자")
    assert samsung["stock_code"] == "A005930"
    assert samsung["market"] == "KOSPI"

    with pytest.raises(HTTPException) as exc:
        find_company("존재하지않는회사12345")
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as exc_empty:
        find_company("")
    assert exc_empty.value.status_code == 422
