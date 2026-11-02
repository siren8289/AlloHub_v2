# RAG전용API 코드검증

- 범위: ALH-0675 ~ ALH-0686
- 대상: `ai/src/features/disclosure_rag_001/router.py`, `schemas.py`의 `RAGExplanationRequest`와 `SearchQuery`, `main.py`의 라우터 등록
- 방법: 소스 대조. 422는 Pydantic 필드 제약, 404는 `ValueError`를 라우터가 바꾸는 경로로 보았다. TestClient는 실행하지 않았다.
- 판정: 통과 7, 실패 4, 부분 1, 확인불가 0

## 실패·부분

- ALH-0682 실패. `as_of_date`는 선택 문자열이다. `20260231`은 달력 검증 없이 explain까지 들어가 4xx가 아니다.
- ALH-0683 실패. `2026-10-10`도 패턴 검사가 없어 422가 아니다.
- ALH-0684 실패. `20269999`도 같은 필드라 길이·숫자 8자리만 통과하고 날짜로는 거절되지 않는다.
- ALH-0685 실패. `user_query`에 `max_length`가 없다. 100자이든 그 이상이든 길이 때문에 4xx가 되지 않는다.
- ALH-0686 부분. `company_name`은 `max_length=100`이라 이 100자는 422가 아니다. 없는 이름이면 explain은 `ValueError`를 404로 바꾼다. 길이 초과는 101자부터다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0675 | P1 | POST /api/v1/disclosure/explain | 통과 | `explain_disclosure_risk_api`가 `run_disclosure_rag`의 `RAGExplanationResponse`를 반환한다. 그 모델에 `citations`, `guardrail_status`, `audit_trace`가 있다. `main.py`가 이 라우터를 포함한다. |
| ALH-0676 | P1 | POST /api/v1/disclosure/explain | 통과 | `company_name`은 `min_length=1`이다. `""`는 핸들러 전에 422다. |
| ALH-0677 | P1 | POST /api/v1/disclosure/explain | 통과 | 없는 종목은 `find_company`가 실패하고 워크플로가 `ValueError`를 낸다. explain은 그 예외를 404로 바꾼다. |
| ALH-0678 | P1 | POST /api/v1/disclosure/search | 통과 | `search_disclosures_api`의 `response_model`은 `SearchResultChunk` 목록이다. 필터가 있으면 `search_disclosures` 결과를 200으로 반환한다. |
| ALH-0679 | P0 | POST /api/v1/disclosure/search | 통과 | `SearchQuery.filter`는 기본값이 없는 필수 필드다. `query_text`만 있으면 422다. |
| ALH-0680 | P1 | POST /api/v1/disclosure/evaluate | 통과 | `evaluate_rag_pipeline_api`가 `run_evaluation`의 `EvaluationMetrics`를 반환한다. 필드는 recall, citation, company, point-in-time, faithfulness 다섯이다. |
| ALH-0681 | P1 | POST /api/v1/disclosure/evaluate | 통과 | evaluate도 `RAGExplanationRequest`를 쓴다. 빈 `company_name`은 422다. |
| ALH-0682 | P0 | as_of_date: 20260231 | 실패 | `RAGExplanationRequest.as_of_date`에 `pattern`이나 날짜 파서가 없다. 2월 31일은 4xx로 막히지 않는다. |
| ALH-0683 | P0 | as_of_date: 2026-10-10 | 실패 | `YYYY-MM-DD`를 거절하는 제약이 없다. 설명 API는 이 문자열을 기준일로 받는다. |
| ALH-0684 | P0 | as_of_date: 20269999 | 실패 | `20269999`도 문자열로 유효하다. 월·일 범위 검사와 4xx가 없다. |
| ALH-0685 | P1 | user_query: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA | 실패 | 입력 질의는 100자이고 필드에는 상한이 없다. 길이 검증으로 4xx를 반환하지 않는다. |
| ALH-0686 | P1 | company_name: AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA | 부분 | 100자는 `max_length=100` 안이라 길이 422가 아니다. 미등록 이름이라 조회 실패 시 404다. |
