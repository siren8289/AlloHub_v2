"""도구 A. pytest가 계약 함수를 실행한다. data/tests 와 겹치는 검사는 그쪽에 둔다."""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "qa" / "contract"))
sys.path.insert(0, str(ROOT / "scripts" / "qa"))

from light_import import install  # noqa: E402

install()

from fastapi import HTTPException  # noqa: E402

from report_store import verify_history_append  # noqa: E402
from src.scoring.company import find_company, normalize_name  # noqa: E402
from src.scoring.rules import grade_of  # noqa: E402


def _where(fn) -> str:
    path = Path(inspect.getsourcefile(fn) or "")
    try:
        line = inspect.getsourcelines(fn)[1]
    except OSError:
        line = "UNKNOWN"
    try:
        rel = path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        rel = str(path)
    return f"{rel}:{fn.__name__}:{line}"


def test_TC_UNIT_001_danger_on_default() -> None:
    company = {
        "default_count": 1,
        "suspend_count": 0,
        "rehab_count": 0,
        "reduction_count": 0,
    }
    assert grade_of(10, company) == "danger", _where(grade_of)


def test_TC_UNIT_002_stable_when_clean() -> None:
    company = {
        "default_count": 0,
        "suspend_count": 0,
        "rehab_count": 0,
        "reduction_count": 0,
    }
    assert grade_of(10, company) == "stable", _where(grade_of)


def test_TC_UNIT_003_warning_at_threshold() -> None:
    company = {
        "default_count": 0,
        "suspend_count": 0,
        "rehab_count": 0,
        "reduction_count": 0,
    }
    assert grade_of(40, company) == "warning", _where(grade_of)


def test_TC_UNIT_004_warning_on_reduction_only() -> None:
    company = {
        "default_count": 0,
        "suspend_count": 0,
        "rehab_count": 0,
        "reduction_count": 1,
    }
    assert grade_of(10, company) == "warning", _where(grade_of)


def test_TC_UNIT_005_normalize_strips_company_marks() -> None:
    assert normalize_name(" 주식회사 삼성전자 ") == "삼성전자"
    assert normalize_name("(주)삼성전자") == "삼성전자"
    assert normalize_name("㈜삼성전자") == "삼성전자"
    assert _where(normalize_name)


def test_TC_UNIT_006_find_samsung() -> None:
    row = find_company("삼성전자")
    assert row["item_name"] == "삼성전자", _where(find_company)
    assert row["stock_code"] == "A005930"


def test_TC_UNIT_007_missing_company_is_404() -> None:
    try:
        find_company("없는회사xyz")
    except HTTPException as exc:
        assert exc.status_code == 404, _where(find_company)
        return
    raise AssertionError("404가 아닙니다")


def test_TC_UNIT_008_empty_company_is_422() -> None:
    try:
        find_company("  ")
    except HTTPException as exc:
        assert exc.status_code == 422, _where(find_company)
        return
    raise AssertionError("422가 아닙니다")


def test_TC_UNIT_QA_001_append_preserves_history(tmp_path: Path) -> None:
    verify_history_append(tmp_path)
    assert _where(verify_history_append)
