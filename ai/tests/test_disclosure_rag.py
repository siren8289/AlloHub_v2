"""공시 RAG 신규 기능 종합 pytest 테스트 모듈.

검증 항목:
1. 청킹 및 임베딩 생성 (오프라인 환경 보장)
2. 타사 공시 혼입 차단 가드레일 (기업 식별자 격리 100%)
3. 미래 공시 혼입 차단 가드레일 (Point-in-time / Lookahead bias 차단 100%)
4. 재무 위험도 근거 매핑 및 근거 없는 부도/파산 확정 방지
5. LangGraph 오케스트레이션 5단계 파이프라인 무중단 실행
6. 5대 정량 평가 메트릭 (Recall@K, Citation Accuracy, 기업 ID 일치율, 시점 정확도, Faithfulness)
7. 기능 전용 API 엔드포인트 동작 검증
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.features.disclosure_rag_001.disclosure_knowledge.service import (
    chunk_document,
    compute_fallback_embedding,
    get_default_disclosure_documents,
)
from src.features.disclosure_rag_001.disclosure_search.service import (
    calculate_cosine_similarity,
    search_disclosures_with_filter,
)
from src.features.disclosure_rag_001.financial_evidence.service import (
    check_financial_evidence,
)
from src.features.disclosure_rag_001.harness.runtime import (
    enforce_read_only_query,
    run_evaluation,
    validate_company_isolation,
    validate_lookahead_bias,
)
from src.features.disclosure_rag_001.orchestration.workflow import (
    run_disclosure_rag,
)
from src.features.disclosure_rag_001.risk_explanation.service import (
    generate_rag_explanation,
    sanitize_risk_statements,
)
from src.features.disclosure_rag_001.router import router
from src.features.disclosure_rag_001.schemas import (
    DisclosureDocument,
    SearchFilter,
)


def test_chunking_and_embedding():
    """공시 본문 청킹과 결정론적 임베딩 생성이 정확히 동작하는지 검증합니다."""
    sample_doc = DisclosureDocument(
        doc_id="TEST_01",
        corp_code="123456",
        corp_name="테스트기업(주)",
        stock_code="A123456",
        report_name="사업보고서",
        rcept_no="202601010001",
        rcept_dt="20260101",
        section="재무상태",
        content="이것은 첫 번째 문장입니다. 감자 결정이 있었습니다. 회생 절차는 없습니다. " * 10,
    )
    chunks = chunk_document(sample_doc, chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1
    assert chunks[0].stock_code == "A123456"
    assert chunks[0].rcept_dt == "20260101"

    # 임베딩 생성 및 코사인 유사도 검증
    emb1 = compute_fallback_embedding("자본금 감소 및 무상감자 결정")
    emb2 = compute_fallback_embedding("결손금 보전을 위한 감자")
    emb3 = compute_fallback_embedding("완전히 무관한 날씨 정보 및 여행")

    sim_similar = calculate_cosine_similarity(emb1, emb2)
    sim_diff = calculate_cosine_similarity(emb1, emb3)
    assert sim_similar > sim_diff


def test_guardrail_company_isolation():
    """검색 결과에서 다른 회사의 공시가 섞이지 않고 100% 차단되는지 검증합니다."""
    docs = get_default_disclosure_documents()
    # KR모터스(A000040) 종목만 검색
    search_filter = SearchFilter(stock_code="A000040", as_of_date="20261010")
    results = search_disclosures_with_filter(
        query_text="재무구조 개선 감자 및 배당",
        search_filter=search_filter,
        top_k=5,
    )

    for item in results:
        # 모든 결과가 KR모터스여야 함 (동화약품이나 삼성전자 혼입 차단)
        assert item.chunk.stock_code == "A000040"
        assert "KR모터스" in item.chunk.corp_name

    # 하네스 검증 함수 직접 테스트
    chunks = [item.chunk for item in results]
    isolated_chunks, passed = validate_company_isolation(chunks, "A000040")
    assert passed is True
    assert len(isolated_chunks) == len(chunks)


def test_guardrail_lookahead_prevention():
    """분석 기준일자 이후의 미래 공시가 원천 차단되는지 검증합니다."""
    # 20261010 기준일로 검색 (20261115 미래 유상증자 공시 배제 확인)
    search_filter = SearchFilter(stock_code="A000040", as_of_date="20261010")
    results = search_disclosures_with_filter(
        query_text="운영자금 조달 유상증자",
        search_filter=search_filter,
        top_k=5,
    )

    for item in results:
        # 20261010 보다 늦은 공시가 없어야 함
        assert int(item.chunk.rcept_dt) <= 20261010
        assert "미래 공시" not in item.chunk.content

    # 하네스 검증 함수 직접 테스트
    chunks = [item.chunk for item in results]
    time_validated, passed = validate_lookahead_bias(chunks, "20261010")
    assert passed is True
    assert len(time_validated) == len(chunks)


def test_read_only_access_guard():
    """쓰기 및 변조 쿼리가 차단되는지 검증합니다."""
    assert enforce_read_only_query("SELECT * FROM disclosure_chunks WHERE stock_code = 'A000040'") is True
    assert enforce_read_only_query("INSERT INTO disclosure_chunks VALUES (1, 2)") is False
    assert enforce_read_only_query("DROP TABLE disclosure_chunks") is False
    assert enforce_read_only_query("DELETE FROM disclosure_chunks") is False


def test_financial_evidence_and_unfounded_claims():
    """재무 위험 지표와 공시 사실이 매핑되고 근거 없는 부도 확정이 차단되는지 검증합니다."""
    company_data = {
        "item_name": "KR모터스",
        "corp_name": "KR모터스(주)",
        "stock_code": "A000040",
        "market": "KOSPI",
    }
    screening_result = {
        "company_name": "KR모터스",
        "stock_code": "A000040",
        "score": 58.5,
        "grade": "danger",
        "default_count": 0,
        "suspend_count": 1,
        "rehab_count": 0,
        "reduction_count": 3,
        "net_profit": -21027.0,
        "bas_dt": "20261007",
    }

    # 검색 실행
    search_filter = SearchFilter(stock_code="A000040", as_of_date="20261007")
    results = search_disclosures_with_filter(
        query_text="감자 결손 영업정지",
        search_filter=search_filter,
        top_k=5,
    )
    chunks = [r.chunk for r in results]

    evidence_result = check_financial_evidence(company_data, screening_result, chunks)
    assert evidence_result.match_rate > 0.0

    # 감자 이력 근거 확인 여부
    reduction_item = next((item for item in evidence_result.evidence_items if "감자" in item.risk_factor), None)
    assert reduction_item is not None
    assert reduction_item.has_confirmed_evidence is True
    assert "주요사항보고서(감자결정)" in reduction_item.citation

    # 부도 관련 근거 없는 확정 차단 확인
    assert evidence_result.has_unfounded_claims is False

    # 사후 가드레일 텍스트 정화 테스트
    bad_text = "이 기업은 부도 확정 상태이며 파산 선고되었습니다."
    sanitized = sanitize_risk_statements(bad_text, evidence_result)
    assert "부도 확정" not in sanitized
    assert "파산 선고" not in sanitized


def test_risk_explanation_generation_with_citations(monkeypatch):
    """설명문에 문서명과 공시일 등 정확한 출처 인용이 표기되는지 검증합니다."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    company_data = {
        "item_name": "KR모터스",
        "corp_name": "KR모터스(주)",
        "stock_code": "A000040",
        "market": "KOSPI",
    }
    screening_result = {
        "company_name": "KR모터스",
        "score": 58.5,
        "grade": "danger",
        "default_count": 0,
        "suspend_count": 1,
        "rehab_count": 0,
        "reduction_count": 3,
        "net_profit": -21027.0,
        "bas_dt": "20261007",
    }

    search_filter = SearchFilter(stock_code="A000040", as_of_date="20261007")
    results = search_disclosures_with_filter(
        query_text="감자 결손",
        search_filter=search_filter,
        top_k=3,
    )
    chunks = [r.chunk for r in results]
    evidence_res = check_financial_evidence(company_data, screening_result, chunks)

    explanation, source, citations = generate_rag_explanation(
        company=company_data,
        screening_result=screening_result,
        evidence_check=evidence_res,
        chunks=chunks,
    )

    assert source == "rag_basic"
    assert "KR모터스" in explanation
    assert len(citations) > 0
    assert any("주요사항보고서" in c for c in citations)


