# RAG재무근거검증 코드검증

- 범위: ALH-0564 ~ ALH-0587
- 대상: `ai/src/features/disclosure_rag_001/financial_evidence/service.py`
- 방법: 소스 대조. `extract_risk_factors`, `find_matching_chunk_for_factor`, `check_financial_evidence`의 분기로 판정했다.
- 판정: 통과 20, 실패 3, 부분 1, 확인불가 0

## 실패·부분

- ALH-0579 실패. `find_matching_chunk_for_factor`는 본문 키워드만 본다. `company_data`의 종목코드로 타사 청크를 빼지 않는다.
- ALH-0580 실패. 청크 `rcept_dt`와 기준일을 비교하지 않는다. 목록에 들어온 미래 공시의 키워드도 근거가 된다.
- ALH-0582 실패. `has_unfounded_claims`는 처음부터 `False`이고, `default_count == 0` 분기도 다시 `False`를 넣는다. 근거 없는 파산을 참으로 잡는 경로가 없다.
- ALH-0587 부분. 위험 요인이 있는데 청크가 비면 항목 `caveat`가 붙는다. 요인이 없으면 빈 코퍼스여도 고지 없이 `match_rate`는 1.0이다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0564 | P0 | reduction_count: 근거 있음 | 통과 | `reduction_count > 0`이면 키워드에 `감자`가 있다. 본문에 있으면 `has_confirmed_evidence=True`와 citation, excerpt를 반환한다. |
| ALH-0565 | P0 | reduction_count: 근거 없음 | 통과 | 감자·자본감소·무상감자·유상감자·결손금이 모두 없으면 `False`와 `caveat` 문장을 반환한다. |
| ALH-0566 | P0 | suspend_count: 근거 있음 | 통과 | `suspend_count > 0`의 키워드에 `영업정지`가 있고, 포함되면 근거 있음과 인용·발췌를 만든다. |
| ALH-0567 | P0 | suspend_count: 근거 없음 | 통과 | 영업정지·생산중단·가동 중단·설비 보수가 없으면 `False`와 caveat다. |
| ALH-0568 | P0 | rehab_count: 근거 있음 | 통과 | `rehab_count > 0`의 키워드에 `회생절차`가 있다. 본문 일치 시 근거를 확정한다. |
| ALH-0569 | P0 | rehab_count: 근거 없음 | 통과 | 회생절차·법정관리·개시신청이 없으면 근거 없음과 caveat다. |
| ALH-0570 | P0 | default_count: 근거 있음 | 통과 | `default_count > 0`의 키워드에 `부도`가 있다. 포함되면 citation과 excerpt를 채운다. |
| ALH-0571 | P0 | default_count: 근거 없음 | 통과 | 부도·어음부도·당좌거래정지가 없으면 `False`와 caveat다. |
| ALH-0572 | P0 | net_profit: 근거 있음 | 통과 | `net_profit < 0`이면 키워드에 `당기순손실`이 있다. 본문에 있으면 근거를 확정한다. |
| ALH-0573 | P0 | net_profit: 근거 없음 | 통과 | 당기순손실·영업손실·적자·결손이 없으면 근거 없음과 caveat다. |
| ALH-0574 | P0 | score: 근거 있음 | 통과 | `score >= 40` 또는 등급이 warning·danger면 키워드에 `불확실성`이 있다. 포함되면 근거를 확정한다. |
| ALH-0575 | P0 | score: 근거 없음 | 통과 | 불확실성·지속·자본잠식·의견·주의가 모두 없으면 `False`와 caveat다. |
| ALH-0576 | P1 | 근거 매치율 0/0 | 통과 | `factors`가 비면 `match_rate`를 1.0으로 둔다. 0으로 나누지 않는다. |
| ALH-0577 | P1 | 근거 매치율 1/2 | 통과 | `confirmed_count / len(factors)`다. 2개 중 1개 확인이면 0.5다. |
| ALH-0578 | P1 | 근거 매치율 3/3 | 통과 | 3개 모두 확인이면 `3/3`이라 `match_rate`는 1.0이다. |
| ALH-0579 | P1 | 타사 동일 키워드 | 실패 | 매칭 루프가 `chunk.stock_code`를 보지 않는다. 타사 부도 문장도 대상 기업 근거가 된다. |
| ALH-0580 | P1 | 미래 공시 동일 키워드 | 실패 | `as_of_date`는 결과 필드에만 복사된다. 기준일 이후 청크의 회생 문구도 매칭된다. |
| ALH-0581 | P1 | 부도 0건 | 통과 | `default_count`가 0이면 `extract_risk_factors`가 부도 요인을 만들지 않아 부도 확정 지표를 내지 않는다. |
| ALH-0582 | P1 | 근거 없는 파산 | 실패 | 정보 없음이어도 `has_unfounded_claims`를 참으로 세울 코드가 없다. 조건 안에서도 `False`만 대입한다. |
| ALH-0583 | P1 | 공시 일자 인용 | 통과 | citation 형식은 `[보고서명, 공시일:접수일, 법인명]`이라 `report_name`, `rcept_dt`, `corp_name`이 들어간다. |
| ALH-0584 | P1 | 본문 180자 발췌 | 통과 | `content[:180]` 뒤에 길이가 180을 넘으면 `...`를 붙인다. 200자면 180자와 말줄임이다. |
| ALH-0585 | P1 | 재무수치 0원 | 통과 | 당기순손실 요인은 `net_profit < 0`일 때만 만든다. 0은 적자 요인이 아니다. |
| ALH-0586 | P1 | 음수 순이익 | 통과 | `net_profit=-1`은 0보다 작아 `당기순손실 발생` 요인을 추가한다. |
| ALH-0587 | P1 | 실제 확인 불가 공시 | 부분 | 빈 청크로 키워드가 안 맞으면 caveat가 있다. 위험 요인이 없는 빈 코퍼스는 불확실성 고지를 만들지 않는다. |
