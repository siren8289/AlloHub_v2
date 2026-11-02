# RAG평가지표 코드검증

- 범위: ALH-0648 ~ ALH-0674
- 대상: `ai/src/features/disclosure_rag_001/harness/runtime.py`의 `compute_recall_at_k`, `compute_citation_accuracy`, `compute_company_id_match_rate`, `compute_point_in_time_accuracy`, `compute_faithfulness_score`, `run_evaluation`
- 방법: 소스 대조. 분모가 0일 때의 반환과 비율 식을 케이스 기대와 비교했다.
- 판정: 통과 23, 실패 0, 부분 4, 확인불가 0

## 실패·부분

- ALH-0668 부분. `compute_recall_at_k`는 정답 집합 대비 상위 k 포함 비율이다. `run_evaluation`은 정답을 안 주면 검색된 id를 정답으로 써서, 청크가 3개 이하면 항상 1.0이다.
- ALH-0671 부분. 미래 1건이 섞이면 `compute_point_in_time_accuracy`는 1.0보다 작다. 원인 문장이나 필드는 없다.
- ALH-0673 부분. faithfulness는 넘겨준 `score` 문자열이 설명에 있는지만 본다. 기준일 점수를 다시 계산하지 않는다.
- ALH-0674 부분. `company_id_match_rate`가 1 미만이면 숫자로 보인다. 미달을 위험으로 적는 필드나 문구는 없다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0648 | P1 | recall_at_k 완전일치 | 통과 | 정답 id가 상위 k에 모두 있으면 `matched / len(ground_truth)`가 1.0이다. 값은 0과 1 사이다. |
| ALH-0649 | P1 | recall_at_k 절반일치 | 통과 | 정답 절반만 상위 k에 있으면 비율은 0.5다. 분모는 정답 개수다. |
| ALH-0650 | P1 | recall_at_k 불일치 | 통과 | 상위 k와 정답이 겹치지 않으면 0.0이다. |
| ALH-0651 | P1 | recall_at_k 빈 문서 | 통과 | `ground_truth_chunk_ids`가 비면 나누지 않고 1.0을 반환한다. |
| ALH-0652 | P1 | citation_accuracy 완전일치 | 통과 | 설명의 `[...]`가 유효 인용과 맞으면 `correct_count / len(found_cites)`가 1.0이다. |
| ALH-0653 | P1 | citation_accuracy 절반일치 | 통과 | 추출된 인용 절반만 유효 목록과 맞으면 0.5다. |
| ALH-0654 | P1 | citation_accuracy 불일치 | 통과 | 추출된 인용이 유효 목록과 하나도 안 맞으면 0.0이다. |
| ALH-0655 | P1 | citation_accuracy 빈 문서 | 통과 | `valid_citations`가 비면 1.0이다. 분모 0을 1.0으로 두는 다른 지표와 같다. |
| ALH-0656 | P0 | company_id_match_rate 완전일치 | 통과 | 모든 청크의 `stock_code`가 대상과 같으면 1.0이다. 타사 청크는 분자에 안 들어간다. |
| ALH-0657 | P0 | company_id_match_rate 절반일치 | 통과 | 절반만 대상 종목이면 `matches / len(chunks)`가 0.5다. 타사는 0으로 센다. |
| ALH-0658 | P0 | company_id_match_rate 불일치 | 통과 | 전부 다른 종목이면 0.0이다. |
| ALH-0659 | P0 | company_id_match_rate 빈 문서 | 통과 | 청크가 없으면 1.0이다. 0으로 나누지 않는다. |
| ALH-0660 | P0 | point_in_time_accuracy 완전일치 | 통과 | 모든 `rcept_dt <= as_of_date`이면 1.0이다. |
| ALH-0661 | P0 | point_in_time_accuracy 절반일치 | 통과 | 미래 일자가 절반이면 유효 비율은 0.5다. 미래 행은 분자에 포함되지 않는다. |
| ALH-0662 | P0 | point_in_time_accuracy 불일치 | 통과 | 전부 기준일 이후이면 0.0이다. |
| ALH-0663 | P0 | point_in_time_accuracy 빈 문서 | 통과 | 청크가 없으면 1.0이다. |
| ALH-0664 | P1 | faithfulness_score 완전일치 | 통과 | 점수와 회사명이 설명에 있고, 설명의 위험 단어가 청크에도 있으면 `passed_checks / total_checks`가 1.0이다. |
| ALH-0665 | P1 | faithfulness_score 절반일치 | 통과 | 검사 절반만 통과하면 0.5다. 각 검사는 0 또는 1로만 더한다. |
| ALH-0666 | P1 | faithfulness_score 불일치 | 통과 | 점수·회사명·위험 단어 검사가 모두 실패하면 0.0이다. |
| ALH-0667 | P1 | faithfulness_score 빈 문서 | 통과 | 점수와 회사명이 비어 위험 단어도 없으면 `total_checks == 0`이라 1.0이다. |
| ALH-0668 | P1 | 공시 Recall@K | 부분 | 함수는 상위 3개와 정답의 교집합을 정답 수로 나눈다. 평가 호출이 정답을 검색 결과로 대체하면 별도 target 3건의 회수율이 아니다. |
| ALH-0669 | P1 | Citation Accuracy | 통과 | 본문에서 찾은 인용 3개 중 2개가 유효하면 `round(2/3, 4)`라 0.6667이다. |
| ALH-0670 | P1 | 기업 ID 완전 일치 | 통과 | `compute_company_id_match_rate`는 대상과 같은 청크 비율이다. 전부 같으면 1.0이다. |
| ALH-0671 | P1 | 시점 정확도 | 부분 | 3건 중 미래 1건이면 `2/3`이라 1.0 미만이다. `EvaluationMetrics`에는 원인 필드가 없다. |
| ALH-0672 | P1 | Faithfulness 근거 충실 | 통과 | 지원되는 문장만 있으면 점수·회사명·청크 단어 검사가 통과해 1.0이 된다. |
| ALH-0673 | P1 | 모의 스크리닝 점수 | 부분 | `str(screening_result["score"]) in explanation`만 검사한다. 분석 기준일의 실제 점수와 맞추는 계산은 없다. |
| ALH-0674 | P1 | 목표치 미달 보고 | 부분 | 회사 일치율이 1보다 작으면 그 실수가 반환된다. 위험 문구로 다시 표현하지는 않는다. |
