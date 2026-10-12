"""공시 RAG 오케스트레이션 파이프라인 (LangGraph 단계 및 분기 워크플로우).

기능 및 설계 이유:
1. 5단계 워크플로우를 체계적으로 실행합니다:
   [1단계: 기업 확인] -> [2단계: 공시 검색] -> [3단계: 시점/타사 검증] -> [4단계: 근거 확인] -> [5단계: 설명 생성]
2. 조건부 분기: 기업 조회 실패 시 조기 안전 종료(Early Termination) 처리.
3. LangGraph 라이브러리가 설치되어 있으면 공식 StateGraph를 사용하고,
   미설치 환경에서는 동일한 단계별 상태 전이와 조건부 분기를 수행하는
   경량 내장 StateGraph 엔진을 통해 100% 무중단 실행을 보장합니다.
"""
from typing import Any, Callable, Dict, List, Optional, TypedDict

from src.features.disclosure_rag_001.disclosure_search.service import (
    search_disclosures_with_filter,
)
from src.features.disclosure_rag_001.financial_evidence.service import (
    check_financial_evidence,
)
from src.features.disclosure_rag_001.harness.runtime import (
    HarnessAuditor,
    validate_company_isolation,
    validate_lookahead_bias,
)
from src.features.disclosure_rag_001.risk_explanation.service import (
    generate_rag_explanation,
)
from src.features.disclosure_rag_001.schemas import (
    DisclosureChunk,
    EvidenceCheckResult,
    RAGExplanationResponse,
    SearchFilter,
)
from src.scoring.company import find_company
from src.service.screener import screen


class PipelineState(TypedDict, total=False):
    """파이프라인 단계 간 전달되는 전역 상태 딕셔너리."""
    company_name: str
    as_of_date: str
    user_query: str
    company_row: Dict[str, Any]
    screening_result: Dict[str, Any]
    raw_chunks: List[DisclosureChunk]
    validated_chunks: List[DisclosureChunk]
    evidence_check: EvidenceCheckResult
    explanation: str
    explanation_source: str
    citations: List[str]
    auditor: HarnessAuditor
    is_terminated: bool
    error_message: Optional[str]


def verify_company_node(state: PipelineState) -> PipelineState:
    """[1단계: 기업 확인] 종목명으로 상장 기업을 조회하고 기존 ML/DL 위험 진단 결과를 획득합니다.

    설계 이유:
    존재하지 않는 종목이나 비상장 기업에 대한 불필요한 검색 및 추론 낭비를 방지하고,
    기존의 검증된 ML/DL 위험 점수를 기준 지표로 확보하기 위함입니다.
    """
    auditor = state.get("auditor") or HarnessAuditor()
    state["auditor"] = auditor
    name = state["company_name"].strip()

    try:
        company_series = find_company(name)
        company_row = company_series.to_dict()
        screening_res = screen(name)

        state["company_row"] = company_row
        state["screening_result"] = screening_res

        # as_of_date 미지정 시 데이터의 기준일자(bas_dt) 자동 설정
        if not state.get("as_of_date"):
            state["as_of_date"] = str(company_row.get("bas_dt", screening_res.get("bas_dt", "20261010")))

        auditor.record_step(
            "1_기업확인",
            True,
            f"종목 조회 완료: {company_row.get('item_name')} ({company_row.get('stock_code')}), 기준일:{state['as_of_date']}"
        )
    except Exception as exc:
        state["is_terminated"] = True
        state["error_message"] = f"기업 조회 실패: {str(exc)}"
        auditor.record_step("1_기업확인", False, f"기업 조회 실패: {str(exc)}")

    return state


def search_disclosures_node(state: PipelineState) -> PipelineState:
    """[2단계: 공시 검색] 대상 기업의 종목코드와 기준일자 필터를 적용하여 공시 문서를 검색합니다.

    설계 이유:
    무차별적 검색이 아니라, 분석 대상 회사의 식별자(stock_code)와 시점(as_of_date)을
    1차 필터로 전달하여 안전한 하이브리드 검색을 수행합니다.
    """
    if state.get("is_terminated"):
        return state

    auditor = state["auditor"]
    company_row = state["company_row"]
    stock_code = str(company_row.get("stock_code", ""))
    as_of_date = str(state["as_of_date"])

    search_filter = SearchFilter(stock_code=stock_code, as_of_date=as_of_date)
    query_text = state.get("user_query") or "재무 위험 감자 영업정지 부도 결손 현금배당"

    results = search_disclosures_with_filter(
        query_text=query_text,
        search_filter=search_filter,
        top_k=5,
    )
    raw_chunks = [item.chunk for item in results]
    state["raw_chunks"] = raw_chunks

    auditor.record_step(
        "2_공시검색",
        True,
        f"필터 검색 완료: {len(raw_chunks)}개 공시 청크 추출됨"
    )
    return state


