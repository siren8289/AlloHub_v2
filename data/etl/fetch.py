"""1단계: 공공데이터 API에서 데이터를 받아 온다.

금융위원회 API는 JSON이다.
  응답 모양: response.body.items.item  (1건이면 딕셔너리, 여러 건이면 리스트)
"""
import time
from datetime import date, timedelta

import requests

from data.etl.config import (
    DISCLOSURE_URLS,
    KRX_ITEM_URL,
    LISTING_LOOKBACK_DAYS,
    ROWS_PER_PAGE,
    SERVICE_KEY,
)

# 공시 원문에 들어 있는 첨부 XML은 매우 길다. 진단에는 필요 없어서 버린다.
DROP_KEYS = {"rptFileCtt", "rptFilePthCtt"}


def need_key():
    if not SERVICE_KEY:
        raise RuntimeError("data/.env 에 DATA_GO_KR_KEY 를 넣어 주세요.")


def as_list(value):
    """API가 1건이면 딕셔너리, 여러 건이면 리스트를 준다. 항상 리스트로 맞춘다."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def shorten_row(row):
    """한 행에서 긴 첨부파일 필드를 빼고, 값은 짧은 글자로 남긴다."""
    clean = {}
    for key, value in row.items():
        if key in DROP_KEYS or isinstance(value, (list, dict)):
            continue
        text = "" if value is None else str(value).strip()
        if len(text) > 300:
            text = text[:300]
        clean[key] = text
    return clean


def _get_page(url, extra_params, page, rows_per_page):
    """한 페이지만 요청하고 (행 리스트, 전체 건수)를 돌려준다."""
    need_key()
    params = {
        "serviceKey": SERVICE_KEY,
        "numOfRows": rows_per_page,
        "pageNo": page,
        "resultType": "json",
        **(extra_params or {}),
    }
    response = requests.get(url, params=params, timeout=90)
    response.raise_for_status()
    body = response.json().get("response", {})

    header = body.get("header") or {}
    result_code = str(header.get("resultCode", ""))
    if result_code not in ("00", "000"):
        raise RuntimeError(f"API 오류 {result_code}: {header.get('resultMsg')}")

    inner = body.get("body") or {}
    items = as_list((inner.get("items") or {}).get("item"))
    rows = [shorten_row(item) for item in items if isinstance(item, dict)]
    total_count = int(inner.get("totalCount") or 0)
    return rows, total_count


def fetch_pages(url, extra_params=None):
    """한 API의 모든 페이지를 받아 행 리스트로 돌려준다."""
    rows = []
    page = 1
    while True:
        page_rows, total_count = _get_page(url, extra_params, page, ROWS_PER_PAGE)
        rows.extend(page_rows)
        if len(rows) >= total_count or not page_rows:
            break
        page += 1
        time.sleep(0.05)  # API 서버에 부담을 주지 않도록 잠깐 쉰다.

    return rows


def recent_weekdays(days):
    """오늘부터 거슬러 올라가며 평일(월~금) 날짜를 YYYYMMDD 로 만든다."""
    found = []
    cursor = date.today()
    while len(found) < days:
        if cursor.weekday() < 5:
            found.append(cursor.strftime("%Y%m%d"))
        cursor -= timedelta(days=1)
    return found


def fetch_listings():
    """최근 평일 중, 상장 종목이 실제로 있는 날짜 하나를 골라 그 목록을 가져온다."""
    for bas_dt in recent_weekdays(LISTING_LOOKBACK_DAYS):
        # 1건만 받아서, 그 날짜에 목록이 있는지(totalCount) 확인한다.
        _, total_count = _get_page(KRX_ITEM_URL, {"basDt": bas_dt}, page=1, rows_per_page=1)
        if total_count < 100:
            print(f"  {bas_dt}: 상장 목록 {total_count}건, 이전 평일을 봅니다.")
            continue
        print(f"  기준일자 {bas_dt} 상장 목록 {total_count}건을 받습니다.")
        return fetch_pages(KRX_ITEM_URL, {"basDt": bas_dt}), bas_dt

    raise RuntimeError("최근 평일에서 상장 종목 목록을 찾지 못했습니다.")


def fetch_disclosures():
    """공시 5종을 모두 받아 {이름: 행 리스트} 로 돌려준다."""
    result = {}
    for name, url in DISCLOSURE_URLS.items():
        print(f"  공시 수집: {name}")
        result[name] = fetch_pages(url)
        print(f"    {len(result[name])}건")
    return result
