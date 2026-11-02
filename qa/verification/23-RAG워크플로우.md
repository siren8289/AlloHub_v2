# RAG워크플로우 코드검증

- 범위: ALH-0606 ~ ALH-0626
- 대상: `ai/src/features/disclosure_rag_001/orchestration/workflow.py`, 오류 코드는 `router.py`의 `explain_disclosure_risk_api`
- 방법: 소스 대조. 기업 조회 실패와 기준일 분기는 코드 경로로 결정했다.
- 판정: 통과 17, 실패 2, 부분 2, 확인불가 0

## 실패·부분

- ALH-0616 부분. `guardrail_status`의 네 값은 bool이다. 워크플로는 `company_isolation`과 `lookahead_blocked`만 갱신하고, `read_only_enforced`와 `unfounded_claims_blocked`는 검사 없이 초기 `True`다.
- ALH-0621 실패. `user_query`에 최대 길이가 없다. 2000자도 `generate_explanation_node`가 프롬프트에 그대로 넘긴다.
- ALH-0622 부분. `get_search_corpus`만 캐시한다. 워크플로 응답 캐시는 없고 `screen`과 설명 생성은 매번 다시 한다. 오프라인 기본 문장은 같은 입력이면 같다.
- ALH-0625 실패. 모델 파일 없음은 `verify_company_node`가 일반 예외로 삼켜 기업 조회 실패가 된다. 라우터는 그 `ValueError`를 404로 바꾼다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0606 | P1 | 기업 확인 단계 | 통과 | `verify_company_node`가 `find_company`와 `screen`을 호출하고 `company_row`, `screening_result`를 상태에 넣는다. |
| ALH-0607 | P1 | 기업 조회 실패 조기 종료 | 통과 | 조회 예외면 `is_terminated`가 참이다. `LightStateGraph.invoke`는 그 뒤 노드를 실행하지 않고, LangGraph 분기도 `END`로 간다. |
| ALH-0608 | P1 | 기준일 미지정 | 통과 | `as_of_date`가 비면 회사 `bas_dt`를 쓰고, 없으면 스크리닝 `bas_dt`, 그것도 없으면 `20261010`이다. |
| ALH-0609 | P1 | 기준일 지정 | 통과 | `20261010`처럼 값이 있으면 기본 기준일로 덮지 않고 그 문자열을 검색 필터에 쓴다. |
| ALH-0610 | P1 | 공시 검색 노드 | 통과 | `search_disclosures_node`가 회사 `stock_code`와 기준일로 `search_disclosures_with_filter`를 호출하고 `raw_chunks`에 담는다. |
| ALH-0611 | P1 | 시점 검증 노드 | 통과 | `validate_period_node`가 `validate_lookahead_bias`로 `rcept_dt > as_of_date` 청크를 뺀다. |
| ALH-0612 | P1 | 회사 검증 노드 | 통과 | 같은 노드가 `validate_company_isolation`으로 대상 종목이 아닌 청크를 먼저 뺀다. |
| ALH-0613 | P1 | 근거 확인 노드 | 통과 | `check_evidence_node`가 검증된 청크로 `check_financial_evidence`를 호출해 `evidence_check`를 만든다. |
| ALH-0614 | P1 | 설명 노드 | 통과 | `generate_explanation_node`가 `explanation`, `explanation_source`, `citations`를 상태에 저장한다. |
| ALH-0615 | P1 | 감사 로그 | 통과 | 성공 경로의 다섯 노드가 `record_step`을 호출하고 `run_disclosure_rag`가 `auditor.logs`를 `audit_trace`로 반환한다. |
| ALH-0616 | P1 | guardrail_status | 부분 | 반환 필드는 `auditor.guardrail_results`의 bool이다. 읽기 전용과 근거 없는 주장 키는 워크플로에서 다시 검증되지 않는다. |
| ALH-0617 | P1 | LangGraph 설치됨 | 통과 | `build_orchestration_graph`는 `langgraph.graph.StateGraph` import가 되면 그 그래프를 컴파일한다. |
| ALH-0618 | P1 | LangGraph 미설치 | 통과 | `ImportError`이면 같은 노드와 간선을 `LightStateGraph`에 얹는다. requirements에는 langgraph가 없다. |
| ALH-0619 | P1 | LightStateGraph 분기 | 통과 | 기업 확인 뒤 `is_terminated`면 `invoke`가 루프를 멈추고, 조건부 간선도 `end`를 `END`로 보낸다. |
| ALH-0620 | P1 | 중간 검색 결과 0개 | 통과 | 검색이 비어도 그래프는 한 번씩만 진행한다. 근거 확인과 기본 설명은 빈 청크로 `특이 위험 사유` 문장을 만들 수 있다. |
| ALH-0621 | P1 | 장문 질문 | 실패 | 스키마 `user_query`와 워크플로 모두 2000자를 자르거나 거절하지 않는다. |
| ALH-0622 | P1 | 사용자 재요청 | 부분 | 같은 요청의 공시 코퍼스 임베딩은 재사용된다. 설명 결과 자체를 저장하는 캐시는 없다. |
| ALH-0623 | P1 | 기준일 이전 공시만 | 통과 | 시점 검증을 통과한 청크만 `validated_chunks`가 되고, 인용은 그 목록에서 만든다. |
| ALH-0624 | P1 | ID 불일치 차단 | 통과 | 타사 `stock_code`는 설명 노드 전에 격리된다. 최종 인용은 남은 청크의 회사명으로만 만든다. |
| ALH-0625 | P1 | 워크플로우 예외 | 실패 | `load_ml_model`의 `FileNotFoundError`도 기업 확인의 `except Exception`에 걸린다. explain API는 이를 404로 반환한다. |
| ALH-0626 | P1 | DB 없는 환경 | 통과 | 검색 노드는 `search_disclosures`가 아니라 `search_disclosures_with_filter`만 호출한다. `DATABASE_URL` 없이 메모리 코퍼스를 검색한다. |
