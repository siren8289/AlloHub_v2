"""공시 RAG 신규 기능 전용 FastAPI 라우터.

기능 및 설계 이유:
1. 기존 API(`src/api/routes.py`)를 절대 수정하지 않고, 신규 기능만의 전용 엔드포인트를
   독립적으로 격리 제공합니다 (Feature-Based Router).
2. 공시 하이브리드 검색, 근거 기반 RAG 위험 설명, 5대 정량 평가 메트릭 측정을 위한
   표준 REST API 인터페이스를 제공합니다.
"""
from typing import List

from fastapi import APIRouter, HTTPException

from src.features.disclosure_rag_001.disclosure_search.service import (
    search_disclosures,
)
from src.features.disclosure_rag_001.harness.runtime import run_evaluation
from src.features.disclosure_rag_001.orchestration.workflow import (
    run_disclosure_rag,
)
from src.features.disclosure_rag_001.schemas import (
    EvaluationMetrics,
    RAGExplanationRequest,
    RAGExplanationResponse,
    SearchQuery,
    SearchResultChunk,
)

# 신규 기능 전용 라우터 인스턴스 (접두어: /api/v1/disclosure)
router = APIRouter(prefix="/api/v1/disclosure", tags=["Disclosure RAG"])


@router.post("/explain", response_model=RAGExplanationResponse)
def explain_disclosure_risk_api(request: RAGExplanationRequest) -> RAGExplanationResponse:
    """기업 공시 RAG 기반 위험 진단 및 출처 인용 설명 생성 엔드포인트.

    설계 이유:
    종목명과 분석 기준일자를 입력받아 LangGraph 오케스트레이션 파이프라인
    (기업 확인 -> 공시 검색 -> 시점/타사 검증 -> 근거 확인 -> 설명 생성)을 일괄 실행하고
    근거가 인용된 최종 진단 결과와 가드레일 감사 로그를 반환합니다.
    """
    try:
        response = run_disclosure_rag(
            company_name=request.company_name.strip(),
            as_of_date=request.as_of_date.strip() if request.as_of_date else None,
            user_query=request.user_query.strip() if request.user_query else None,
        )
        return response
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"공시 RAG 처리 중 내부 오류 발생: {str(exc)}")


@router.post("/search", response_model=List[SearchResultChunk])
def search_disclosures_api(query: SearchQuery) -> List[SearchResultChunk]:
    """기업 식별자 및 기준일자 필터 기반 공시 하이브리드 검색 엔드포인트.

    설계 이유:
    타사 공시와 미래 공시가 차단된 안전한 공시 청크 검색 결과를 반환하며,
    밀집 벡터 유사도와 희소 키워드 유사도 및 리랭킹 점수를 함께 제공합니다.
    """
    try:
        results = search_disclosures(query)
        return results
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"공시 검색 중 오류 발생: {str(exc)}")


@router.post("/evaluate", response_model=EvaluationMetrics)
def evaluate_rag_pipeline_api(request: RAGExplanationRequest) -> EvaluationMetrics:
    """공시 RAG 파이프라인의 5대 핵심 정량 평가 지표 측정 엔드포인트.

    설계 이유:
    특정 기업 분석 요청에 대해 Recall@K, Citation Accuracy, 기업 ID 일치율,
    분석 시점 정확도(Lookahead 차단율), Faithfulness를 즉시 계산하여
    신뢰도 수준을 평가 보고서 형태로 반환합니다.
    """
    try:
        rag_response = run_disclosure_rag(
            company_name=request.company_name.strip(),
            as_of_date=request.as_of_date.strip() if request.as_of_date else None,
            user_query=request.user_query.strip() if request.user_query else None,
        )

        from src.features.disclosure_rag_001.disclosure_search.service import (
            get_search_corpus,
        )
        corpus = get_search_corpus()
        target_chunks = [c for c in corpus if c.stock_code == rag_response.stock_code and str(c.rcept_dt) <= str(rag_response.as_of_date)]

        screening_mock = {
            "score": rag_response.score,
            "company_name": rag_response.company_name,
        }

        metrics = run_evaluation(
            explanation=rag_response.explanation,
            chunks=target_chunks,
            valid_citations=rag_response.citations,
            target_stock_code=rag_response.stock_code,
            as_of_date=rag_response.as_of_date,
            screening_result=screening_mock,
        )
        return metrics
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"평가 메트릭 계산 중 오류 발생: {str(exc)}")
