"""도구 B. pytest를 쓰지 않고 같은 계약을 다시 확인한다."""

from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "qa" / "contract"))
sys.path.insert(0, str(ROOT / "scripts" / "qa"))

from light_import import install  # noqa: E402

install()

from fastapi import HTTPException  # noqa: E402

from data.etl.fetch import as_list, shorten_row  # noqa: E402
from data.etl.transform import build_companies, count_by_crno, to_number  # noqa: E402
from report_store import verify_history_append  # noqa: E402
from src.scoring.company import find_company, normalize_name  # noqa: E402
from src.scoring.rules import grade_of  # noqa: E402


def _place(fn) -> dict[str, str]:
    source = inspect.getsourcefile(fn)
    try:
        line = str(inspect.getsourcelines(fn)[1])
    except OSError:
        line = "UNKNOWN"
    if not source:
        rel = "UNKNOWN"
    else:
        path = Path(source).resolve()
        try:
            rel = path.relative_to(ROOT).as_posix()
        except ValueError:
            rel = str(path)
    return {"file": rel, "function": getattr(fn, "__name__", "UNKNOWN"), "line": line}


def _case(tc_id: str, feature: str, fn, check) -> dict:
    place = _place(fn)
    try:
        detail = check()
        status = "PASS"
        error = ""
    except AssertionError as exc:
        status = "FAIL"
        detail = str(exc)
        error = str(exc)
    except Exception as exc:  # 도구 자체 오류는 PASS가 아니다.
        status = "ERROR"
        detail = f"{type(exc).__name__}: {exc}"
        error = detail
    return {
        "tc_id": tc_id,
        "feature": feature,
        "status": status,
        "detail": detail or status,
        "error": error,
        **place,
    }


def _clean() -> dict:
    return {
        "default_count": 0,
        "suspend_count": 0,
        "rehab_count": 0,
        "reduction_count": 0,
    }


