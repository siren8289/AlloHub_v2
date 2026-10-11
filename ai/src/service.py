"""기업 위험 진단.

1. 전처리된 상장 종목 표에서 회사를 찾는다.
2. ML(랜덤포레스트)과 DL(신경망)이 각각 위험 점수(0~100)를 낸다.
3. 두 점수의 평균을 참고 점수로 쓴다.
4. 부도·영업정지·회생 공시가 있으면 단계는 '위험'으로 올린다. (모델보다 공시 사실이 우선)
5. LLM(또는 기본 문장)으로 설명한다.
"""
from pathlib import Path

import pandas as pd
from fastapi import HTTPException

from src.dl_model import predict_dl
from src.features import make_input_frame
from src.llm_explain import explain
from src.ml_model import predict_ml

# 학습 때 복사해 둔 표. 없으면 저장소의 data/processed 를 본다.
MODELS_CSV = Path(__file__).resolve().parent.parent / "models" / "companies.csv"
DATA_CSV = Path(__file__).resolve().parents[2] / "data" / "processed" / "companies.csv"

_companies = None


def load_companies():
    global _companies
    if _companies is None:
        path = MODELS_CSV if MODELS_CSV.exists() else DATA_CSV
        if not path.exists():
            raise HTTPException(status_code=500, detail="회사 데이터 파일이 없습니다. data 파이프라인을 먼저 실행하세요.")
        _companies = pd.read_csv(path, dtype={"crno": str, "stock_code": str})
    return _companies


def normalize_name(name):
    """검색용으로 공백과 '주식회사' 표현을 뺀다."""
    text = str(name).strip().lower().replace(" ", "")
    for word in ("주식회사", "(주)", "㈜"):
        text = text.replace(word, "")
    return text


def find_company(name):
    """종목명 또는 법인명으로 회사 1곳을 찾는다. 없으면 404."""
    table = load_companies()
    query = str(name).strip()
    if not query:
        raise HTTPException(status_code=422, detail="회사 이름을 입력하세요.")

    key = normalize_name(query)
    names = table["item_name"].map(normalize_name)
    corps = table["corp_name"].map(normalize_name)

    exact = table[names == key]
    if exact.empty:
        exact = table[corps == key]
    if exact.empty:
        # 이름이 포함된 종목을 찾는다. 예) "삼성" → 삼성전자, 삼성물산 ...
        exact = table[names.str.contains(key, regex=False) | corps.str.contains(key, regex=False)]

    if exact.empty:
        raise HTTPException(status_code=404, detail=f"상장 종목에서 '{query}' 를 찾지 못했습니다.")

    # 같은 이름이면 보통주(이름 끝이 '우'가 아닌 것)를 먼저 고른다.
    exact = exact.copy()
    exact["_preferred"] = exact["item_name"].str.endswith("우").astype(int)
    exact = exact.sort_values(["_preferred", "stock_code"])
    return exact.iloc[0]


def grade_of(score, company):
    """공시 사실이 있으면 그 사실을 우선하고, 없으면 모델 점수로 단계를 나눈다."""
    if int(company["default_count"]) or int(company["suspend_count"]) or int(company["rehab_count"]):
        return "danger"
    if score >= 40 or int(company["reduction_count"]) > 0:
        return "warning"
    return "stable"


def screen(company_name):
    company = find_company(company_name)
    features = make_input_frame(company)

    ml_score = predict_ml(features)
    dl_score = predict_dl(features)
    score = round((ml_score + dl_score) / 2, 1)

    result = {
        "company_name": company["item_name"],
        "corp_name": company["corp_name"],
        "stock_code": company["stock_code"],
        "market": company["market"],
        "bas_dt": str(company["bas_dt"]),
        "ml_score": ml_score,
        "dl_score": dl_score,
        "score": score,
        "grade": grade_of(score, company),
        "dividend_rate": float(company["dividend_rate"]),
        "net_profit": float(company["net_profit"]),
        "default_count": int(company["default_count"]),
        "suspend_count": int(company["suspend_count"]),
        "rehab_count": int(company["rehab_count"]),
        "reduction_count": int(company["reduction_count"]),
    }
    explanation, source = explain(company, result)
    result["explanation"] = explanation
    result["explanation_source"] = source
    return result
