"""근거 기반 RAG 위험 설명 및 출처 인용 생성 모듈.

기능 및 설계 이유:
1. 검색된 공시 문서의 사실과 재무 위험 지표를 결합하여 신뢰할 수 있는 설명문을 작성합니다.
2. 각 설명 문장에 구체적인 출처 인용([보고서명, 공시일, 회사명])을 명시합니다.
3. [핵심 가드레일] 공시로 확인되지 않은 파산/부도 확정 표현을 필터링 및 순화하여
   AI 환각(Hallucination)에 의한 법적·금융적 오류를 방지합니다.
"""
from typing import Any, List, Mapping, Tuple

from src.core.config import (
    GEMINI_TIMEOUT_MS,
    GRADE_NAMES,
    get_gemini_api_key,
    get_gemini_model,
)
from src.features.disclosure_rag_001.schemas import (
    DisclosureChunk,
    EvidenceCheckResult,
)


def extract_citations_from_chunks(chunks: List[DisclosureChunk]) -> List[str]:
    """검색된 공시 청크들로부터 고유한 출처 인용 표기 목록을 생성합니다.

    설계 이유:
    보고서 작성 시 사용자가 원본 공시 문서를 직접 열람하고 대조할 수 있도록
    문서명, 공시접수일자, 회사명을 정형화된 형식으로 제공하기 위함입니다.
    """
    citations = []
    seen = set()
    for chunk in chunks:
        cite_str = f"[{chunk.report_name}, 공시일: {chunk.rcept_dt}, {chunk.corp_name}]"
        if cite_str not in seen:
            seen.add(cite_str)
            citations.append(cite_str)
    return citations


def build_rag_prompt(
    company: Mapping[str, Any],
    screening_result: Mapping[str, Any],
    evidence_check: EvidenceCheckResult,
    chunks: List[DisclosureChunk],
    user_query: str = ""
) -> str:
    """Gemini LLM 호출을 위한 공시 근거 중심의 엄격한 프롬프트를 생성합니다.

    설계 이유:
    인공지능 모델이 임의의 지식을 지어내지 않고, 반드시 제공된 공시 컨텍스트(Context)와
    검증된 위험 지표만을 인용하도록 엄격한 지침을 프롬프트에 주입합니다.
    """
    grade_kor = GRADE_NAMES.get(str(screening_result.get("grade", "stable")), "안정")
    company_name = company.get("item_name", "")

    # 공시 컨텍스트 조립
    context_lines = []
    for chunk in chunks:
        context_lines.append(
            f"- 출처: [{chunk.report_name}, 공시일:{chunk.rcept_dt}] 내용: {chunk.content}"
        )
    context_text = "\n".join(context_lines) if context_lines else "관련 주요 공시 없음"

    prompt_lines = [
        "너는 공시 분석 기반의 벤처/기업 출자 심사 보조 AI 도우미다.",
        "아래 제공된 [공시 문서 발췌]와 [재무 위험 진단 수치]만을 근거로 하여 3~4문장의 쉬운 한국어로 위험 요인을 설명해라.",
        "",
        "[필수 가드레일 지침]",
        "1. 제공된 공시 문건에 명시된 사실만 언급하고, 없는 내용을 추측하지 마라.",
        "2. 반드시 인용 출처(예: [보고서명, 공시일])를 문장에 포함하거나 문장 끝에 밝혀라.",
        "3. 기업의 파산이나 부도를 근거 없이 단정하거나 확정 표현을 쓰지 마라.",
        "4. 매수·매도·투자 권유를 절대 하지 마라.",
        "",
        f"[기업 정보] 종목명: {company_name} / 시장: {company.get('market', '')} / 기준일: {screening_result.get('bas_dt', '')}",
        f"[진단 결과] 종합 위험점수: {screening_result.get('score')}점 ({grade_kor} 단계)",
        f"- 감자: {screening_result.get('reduction_count')}건, 영업정지: {screening_result.get('suspend_count')}건, "
        f"부도: {screening_result.get('default_count')}건, 회생: {screening_result.get('rehab_count')}건",
        "",
        "[공시 문서 발췌]",
        context_text,
    ]

    if user_query:
        prompt_lines.append(f"\n[사용자 질의] {user_query}")

    return "\n".join(prompt_lines)