def validate_period_node(state: PipelineState) -> PipelineState:
    """[3단계: 시점/타사 검증] Harness 가드레일을 적용하여 타사 공시 및 미래 공시를 배제합니다.

    설계 이유:
    [필수 가드레일] 2단계 검색 결과를 런타임 하네스에서 재검증하여,
    타사 종목이나 분석 기준일 이후 자료가 단 하나라도 섞이지 않도록 방어막을 구축합니다.
    """
    if state.get("is_terminated"):
        return state

    auditor = state["auditor"]
    raw_chunks = state.get("raw_chunks", [])
    target_stock_code = str(state["company_row"].get("stock_code", ""))
    as_of_date = str(state["as_of_date"])

    # 1. 타사 공시 혼입 차단
    isolated_chunks, _ = validate_company_isolation(raw_chunks, target_stock_code, auditor)

    # 2. 기준일 이후 미래 공시 차단
    time_validated_chunks, _ = validate_lookahead_bias(isolated_chunks, as_of_date, auditor)

    state["validated_chunks"] = time_validated_chunks
    auditor.record_step(
        "3_기간_및_식별자_검증",
        True,
        f"가드레일 검증 완료: 최종 {len(time_validated_chunks)}개 유효 공시 확정"
    )
    return state


def check_evidence_node(state: PipelineState) -> PipelineState:
    """[4단계: 근거 확인] 기존 ML/DL 위험 점수와 검증된 공시 청크 간의 인과적 근거를 대조합니다.

    설계 이유:
    통계 모델 점수가 실제 공시로 증명되는지 확인하고,
    공시상 부도/파산 사실이 없는데 임의로 단정하는 환각을 원천 차단합니다.
    """
    if state.get("is_terminated"):
        return state

    auditor = state["auditor"]
    company_row = state["company_row"]
    screening_res = state["screening_result"]
    valid_chunks = state.get("validated_chunks", [])

    evidence_result = check_financial_evidence(company_row, screening_res, valid_chunks)
    state["evidence_check"] = evidence_result

    auditor.record_step(
        "4_근거확인",
        True,
        f"근거 대조 완료: 일치율 {evidence_result.match_rate * 100:.1f}%, 근거없는 부도확정 방지 상태 통과"
    )
    return state


def generate_explanation_node(state: PipelineState) -> PipelineState:
    """[5단계: 설명 생성] 검증된 공시 사실과 출처 인용을 결합하여 최종 RAG 설명문을 작성합니다.

    설계 이유:
    출처가 명시된 신뢰할 수 있는 최종 보고서 문장을 완성하고,
    위험 단어 사후 검역을 통과한 안전한 결과만을 사용자에게 제공합니다.
    """
    if state.get("is_terminated"):
        return state

    auditor = state["auditor"]
    company_row = state["company_row"]
    screening_res = state["screening_result"]
    evidence_res = state["evidence_check"]
    valid_chunks = state.get("validated_chunks", [])
    user_query = state.get("user_query", "")

    explanation, source, citations = generate_rag_explanation(
        company=company_row,
        screening_result=screening_res,
        evidence_check=evidence_res,
        chunks=valid_chunks,
        user_query=user_query,
    )

    state["explanation"] = explanation
    state["explanation_source"] = source
    state["citations"] = citations

    auditor.record_step(
        "5_설명생성",
        True,
        f"최종 설명문 생성 완료 (출처: {source}, 인용 공시 {len(citations)}건)"
    )
    return state


class LightStateGraph:
    """LangGraph 미설치 환경에서도 동일한 노드 실행, 상태 전이, 분기를 지원하는 경량 그래프 엔진.

    설계 이유:
    LangGraph 라이브러리 추가 설치(requirements 수정)를 금지하는 개발 제약 규칙을 준수하면서도,
    LangGraph의 핵심 철학인 노드(Node), 엣지(Edge), 조건부 분기(Conditional Edge)를
    순수 파이썬으로 동일하게 재현하기 위함입니다.
    """

    def __init__(self):
        self.nodes: Dict[str, Callable[[PipelineState], PipelineState]] = {}
        self.edges: Dict[str, str] = {}
        self.conditional_edges: Dict[str, Tuple[Callable[[PipelineState], str], Dict[str, str]]] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, func: Callable[[PipelineState], PipelineState]) -> None:
        self.nodes[name] = func

    def set_entry_point(self, name: str) -> None:
        self.entry_point = name

    def add_edge(self, from_node: str, to_node: str) -> None:
        self.edges[from_node] = to_node

    def add_conditional_edges(
        self,
        source: str,
        path: Callable[[PipelineState], str],
        path_map: Dict[str, str]
    ) -> None:
        self.conditional_edges[source] = (path, path_map)

    def invoke(self, initial_state: PipelineState) -> PipelineState:
        """그래프 진입점부터 종료점(END)까지 노드를 순차 실행합니다."""
        curr = self.entry_point
        state = initial_state

        while curr and curr != "END":
            node_func = self.nodes.get(curr)
            if not node_func:
                break
            state = node_func(state)

            # 조기 종료 조건 검사
            if state.get("is_terminated"):
                break

            # 조건부 엣지 확인
            if curr in self.conditional_edges:
                route_func, path_map = self.conditional_edges[curr]
                target_key = route_func(state)
                curr = path_map.get(target_key, "END")
            else:
                curr = self.edges.get(curr, "END")

        return state


