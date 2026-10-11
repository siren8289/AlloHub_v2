"""2단계: 받아 온 표를 학습·진단에 쓸 수 있게 정리한다.

전처리 순서
  1. 숫자 문자열 정리 ("1,383" → 1383, 빈 값 → 없음)
  2. 상장 목록에서 법인등록번호가 없는 행(외국기업 등) 제거
  3. 배당·공시는 법인등록번호(crno)마다 최신 날짜 1건, 또는 건수만 남긴다
  4. 상장 종목에 배당·위험 공시를 붙인다
  5. 파생 변수 (배당 있음/없음, 적자 여부, 위험 라벨)
  6. 이상치 자르기 (배당률 0~100, 액면가 음수 제거)
"""
import math

import pandas as pd

# 법인등록번호가 이 값이면 "번호 없음"이다. (외국 상장사 등에 들어 있다)
EMPTY_CRNO = "0000000000000"


def to_number(value):
    """'1,383' 이나 '' 를 숫자로 바꾼다. 숫자가 아니면 None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).replace(",", "").strip()
    if text in ("", "-", "null", "None"):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def count_by_crno(rows):
    """법인등록번호별 공시 건수. 번호가 없는 행은 세지 않는다."""
    counts = {}
    for row in rows:
        crno = str(row.get("crno") or "").strip()
        if not crno or crno == EMPTY_CRNO:
            continue
        counts[crno] = counts.get(crno, 0) + 1
    return counts


def latest_dividend(rows):
    """법인마다 가장 최근 배당 공시 1건만 남긴다.

    같은 회사가 여러 해 배당 공시를 냈을 수 있다. basDt(기준일자)가 큰 행이 최신이다.
    """
    latest = {}
    for row in rows:
        crno = str(row.get("crno") or "").strip()
        if not crno or crno == EMPTY_CRNO:
            continue
        old = latest.get(crno)
        if old is None or str(row.get("basDt") or "") >= str(old.get("basDt") or ""):
            latest[crno] = row
    return latest


def clip(value, low, high):
    """값을 low~high 안으로 자른다. 없거나 숫자가 아니면 low 를 쓴다."""
    number = to_number(value)
    if number is None:
        return float(low)
    return float(min(max(number, low), high))


def build_companies(listings, disclosures):
    """상장 종목 + 공시를 합쳐 회사(종목) 1행짜리 표를 만든다.

    위험 라벨(distress)
      부도, 영업정지, 회생 공시가 한 번이라도 있으면 1, 없으면 0.
      이 값이 ML/DL이 맞히는 정답이다.
      감자 건수는 정답에 넣지 않고, 모델 입력(특징)으로만 쓴다.
    """
    dividend = latest_dividend(disclosures.get("dividend") or [])
    default_count = count_by_crno(disclosures.get("default") or [])
    suspend_count = count_by_crno(disclosures.get("suspend") or [])
    rehab_count = count_by_crno(disclosures.get("rehab") or [])
    reduction_count = count_by_crno(disclosures.get("reduction") or [])

    records = []
    for row in listings:
        crno = str(row.get("crno") or "").strip()
        item_name = str(row.get("itmsNm") or "").strip()
        if not item_name or not crno or crno == EMPTY_CRNO:
            continue

        div = dividend.get(crno) or {}
        # 당기 보통주 현금배당률, 당기순이익, 액면가. 공시가 없으면 0으로 채운다.
        dividend_rate = clip(div.get("pvtrOnskCashDvdnBnfRt"), 0, 100)
        net_profit = to_number(div.get("pvtrCrtmNpf"))
        if net_profit is None:
            net_profit = 0.0
        par_price = clip(div.get("pvtrParPrc"), 0, 100000)

        defaults = default_count.get(crno, 0)
        suspends = suspend_count.get(crno, 0)
        rehabs = rehab_count.get(crno, 0)
        reductions = reduction_count.get(crno, 0)

        records.append({
            "bas_dt": str(row.get("basDt") or ""),
            "stock_code": str(row.get("srtnCd") or ""),
            "market": str(row.get("mrktCtg") or "UNKNOWN"),
            "item_name": item_name,
            "corp_name": str(row.get("corpNm") or item_name),
            "crno": crno,
            "has_dividend": 1 if div else 0,
            "dividend_rate": dividend_rate,
            "net_profit": net_profit,
            "profit_negative": 1 if net_profit < 0 else 0,
            "par_price": par_price,
            # 순이익은 회사마다 차이가 매우 크다. log(1+|값|)으로 줄여 모델 입력에 쓴다.
            "log_profit": round(math.log1p(abs(net_profit)), 4),
            "default_count": defaults,
            "suspend_count": suspends,
            "rehab_count": rehabs,
            "reduction_count": reductions,
            # 정답 라벨. 부도·영업정지·회생이 있으면 위험(1).
            "distress": 1 if (defaults + suspends + rehabs) > 0 else 0,
        })

    frame = pd.DataFrame(records)
    if frame.empty:
        raise RuntimeError("전처리 결과가 비었습니다. 상장 목록을 확인해 주세요.")

    # 같은 종목코드가 두 번 들어오면 첫 행만 남긴다.
    frame = frame.drop_duplicates(subset=["stock_code"]).reset_index(drop=True)
    return frame
