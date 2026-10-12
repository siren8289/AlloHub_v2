"""공시 RAG 기능 입출력 계약 및 데이터 모델 정의.

설계 이유:
공시 데이터, 검색 결과, 재무 근거, 설명문 생성 및 평가 지표의 규격을 명확히 정의하여
시스템 모듈 간의 결합도를 낮추고 데이터 무결성을 보장합니다.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DisclosureDocument(BaseModel):
    """공시 원본 문서 또는 수집 데이터 모델."""
    doc_id: str = Field(description="공시 문서 고유 식별자")
    corp_code: str = Field(description="법인 고유번호 또는 법인등록번호")
    corp_name: str = Field(description="법인명")
    stock_code: str = Field(description="상장 종목코드 (예: A000040)")
    report_name: str = Field(description="공시 보고서명 (예: 주요사항보고서(감자결정))")
    rcept_no: str = Field(description="공시 접수번호")
    rcept_dt: str = Field(description="공시 접수일자 (YYYYMMDD 형식)")
    content: str = Field(description="공시 본문 전체 또는 요약 텍스트")
    section: str = Field(default="전체", description="공시 본문 주요 섹션명")


class DisclosureChunk(BaseModel):
    """검색 및 임베딩을 위해 분할된 공시 청크 모델."""
    chunk_id: str = Field(description="청크 고유 식별자")
    doc_id: str = Field(description="원본 공시 문서 식별자")
    corp_code: str = Field(description="법인 식별자")
    corp_name: str = Field(description="법인명")
    stock_code: str = Field(description="종목코드")
    report_name: str = Field(description="보고서명")
    rcept_dt: str = Field(description="공시 접수일자 (YYYYMMDD)")
    section: str = Field(description="해당 청크가 속한 섹션명")
    content: str = Field(description="청크 텍스트 본문")
    embedding: Optional[List[float]] = Field(default=None, description="임베딩 벡터")


class SearchFilter(BaseModel):
    """공시 검색 시 적용되는 필터 조건."""
    stock_code: str = Field(description="검색 대상 종목코드 (타사 공시 차단용)")
    as_of_date: str = Field(description="분석 기준일자 (YYYYMMDD, 미래 공시 혼입 차단용)")
    report_types: Optional[List[str]] = Field(default=None, description="선택적 공시 유형 필터")


class SearchQuery(BaseModel):
    """공시 하이브리드 검색 요청 쿼리."""
    query_text: str = Field(description="검색 질의어")
    filter: SearchFilter = Field(description="기업 및 기준일자 필수 필터")
    top_k: int = Field(default=3, ge=1, le=20, description="반환할 상위 청크 수")
    hybrid_alpha: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="하이브리드 가중치 (1.0: 순수 벡터, 0.0: 순수 키워드)"
    )


class SearchResultChunk(BaseModel):
    """검색 결과 청크와 유사도 점수."""
    chunk: DisclosureChunk = Field(description="검색된 공시 청크")
    dense_score: float = Field(description="밀집 벡터 코사인 유사도 점수")
    sparse_score: float = Field(description="희소 키워드 매칭 점수")
    hybrid_score: float = Field(description="하이브리드 결합 점수")
    rerank_score: float = Field(description="최신성 및 핵심 위험어 가중치가 반영된 최종 점수")


class FinancialEvidenceItem(BaseModel):
    """재무 위험 지표와 공시 내용 간의 근거 매핑 항목."""
    risk_factor: str = Field(description="위험 요인 명칭 (예: 감자 이력, 영업정지 등)")
    model_indicator: str = Field(description="기존 ML/DL 또는 재무 피처 수치 설명")
    has_confirmed_evidence: bool = Field(description="공시 문서에서 실제 사실 근거가 확인되었는지 여부")
    citation: Optional[str] = Field(default=None, description="인용 출처 표기 (문서명, 공시일, 종목)")
    excerpt: Optional[str] = Field(default=None, description="공시 원문 발췌 내용")
    caveat: Optional[str] = Field(default=None, description="근거 미확인 시 주의 문구 (임의 확정 방지용)")


class EvidenceCheckResult(BaseModel):
    """재무 위험도와 공시 근거 검증 전체 결과."""
    company_name: str = Field(description="종목명")
    stock_code: str = Field(description="종목코드")
    as_of_date: str = Field(description="분석 기준일자")
    evidence_items: List[FinancialEvidenceItem] = Field(description="위험 요인별 근거 검증 목록")
    match_rate: float = Field(description="위험 요인 대비 공시 근거 확인 비율 (0.0 ~ 1.0)")
    has_unfounded_claims: bool = Field(
        description="공시 근거가 없는데 파산/부도로 성급하게 확정된 주장이 존재하는지 여부"
    )


class RAGExplanationRequest(BaseModel):
    """공시 RAG 기반 위험 진단 설명 요청 계약."""
    company_name: str = Field(
        min_length=1,
        max_length=100,
        description="진단 대상 상장기업 종목명 또는 법인명",
        examples=["KR모터스", "동화약품", "삼성전자"]
    )
    as_of_date: Optional[str] = Field(
        default=None,
        description="분석 기준일자 (YYYYMMDD 형식, 미지정 시 기업 최신 기준일자 자동 적용)",
        examples=["20261010"]
    )
    user_query: Optional[str] = Field(
        default=None,
        description="사용자 추가 질문 또는 중점 검토 요구사항"
    )


class RAGExplanationResponse(BaseModel):
    """공시 RAG 기반 위험 진단 설명 최종 응답."""
    company_name: str = Field(description="종목명")
    corp_name: str = Field(description="법인명")
    stock_code: str = Field(description="종목코드")
    as_of_date: str = Field(description="분석 기준일자")
    ml_score: float = Field(description="ML 위험 점수 (0~100)")
    dl_score: float = Field(description="DL 위험 점수 (0~100)")
    score: float = Field(description="종합 위험 점수 (0~100)")
    grade: str = Field(description="위험 등급 (stable/warning/danger)")
    explanation: str = Field(description="근거 인용이 포함된 최종 AI 설명 문장")
    explanation_source: str = Field(description="설명 생성기 (rag_gemini 또는 rag_basic)")
    citations: List[str] = Field(description="인용된 공시 출처 목록")
    evidence_items: List[FinancialEvidenceItem] = Field(description="세부 근거 검증 항목")
    guardrail_status: Dict[str, bool] = Field(description="Harness 가드레일 통과 여부")
    audit_trace: List[str] = Field(description="실행 감사 로그 단계별 내역")


class EvaluationMetrics(BaseModel):
    """RAG 파이프라인 정량 평가 메트릭 모델."""
    recall_at_k: float = Field(description="상위 K개 검색의 관련 공시 회수율 (Recall@K)")
    citation_accuracy: float = Field(description="설명문에 포함된 인용의 실제 문서 일치도")
    company_id_match_rate: float = Field(description="검색 및 인용 문서의 대상 기업 ID 일치율 (목표 1.0)")
    point_in_time_accuracy: float = Field(description="기준일 이전 공시 준수율 (Lookahead 차단율, 목표 1.0)")
    faithfulness_score: float = Field(description="공시 원문 및 재무 지표 대비 설명문의 사실 충실도")
