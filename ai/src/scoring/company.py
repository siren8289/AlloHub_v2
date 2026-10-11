"""전처리된 상장 기업 데이터 로딩 및 종목 검색 모듈."""
from typing import Optional

import pandas as pd
from fastapi import HTTPException

from src.core.config import DATA_CSV, MODELS_CSV

_companies: Optional[pd.DataFrame] = None


def load_companies(force_reload: bool = False) -> pd.DataFrame:
    """전처리된 회사 표를 로드합니다. models/ 또는 data/processed/ 경로를 탐색합니다."""
    global _companies
    if _companies is None or force_reload:
        path = MODELS_CSV if MODELS_CSV.exists() else DATA_CSV
        if not path.exists():
            raise HTTPException(
                status_code=500,
                detail="회사 데이터 파일이 없습니다. data 파이프라인을 먼저 실행하세요."
            )
        _companies = pd.read_csv(path, dtype={"crno": str, "stock_code": str})
    return _companies


def normalize_name(name: str) -> str:
    """검색 정확도를 높이기 위해 공백 및 주식회사 표기를 제거하고 소문자로 정규화합니다."""
    text = str(name).strip().lower().replace(" ", "")
    for word in ("주식회사", "(주)", "㈜"):
        text = text.replace(word, "")
    return text


def find_company(name: str, table: Optional[pd.DataFrame] = None) -> pd.Series:
    """종목명 또는 법인명으로 회사 1곳을 조회합니다. 일치하는 회사가 없으면 404를 발생시킵니다."""
    if table is None:
        table = load_companies()

    query = str(name).strip()
    if not query:
        raise HTTPException(status_code=422, detail="회사 이름을 입력하세요.")

    key = normalize_name(query)
    names = table["item_name"].map(normalize_name)
    corps = table["corp_name"].map(normalize_name)

    # 1. 완전 일치 검색 (종목명 우선, 이후 법인명)
    exact = table[names == key]
    if exact.empty:
        exact = table[corps == key]

    # 2. 부분 일치 검색
    if exact.empty:
        exact = table[names.str.contains(key, regex=False) | corps.str.contains(key, regex=False)]

    if exact.empty:
        raise HTTPException(status_code=404, detail=f"상장 종목에서 '{query}' 를 찾지 못했습니다.")

    # 복수 매칭 시 보통주(이름 끝이 '우'가 아닌 종목)를 우선 선택
    exact = exact.copy()
    exact["_preferred"] = exact["item_name"].str.endswith("우").astype(int)
    exact = exact.sort_values(["_preferred", "stock_code"])
    return exact.iloc[0]
