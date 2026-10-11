"""기업 위험 진단 오케스트레이션 서비스.

데이터 조회, 피처 추출, ML 및 DL 추론, 종합 점수 및 등급 계산, 설명 생성을 종합 수행합니다.
"""
from typing import Any, Dict

from src.inference.dl_risk import predict_dl
from src.inference.ml_risk import predict_ml
from src.llm.explainer import explain
from src.scoring.company import find_company
from src.scoring.features import make_input_frame
from src.scoring.rules import grade_of


def screen(company_name: str) -> Dict[str, Any]:
    """회사명을 입력받아 상장 기업 위험 진단 결과를 반환합니다."""
    company = find_company(company_name)
    features = make_input_frame(company)

    ml_score = predict_ml(features)
    dl_score = predict_dl(features)
    score = round((ml_score + dl_score) / 2, 1)
    grade = grade_of(score, company)

    result = {
        "company_name": company["item_name"],
        "corp_name": company["corp_name"],
        "stock_code": company["stock_code"],
        "market": company["market"],
        "bas_dt": str(company["bas_dt"]),
        "ml_score": ml_score,
        "dl_score": dl_score,
        "score": score,
        "grade": grade,
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