def test_orchestration_workflow_pipeline(monkeypatch):
    """LangGraph 기반 5단계 파이프라인의 전체 실행 및 감사 추적을 검증합니다."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = run_disclosure_rag(
        company_name="KR모터스",
        as_of_date="20261007",
        user_query="감자 및 영업정지 관련 공시를 확인해줘",
    )

    assert response.company_name == "KR모터스"
    assert response.stock_code == "A000040"
    assert response.grade in ("warning", "danger")
    assert response.score > 0
    assert len(response.citations) > 0
    assert len(response.evidence_items) > 0

    # 가드레일 상태 검증
    assert response.guardrail_status["company_isolation"] is True
    assert response.guardrail_status["lookahead_blocked"] is True

    # 5단계 감사 로그 검증
    trace_text = "\n".join(response.audit_trace)
    assert "1_기업확인" in trace_text
    assert "2_공시검색" in trace_text
    assert "3_기간_및_식별자_검증" in trace_text
    assert "4_근거확인" in trace_text
    assert "5_설명생성" in trace_text


def test_harness_evaluation_metrics():
    """Recall@K, Citation Accuracy, 기업 ID 일치율, 시점 정확도, Faithfulness 평가 지표를 검증합니다."""
    search_filter = SearchFilter(stock_code="A000040", as_of_date="20261007")
    results = search_disclosures_with_filter(
        query_text="감자 영업정지 결손",
        search_filter=search_filter,
        top_k=3,
    )
    chunks = [r.chunk for r in results]
    citations = [f"[{c.report_name}, 공시일: {c.rcept_dt}, {c.corp_name}]" for c in chunks]

    explanation = (
        "KR모터스의 종합 위험 점수는 58.5점으로 위험 단계입니다. "
        "감자의 경우 [주요사항보고서(감자결정), 공시일: 20260512, KR모터스(주)]에 근거하여 확인되었습니다."
    )
    screening_mock = {"score": 58.5, "company_name": "KR모터스"}

    metrics = run_evaluation(
        explanation=explanation,
        chunks=chunks,
        valid_citations=citations,
        target_stock_code="A000040",
        as_of_date="20261007",
        screening_result=screening_mock,
    )

    # 1. 기업 ID 일치율 100% 필수
    assert metrics.company_id_match_rate == 1.0
    # 2. 분석 시점 정확도 100% 필수 (미래 공시 배제)
    assert metrics.point_in_time_accuracy == 1.0
    # 3. 인용 정확도 양호
    assert metrics.citation_accuracy >= 0.8
    # 4. 회수율 및 사실 충실도 확인
    assert metrics.recall_at_k >= 0.8
    assert metrics.faithfulness_score >= 0.8


def test_feature_api_endpoints(monkeypatch):
    """신규 기능 전용 API 엔드포인트(/explain, /search, /evaluate)를 검증합니다."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    # 기존 main.py를 수정하지 않고 신규 라우터 단독 테스트 클라이언트 구성
    app = FastAPI(title="Test Feature App")
    app.include_router(router)
    client = TestClient(app)

    # 1. /explain 엔드포인트 테스트
    resp = client.post("/api/v1/disclosure/explain", json={
        "company_name": "KR모터스",
        "as_of_date": "20261007"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_name"] == "KR모터스"
    assert data["stock_code"] == "A000040"
    assert len(data["citations"]) > 0
    assert data["guardrail_status"]["company_isolation"] is True
    assert data["guardrail_status"]["lookahead_blocked"] is True

    # 2. /search 엔드포인트 테스트
    search_resp = client.post("/api/v1/disclosure/search", json={
        "query_text": "무상감자",
        "filter": {
            "stock_code": "A000040",
            "as_of_date": "20261007"
        },
        "top_k": 2
    })
    assert search_resp.status_code == 200
    search_data = search_resp.json()
    assert len(search_data) > 0
    assert search_data[0]["chunk"]["stock_code"] == "A000040"

    # 3. /evaluate 엔드포인트 테스트
    eval_resp = client.post("/api/v1/disclosure/evaluate", json={
        "company_name": "KR모터스",
        "as_of_date": "20261007"
    })
    assert eval_resp.status_code == 200
    eval_data = eval_resp.json()
    assert eval_data["company_id_match_rate"] == 1.0
    assert eval_data["point_in_time_accuracy"] == 1.0
    assert eval_data["citation_accuracy"] >= 0.8

    # 4. 없는 기업 요청 시 404 테스트
    not_found_resp = client.post("/api/v1/disclosure/explain", json={
        "company_name": "가상의존재하지않는회사999"
    })
    assert not_found_resp.status_code == 404