def cases() -> list[dict]:
    found = []

    def danger() -> str:
        company = _clean()
        company["default_count"] = 1
        actual = grade_of(10, company)
        if actual != "danger":
            raise AssertionError(f"expected danger actual {actual}")
        return "default_count=1 score=10 -> danger"

    def stable() -> str:
        actual = grade_of(10, _clean())
        if actual != "stable":
            raise AssertionError(f"expected stable actual {actual}")
        return "score=10 clean -> stable"

    def warning_score() -> str:
        actual = grade_of(40, _clean())
        if actual != "warning":
            raise AssertionError(f"expected warning actual {actual}")
        return "score=40 -> warning"

    def warning_reduction() -> str:
        company = _clean()
        company["reduction_count"] = 1
        actual = grade_of(10, company)
        if actual != "warning":
            raise AssertionError(f"expected warning actual {actual}")
        return "reduction_count=1 -> warning"

    def names() -> str:
        samples = {
            " 주식회사 삼성전자 ": "삼성전자",
            "(주)삼성전자": "삼성전자",
            "㈜삼성전자": "삼성전자",
        }
        for raw, expected in samples.items():
            actual = normalize_name(raw)
            if actual != expected:
                raise AssertionError(f"{raw!r} -> {actual!r}")
        return "주식회사/(주)/㈜ and spaces stripped"

    def samsung() -> str:
        row = find_company("삼성전자")
        if row["item_name"] != "삼성전자" or row["stock_code"] != "A005930":
            raise AssertionError(f"item={row['item_name']} code={row['stock_code']}")
        return "삼성전자 stock_code=A005930"

    def missing() -> str:
        try:
            find_company("없는회사xyz")
        except HTTPException as exc:
            if exc.status_code != 404:
                raise AssertionError(f"status {exc.status_code}") from exc
            return "missing name -> 404"
        raise AssertionError("no HTTPException")

    def empty() -> str:
        try:
            find_company("  ")
        except HTTPException as exc:
            if exc.status_code != 422:
                raise AssertionError(f"status {exc.status_code}") from exc
            return "blank name -> 422"
        raise AssertionError("no HTTPException")

    def numbers() -> str:
        if to_number("1,383") != 1383:
            raise AssertionError(f"comma -> {to_number('1,383')}")
        if to_number("") is not None or to_number("-") is not None:
            raise AssertionError("empty or dash was not None")
        return "1,383 -> 1383; empty and dash -> None"

    def crno() -> str:
        rows = [
            {"crno": "1101110000001"},
            {"crno": "1101110000001"},
            {"crno": "0000000000000"},
            {"crno": ""},
        ]
        actual = count_by_crno(rows)
        if actual != {"1101110000001": 2}:
            raise AssertionError(str(actual))
        return "empty crno skipped"

    def listing() -> str:
        if as_list({"crno": "1"}) != [{"crno": "1"}] or as_list(None) != []:
            raise AssertionError("as_list mismatch")
        row = shorten_row({"crno": "1", "rptFileCtt": [1, 2, 3], "note": "a" * 500})
        if "rptFileCtt" in row or len(row["note"]) != 300:
            raise AssertionError(str(row))
        return "as_list and shorten_row"

    def joined() -> str:
        listings = [
            {
                "basDt": "20261007",
                "srtnCd": "A005930",
                "mrktCtg": "KOSPI",
                "itmsNm": "삼성전자",
                "corpNm": "삼성전자(주)",
                "crno": "1301110006246",
            },
            {
                "basDt": "20261007",
                "srtnCd": "A000660",
                "mrktCtg": "KOSPI",
                "itmsNm": "SK하이닉스",
                "corpNm": "에스케이하이닉스(주)",
                "crno": "1344110001387",
            },
            {
                "basDt": "20261007",
                "srtnCd": "A900110",
                "mrktCtg": "KOSDAQ",
                "itmsNm": "외국회사",
                "corpNm": "외국회사",
                "crno": "0000000000000",
            },
        ]
        disclosures = {
            "dividend": [
                {
                    "basDt": "20250930",
                    "crno": "1301110006246",
                    "pvtrOnskCashDvdnBnfRt": "2.5",
                    "pvtrCrtmNpf": "-10",
                    "pvtrParPrc": "100",
                }
            ],
            "default": [{"crno": "1344110001387", "basDt": "20200101"}],
            "suspend": [],
            "rehab": [{"crno": "1344110001387"}],
            "reduction": [{"crno": "1301110006246"}],
        }
        frame = build_companies(listings, disclosures)
        names = list(frame["item_name"])
        if names != ["삼성전자", "SK하이닉스"]:
            raise AssertionError(str(names))
        samsung_row = frame.iloc[0]
        if int(samsung_row["distress"]) != 0 or int(samsung_row["reduction_count"]) != 1:
            raise AssertionError("samsung label mismatch")
        hynix = frame.iloc[1]
        if int(hynix["distress"]) != 1 or int(hynix["default_count"]) != 1:
            raise AssertionError("hynix label mismatch")
        return "build_companies joins disclosures"

    def history() -> str:
        with tempfile.TemporaryDirectory() as tmp:
            verify_history_append(Path(tmp))
        return "two appends keep the first RUN_ID"

    specs = [
        ("TC-UNIT-001", "위험등급", grade_of, danger),
        ("TC-UNIT-002", "위험등급", grade_of, stable),
        ("TC-UNIT-003", "위험등급", grade_of, warning_score),
        ("TC-UNIT-004", "위험등급", grade_of, warning_reduction),
        ("TC-UNIT-005", "기업명정규화", normalize_name, names),
        ("TC-UNIT-006", "기업검색", find_company, samsung),
        ("TC-UNIT-007", "기업검색", find_company, missing),
        ("TC-UNIT-008", "기업검색", find_company, empty),
        ("TC-UNIT-009", "숫자변환", to_number, numbers),
        ("TC-UNIT-010", "공시건수", count_by_crno, crno),
        ("TC-UNIT-011", "수집행정리", as_list, listing),
        ("TC-UNIT-012", "회사표결합", build_companies, joined),
        ("TC-UNIT-QA-001", "QA기록", verify_history_append, history),
    ]
    for tc_id, feature, fn, check in specs:
        found.append(_case(tc_id, feature, fn, check))
    return found


def main() -> int:
    payload = cases()
    json.dump(payload, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
