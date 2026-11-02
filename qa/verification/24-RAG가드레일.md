# RAG가드레일 코드검증

- 범위: ALH-0627 ~ ALH-0647
- 대상: `ai/src/features/disclosure_rag_001/harness/runtime.py`
- 방법: 소스 대조. `validate_company_isolation`, `validate_lookahead_bias`, `enforce_read_only_query`, `execute_with_retry`, `HarnessAuditor`를 분기별로 따라갔다.
- 판정: 통과 18, 실패 2, 부분 1, 확인불가 0

## 실패·부분

- ALH-0634 실패. `validate_lookahead_bias`는 `YYYYMMDD`만 받는 검사가 없다. `2026-10-10`은 문자열 비교라 같은 해의 `20261010`보다 작다고 판정될 수 있다.
- ALH-0645 실패. 하네스에는 설명문의 `부도 확정`을 보는 함수가 없다. `unfounded_claims_blocked`는 초기 `True`에서 바뀌지 않는다.
- ALH-0647 부분. 미래 청크는 반환 목록에서 빠진다. 그러나 하나라도 있었으면 `lookahead_blocked`는 `False`다. 이름은 차단인데 값은 검증 실패라 출력에 미래 자료가 남았다는 뜻과 다르다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0627 | P1 | 회사 격리 정상 | 통과 | `validate_company_isolation`은 `chunk.stock_code == target_stock_code`인 청크만 남긴다. 전부 `A000040`이면 개수가 그대로다. |
| ALH-0628 | P1 | 회사 격리 혼합 | 통과 | `A000020`은 같지 않아 `valid_chunks`에서 빠지고 `has_leakage`가 참이 된다. |
| ALH-0629 | P1 | 회사 격리 전체 타사 | 통과 | 전부 다른 종목이면 빈 목록과 `passed=False`를 반환한다. 감사가 있으면 타사 배제 WARNING을 남긴다. |
| ALH-0630 | P1 | 회사 격리 감사 | 통과 | 위반 청크마다 `record_step(..., False, ...)`이라 로그 상태가 `WARNING`이다. `company_isolation`도 `False`가 된다. |
| ALH-0631 | P1 | 시점 정상 | 통과 | `validate_lookahead_bias`는 `str(rcept_dt) <= str(as_of_date)`인 청크를 유지한다. |
| ALH-0632 | P1 | 시점 경계일 | 통과 | 같은 날짜는 `<=`라 유지된다. 미래로 보지 않는다. |
| ALH-0633 | P1 | 미래 공시 차단 | 통과 | `rcept_dt`가 기준일보다 크면 목록에서 제외하고, 감사가 있으면 차단 로그를 남긴다. |
| ALH-0634 | P1 | 다른 형식 날짜 | 실패 | `2026-10-10` 형식 검증이 없다. 하이픈과 숫자 문자열을 그대로 비교한다. |
| ALH-0635 | P1 | 문자열 날짜 비교 | 통과 | 둘 다 8자리 `YYYYMMDD`면 문자열 비교가 날짜 순서와 같다. `<=`가 기준일 이전과 당일을 유지한다. |
| ALH-0636 | P1 | readonly SELECT | 통과 | `enforce_read_only_query`는 금지 단어가 없으면 `True`다. `SELECT`만 있는 문은 허용된다. |
| ALH-0637 | P1 | readonly DROP | 통과 | 소문자로 바꾼 뒤 `\\bdrop\\b`가 있으면 `False`다. `DROP TABLE`은 거부된다. |
| ALH-0638 | P1 | readonly INSERT | 통과 | `insert`가 단어 경계로 있으면 `False`다. |
| ALH-0639 | P1 | readonly UPDATE | 통과 | `update`가 단어 경계로 있으면 `False`다. |
| ALH-0640 | P1 | SQL 주석 뒤 INSERT | 통과 | 주석을 지우지는 않지만 문자열 전체에서 `insert`를 찾는다. 줄바꿈 뒤 `INSERT`도 거부된다. |
| ALH-0641 | P1 | 재시도 성공 | 통과 | `execute_with_retry`는 예외 전에 성공한 반환값을 바로 돌려준다. 첫 실패 다음 성공이면 그 결과다. |
| ALH-0642 | P1 | 재시도 모두 실패 | 통과 | 기본 `max_retries=3`이 모두 실패하면 마지막 예외를 담은 `RuntimeError`를 올린다. |
| ALH-0643 | P1 | 감사 초기 상태 | 통과 | `HarnessAuditor()`의 `guardrail_results`에 `company_isolation`, `lookahead_blocked`, `read_only_enforced`, `unfounded_claims_blocked`가 있고 처음에는 모두 `True`다. |
| ALH-0644 | P1 | 감사 단계 기록 | 통과 | `record_step`이 호출될 때마다 `logs`에 한 줄이 쌓인다. 두 번 호출하면 두 줄이다. |
| ALH-0645 | P1 | 모델 출력 부도 확정 | 실패 | 런타임은 모델 문장을 받지 않는다. 근거 없는 `부도 확정`을 차단하거나 플래그를 내리지 않는다. |
| ALH-0646 | P1 | 기업 미매칭 | 통과 | 다른 `stock_code`가 있으면 `mark_guardrail("company_isolation", False)`와 WARNING 로그로 격리 실패를 기록한다. |
| ALH-0647 | P1 | 미래 유출 | 부분 | 미래 행은 제거되지만 `lookahead_blocked`는 유출을 봤을 때 `False`다. 차단 성공과 가드레일 통과가 한 값에 겹친다. |