def build_orchestration_graph() -> Any:
    """LangGraph 기반 파이프라인 그래프를 구축하고 컴파일합니다.

    설계 이유:
    langgraph 패키지가 설치되어 있으면 공식 StateGraph를 사용하고,
    미설치 시 LightStateGraph를 사용하여 환경 의존성 없이 항상 동작하도록 합니다.
    """
    try:
        from langgraph.graph import StateGraph, END  # type: ignore

        workflow = StateGraph(PipelineState)
        workflow.add_node("verify_company", verify_company_node)
        workflow.add_node("search_disclosures", search_disclosures_node)
        workflow.add_node("validate_period", validate_period_node)
        workflow.add_node("check_evidence", check_evidence_node)
        workflow.add_node("generate_explanation", generate_explanation_node)

        workflow.set_entry_point("verify_company")

        def route_after_verify(state: PipelineState) -> str:
            return "end" if state.get("is_terminated") else "continue"

        workflow.add_conditional_edges(
            "verify_company",
            route_after_verify,
            {"end": END, "continue": "search_disclosures"}
        )
        workflow.add_edge("search_disclosures", "validate_period")
        workflow.add_edge("validate_period", "check_evidence")
        workflow.add_edge("check_evidence", "generate_explanation")
        workflow.add_edge("generate_explanation", END)

        return workflow.compile()
    except ImportError:
        # LangGraph 패키지 미설치 시 경량 그래프 엔진으로 완벽 폴백
        graph = LightStateGraph()
        graph.add_node("verify_company", verify_company_node)
        graph.add_node("search_disclosures", search_disclosures_node)
        graph.add_node("validate_period", validate_period_node)
        graph.add_node("check_evidence", check_evidence_node)
        graph.add_node("generate_explanation", generate_explanation_node)

        graph.set_entry_point("verify_company")

        def route_after_verify_fallback(state: PipelineState) -> str:
            return "end" if state.get("is_terminated") else "continue"

        graph.add_conditional_edges(
            "verify_company",
            route_after_verify_fallback,
            {"end": "END", "continue": "search_disclosures"}
        )
        graph.add_edge("search_disclosures", "validate_period")
        graph.add_edge("validate_period", "check_evidence")
        graph.add_edge("check_evidence", "generate_explanation")
        graph.add_edge("generate_explanation", "END")

        return graph


def run_disclosure_rag(
    company_name: str,
    as_of_date: Optional[str] = None,
    user_query: Optional[str] = None
) -> RAGExplanationResponse:
    """기업 위험도 진단 및 공시 근거 설명 파이프라인의 전체 오케스트레이션을 실행합니다.

    설계 이유:
    외부 API(FastAPI 라우터)나 백엔드 서비스에서 단일 함수 호출로
    전체 RAG 워크플로우를 가드레일 하에 실행하고 정형화된 응답을 얻을 수 있는 통합 진입점입니다.
    """
    auditor = HarnessAuditor()
    initial_state: PipelineState = {
        "company_name": company_name,
        "as_of_date": as_of_date or "",
        "user_query": user_query or "",
        "auditor": auditor,
        "is_terminated": False,
        "error_message": None,
    }

    graph = build_orchestration_graph()
    final_state = graph.invoke(initial_state)

    if final_state.get("is_terminated"):
        err_msg = final_state.get("error_message", "알 수 없는 이유로 분석이 중단되었습니다.")
        raise ValueError(err_msg)

    company_row = final_state["company_row"]
    screening_res = final_state["screening_result"]
    evidence_res = final_state["evidence_check"]

    return RAGExplanationResponse(
        company_name=str(company_row.get("item_name", company_name)),
        corp_name=str(company_row.get("corp_name", "")),
        stock_code=str(company_row.get("stock_code", "")),
        as_of_date=str(final_state.get("as_of_date", "")),
        ml_score=float(screening_res.get("ml_score", 0.0)),
        dl_score=float(screening_res.get("dl_score", 0.0)),
        score=float(screening_res.get("score", 0.0)),
        grade=str(screening_res.get("grade", "stable")),
        explanation=final_state.get("explanation", ""),
        explanation_source=final_state.get("explanation_source", "rag_basic"),
        citations=final_state.get("citations", []),
        evidence_items=evidence_res.evidence_items,
        guardrail_status=auditor.guardrail_results,
        audit_trace=auditor.logs,
    )
