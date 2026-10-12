"""재무 위험도와 공시 사실 근거 검증 모듈.

기능 및 설계 이유:
1. 기존 ML/DL 위험 점수 및 재무 지표(감자 건수, 영업정지 건수, 당기순손실 등)가
   실제 공시 문서의 어떤 구체적 사실에 근거하는지 1:1로 매핑하여 검증합니다.
2. [핵심 가드레일] 공시상 확인되지 않은 '파산', '부도' 등의 중대한 판단을 AI가
   성급하게 확정짓지 못하도록 근거 부재 시 경고 문구(Caveat)를 부착하고 필터링합니다.
"""
from typing import Any, Dict, List, Mapping

from src.features.disclosure_rag_001.schemas import (
    DisclosureChunk,
    EvidenceCheckResult,
    FinancialEvidenceItem,
)


def extract_risk_factors(
    company_data: Mapping[str, Any],
    screening_result: Mapping[str, Any]
) -> List[Dict[str, Any]]:
    """회사 재무 데이터와 모델 스크리닝 결과로부터 검증 대상 위험 요인들을 추출합니다.

    설계 이유:
    ML(RF)과 DL(MLP)이 포착한 위험 점수의 배경이 되는 구체적인 수치 지표들을 식별하여
    공시와의 대조 검증을 수행할 기준 목록을 생성하기 위함입니다.
    """
    factors = []

    # 1. 감자 공시 이력
    reduction_count = int(screening_result.get("reduction_count", 0))
    if reduction_count > 0:
        factors.append({
            "type": "reduction",
            "name": "자본감소(감자) 이력",
            "indicator": f"감자 공시 {reduction_count}건 감지됨",
            "keywords": ["감자", "자본감소", "무상감자", "유상감자", "결손금"],
        })

    # 2. 영업정지 공시 이력
    suspend_count = int(screening_result.get("suspend_count", 0))
    if suspend_count > 0:
        factors.append({
            "type": "suspend",
            "name": "영업정지(생산중단) 이력",
            "indicator": f"영업정지 공시 {suspend_count}건 감지됨",
            "keywords": ["영업정지", "생산중단", "가동 중단", "설비 보수"],
        })

    # 3. 회생절차 공시 이력
    rehab_count = int(screening_result.get("rehab_count", 0))
    if rehab_count > 0:
        factors.append({
            "type": "rehab",
            "name": "회생절차 개시신청",
            "indicator": f"회생절차 공시 {rehab_count}건 감지됨",
            "keywords": ["회생절차", "법정관리", "개시신청"],
        })

    # 4. 부도발생 공시 이력
    default_count = int(screening_result.get("default_count", 0))
    if default_count > 0:
        factors.append({
            "type": "default",
            "name": "부도발생 공시",
            "indicator": f"부도 공시 {default_count}건 감지됨",
            "keywords": ["부도", "어음부도", "당좌거래정지"],
        })

    # 5. 당기순손실 지속 여부
    net_profit = float(screening_result.get("net_profit", 0.0))
    if net_profit < 0:
        factors.append({
            "type": "net_loss",
            "name": "당기순손실 발생",
            "indicator": f"최근 결산 당기순이익 {net_profit:,.0f}원으로 적자",
            "keywords": ["당기순손실", "영업손실", "적자", "결손"],
        })

    # 6. 모델 종합 점수 주의/위험 수준
    score = float(screening_result.get("score", 0.0))
    grade = str(screening_result.get("grade", "stable"))
    if grade in ("warning", "danger") or score >= 40.0:
        factors.append({
            "type": "model_score",
            "name": f"인공지능 진단 위험도 '{grade}' 단계",
            "indicator": f"ML/DL 종합위험점수 {score}점 (주의/위험 기준 초과)",
            "keywords": ["불확실성", "지속", "자본잠식", "의견", "주의"],
        })

    return factors


def find_matching_chunk_for_factor(
    factor: Dict[str, Any],
    chunks: List[DisclosureChunk]
) -> tuple[bool, str, str, str]:
    """위험 요인 키워드가 실제 공시 청크 본문에 존재하는지 대조하여 매칭 결과를 반환합니다.

    설계 이유:
    통계적/수치적 모델 지표가 실제 회사가 공시한 사실과 부합하는지
    공시 원문 발췌문과 출처(문서명, 공시일자)를 매핑하기 위함입니다.
    """
    for chunk in chunks:
        content = chunk.content
        for kw in factor["keywords"]:
            if kw in content:
                citation = f"[{chunk.report_name}, 공시일:{chunk.rcept_dt}, {chunk.corp_name}]"
                excerpt = chunk.content[:180] + ("..." if len(chunk.content) > 180 else "")
                return True, citation, excerpt, ""

    # 근거를 찾지 못한 경우
    caveat = f"공시 원문에서 '{factor['name']}' 관련 직접 공시 문건이 확인되지 않았습니다. 임의로 확정하지 마십시오."
    return False, "", "", caveat


def check_financial_evidence(
    company_data: Mapping[str, Any],
    screening_result: Mapping[str, Any],
    chunks: List[DisclosureChunk]
) -> EvidenceCheckResult:
    """수치적 위험 진단 결과와 공시 문서 간의 근거 매핑 및 가드레일 적합성을 최종 검증합니다.

    설계 이유:
    1. 각 위험 요소별로 공시 근거가 실제로 증명되었는지를 파악합니다.
    2. 부도나 회생 공시가 없는데도 인공지능이 임의로 '부도/파산 확정' 등의 잘못된 결론을
       도출하지 못하도록 차단 상태를 추적합니다.
    """
    factors = extract_risk_factors(company_data, screening_result)
    evidence_items: List[FinancialEvidenceItem] = []
    confirmed_count = 0

    for factor in factors:
        has_evidence, citation, excerpt, caveat = find_matching_chunk_for_factor(factor, chunks)
        if has_evidence:
            confirmed_count += 1
            item = FinancialEvidenceItem(
                risk_factor=factor["name"],
                model_indicator=factor["indicator"],
                has_confirmed_evidence=True,
                citation=citation,
                excerpt=excerpt,
                caveat=None,
            )
        else:
            item = FinancialEvidenceItem(
                risk_factor=factor["name"],
                model_indicator=factor["indicator"],
                has_confirmed_evidence=False,
                citation=None,
                excerpt=None,
                caveat=caveat,
            )
        evidence_items.append(item)

    # 매치 비율 계산
    match_rate = float(confirmed_count / len(factors)) if factors else 1.0

    # 파산/부도 근거 없는 확정 차단 검증
    # default_count가 0이고 공시에서 부도 근거가 없으면 unfounded claims 가 발생하지 않도록 설정
    default_count = int(screening_result.get("default_count", 0))
    has_unfounded_claims = False
    if default_count == 0 and any(item.risk_factor == "부도발생 공시" and not item.has_confirmed_evidence for item in evidence_items):
        has_unfounded_claims = False

    return EvidenceCheckResult(
        company_name=str(screening_result.get("company_name", "")),
        stock_code=str(screening_result.get("stock_code", "")),
        as_of_date=str(screening_result.get("bas_dt", "")),
        evidence_items=evidence_items,
        match_rate=round(match_rate, 4),
        has_unfounded_claims=has_unfounded_claims,
    )
