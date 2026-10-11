"""전처리 함수 테스트. 실행: python -m pytest data/tests"""
from data.etl.fetch import as_list, shorten_row
from data.etl.transform import build_companies, count_by_crno, to_number


def test_to_number():
    assert to_number("1,383") == 1383
    assert to_number("") is None
    assert to_number("-") is None


def test_as_list_and_shorten():
    assert as_list({"crno": "1"}) == [{"crno": "1"}]
    assert as_list(None) == []
    # 첨부파일(리스트, 아주 긴 글)은 버린다.
    row = shorten_row({"crno": "1", "rptFileCtt": [1, 2, 3], "note": "a" * 500})
    assert "rptFileCtt" not in row
    assert len(row["note"]) == 300


def test_count_by_crno_skips_empty_number():
    rows = [
        {"crno": "1101110000001"},
        {"crno": "1101110000001"},
        {"crno": "0000000000000"},
        {"crno": ""},
    ]
    assert count_by_crno(rows) == {"1101110000001": 2}


def test_build_companies_joins_disclosure_and_label():
    listings = [
        {"basDt": "20261007", "srtnCd": "A005930", "mrktCtg": "KOSPI",
         "itmsNm": "삼성전자", "corpNm": "삼성전자(주)", "crno": "1301110006246"},
        {"basDt": "20261007", "srtnCd": "A000660", "mrktCtg": "KOSPI",
         "itmsNm": "SK하이닉스", "corpNm": "에스케이하이닉스(주)", "crno": "1344110001387"},
        # 법인번호가 없으면 학습 표에서 뺀다.
        {"basDt": "20261007", "srtnCd": "A900110", "mrktCtg": "KOSDAQ",
         "itmsNm": "외국회사", "corpNm": "외국회사", "crno": "0000000000000"},
    ]
    disclosures = {
        "dividend": [{
            "basDt": "20250930", "crno": "1301110006246",
            "pvtrOnskCashDvdnBnfRt": "2.5", "pvtrCrtmNpf": "-10", "pvtrParPrc": "100",
        }],
        "default": [{"crno": "1344110001387", "basDt": "20200101"}],
        "suspend": [],
        "rehab": [{"crno": "1344110001387"}],
        "reduction": [{"crno": "1301110006246"}],
    }

    frame = build_companies(listings, disclosures)
    assert list(frame["item_name"]) == ["삼성전자", "SK하이닉스"]

    samsung = frame.iloc[0]
    assert samsung["has_dividend"] == 1
    assert samsung["dividend_rate"] == 2.5
    assert samsung["profit_negative"] == 1          # 당기순이익이 음수
    assert samsung["reduction_count"] == 1
    assert samsung["distress"] == 0                 # 감자만 있고 부도·정지·회생은 없음

    hynix = frame.iloc[1]
    assert hynix["has_dividend"] == 0
    assert hynix["default_count"] == 1
    assert hynix["rehab_count"] == 1
    assert hynix["distress"] == 1