def sanitize_risk_statements(explanation: str, evidence_check: EvidenceCheckResult) -> str:
    """생성된 설명문에서 근거 없는 부도/파산 확정 표현을 필터링 및 완화합니다.

    설계 이유:
    [핵심 가드레일] LLM 또는 템플릿이 사실 확인 없이 '부도 확정', '파산 확실' 등의 치명적인
    단정 표현을 출력할 경우 기업 신용 훼손 및 오판 위험이 있으므로, 안전 표현으로 자동 보정합니다.
    """
    text = explanation
    # 부도 공시 근거가 없는데 확정 표현이 들어간 경우
    has_default_evidence = any(
        item.risk_factor == "부도발생 공시" and item.has_confirmed_evidence
        for item in evidence_check.evidence_items
    )
    if not has_default_evidence:
        unsafe_phrases = ["부도 확정", "파산 확실", "파산 선고", "부도가 발생하여", "부도 처리되었습니다"]
        for phrase in unsafe_phrases:
            if phrase in text:
                text = text.replace(phrase, "재무적 주의 관찰이 필요한 상태이며")

    return text


def generate_basic_rag_explanation(
    company: Mapping[str, Any],
    screening_result: Mapping[str, Any],
    evidence_check: EvidenceCheckResult,
    chunks: List[DisclosureChunk]
) -> str:
    """Gemini API가 없을 때 사용하는 규칙 기반의 정확한 공시 근거 인용 설명문입니다.

    설계 이유:
    오프라인 환경이나 API 키가 없는 상황에서도 수치 데이터와 공시 인용문을 결합하여
    규칙 기반으로 완벽한 근거 중심 설명문을 일관되게 생성하기 위함입니다.
    """
    company_name = str(company.get("item_name", ""))
    market = str(company.get("market", ""))
    score = screening_result.get("score", 0.0)
    grade_kor = GRADE_NAMES.get(str(screening_result.get("grade", "stable")), "안정")

    intro = f"{company_name}({market})의 종합 위험 점수는 {score}점으로 '{grade_kor}' 단계입니다."

    # 확인된 공시 근거 문장 합성
    confirmed_evidences = []
    for item in evidence_check.evidence_items:
        if item.has_confirmed_evidence and item.citation:
            confirmed_evidences.append(f"{item.risk_factor}의 경우 {item.citation}에 근거하여 확인되었습니다.")

    if confirmed_evidences:
        evidence_text = " " + " ".join(confirmed_evidences)
    else:
        evidence_text = " 수집된 기준일 이전 공시에서는 특이 위험 사유가 직접 확인되지 않았습니다."

    conclusion = (
        " 본 결과는 과거 공시 및 재무제표를 바탕으로 한 참고 자료이며, "
        "공시상 직접 확인되지 않은 파산이나 부도를 임의로 단정하지 않습니다."
    )

    return intro + evidence_text + conclusion


def generate_rag_explanation(
    company: Mapping[str, Any],
    screening_result: Mapping[str, Any],
    evidence_check: EvidenceCheckResult,
    chunks: List[DisclosureChunk],
    user_query: str = ""
) -> Tuple[str, str, List[str]]:
    """(설명 문장, 생성 출처, 인용 출처 목록)을 생성하여 반환합니다.

    설계 이유:
    Gemini API 키가 설정되어 있으면 프롬프트 기반의 유연한 LLM 설명을 생성하고,
    미설정 또는 오류 시 신뢰할 수 있는 템플릿 기반 설명을 생성한 뒤
    가드레일 검사를 거쳐 안전성이 검증된 텍스트만 최종 반환합니다.
    """
    citations = extract_citations_from_chunks(chunks)
    api_key = get_gemini_api_key()

    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS),
            )
            prompt = build_rag_prompt(company, screening_result, evidence_check, chunks, user_query)
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=prompt,
            )
            if response.text:
                cleaned = sanitize_risk_statements(response.text.strip(), evidence_check)
                return cleaned, "rag_gemini", citations
        except Exception:
            # API 호출 실패 시 조용히 기본 템플릿 생성기로 전환
            pass

    # Gemini 미사용 시 기본 템플릿 생성기 적용
    basic_text = generate_basic_rag_explanation(company, screening_result, evidence_check, chunks)
    cleaned_basic = sanitize_risk_statements(basic_text, evidence_check)
    return cleaned_basic, "rag_basic", citations
