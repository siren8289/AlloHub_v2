# RAG문서청킹 코드검증

- 범위: ALH-0505 ~ ALH-0521
- 대상: `ai/src/features/disclosure_rag_001/disclosure_knowledge/service.py`, 코사인 쪽은 `disclosure_search/service.py`의 `calculate_cosine_similarity`
- 방법: 소스 대조. `ai/tests/test_disclosure_rag.py`는 읽었고, 이 환경에는 pydantic이 없어 pytest는 실행하지 않았다.
- 판정: 통과 15, 실패 2, 부분 0, 확인불가 0

## 실패·부분

- ALH-0514 실패. `split_text_into_chunks`는 `chunk_overlap >= chunk_size`를 거절하지 않는다. 본문이 `chunk_size`보다 길면 `start`가 0만큼만 증가해 무한 루프다.
- ALH-0520 실패. 오프라인 임베딩은 512차원이고 Gemini 응답 차원은 맞추지 않는다. `calculate_cosine_similarity`는 길이가 다르면 `np.dot`에서 예외가 나고, 막는 정책이 없다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0505 | P1 | 기본 문서 목록 | 통과 | `get_default_disclosure_documents`가 KR모터스(주), 동화약품(주), 삼성전자(주) 문서를 나눠 반환한다. |
| ALH-0506 | P1 | 타사 문서 포함 | 통과 | 원본 `stock_code`는 `A000040`, `A000020`, `A005930`이고 `chunk_document`가 그 값을 청크에 그대로 복사한다. |
| ALH-0507 | P1 | 미래 공시 테스트 원본 | 통과 | `DOC_KR_20261115_FUTURE`의 `rcept_dt`는 `20261115`다. 검색은 `str(chunk.rcept_dt) > str(as_of_date)`이면 그 청크를 뺀다. |
| ALH-0508 | P1 | 짧은 문서 청킹 | 통과 | `split_text_into_chunks`는 정규화 길이가 `chunk_size` 이하면 청크 하나를 반환한다. 100자와 size 250은 1청크다. |
| ALH-0509 | P1 | 긴 문서 청킹 | 통과 | 600자, size 250, overlap 50이면 시작점이 0, 200, 400이라 50자씩 겹치고 0부터 끝까지 빠지지 않는다. |
| ALH-0510 | P1 | chunk_id 생성 | 통과 | `chunk_document`가 `f"{doc.doc_id}_C{index + 1}"`을 쓴다. `DOC_KR_..._C1`, `_C2`처럼 문서 안에서 유일하다. |
| ALH-0511 | P1 | 청크 메타데이터 | 통과 | `corp_code`, `stock_code`, `rcept_dt`, 보고서명, 섹션을 원본 `DisclosureDocument`에서 복사한다. |
| ALH-0512 | P1 | 텍스트 공백 정리 | 통과 | `" ".join(text.split())`이 탭, 개행, 연속 공백을 공백 하나로 만든다. |
| ALH-0513 | P1 | 빈 문서 | 통과 | 빈 문자열은 길이 0이라 예외 없이 `[""]` 한 청크로 반환된다. 빈 결과 또는 안전한 처리에 해당한다. |
| ALH-0514 | P1 | overlap>=chunk_size | 실패 | size 50, overlap 50이면 `start += 0`이다. 긴 본문은 같은 위치를 반복하고 입력 오류를 내지 않는다. |
| ALH-0515 | P1 | 오프라인 임베딩 | 통과 | 키가 없으면 `compute_fallback_embedding`이 `HashingVectorizer(n_features=512, norm="l2")` 실수 벡터를 만든다. |
| ALH-0516 | P1 | 동일 문자열 임베딩 | 통과 | 해싱 벡터라이저에 난수 상태가 없다. 같은 문자열은 같은 512차원 벡터다. |
| ALH-0517 | P1 | 벡터 0 처분 | 통과 | 빈 문자열도 `embed_text`가 예외 없이 폴백을 호출한다. 영벡터의 코사인은 검색 쪽에서 0.0으로 막는다. |
| ALH-0518 | P1 | Gemini 임베딩 | 통과 | 키가 있고 응답에 `embedding.values` 또는 `embeddings[0].values`가 있으면 그 모델 벡터를 반환한다. |
| ALH-0519 | P1 | Gemini 임베딩 실패 | 통과 | `embed_text`의 `except Exception`이 429와 timeout을 포함한 오류 뒤 `compute_fallback_embedding`으로 내려간다. |
| ALH-0520 | P1 | 임베딩 차원 혼합 | 실패 | 폴백은 512로 고정이고 Gemini 벡터는 길이를 검사하지 않는다. 차원이 다르면 코사인 계산이 예외로 끝난다. |
| ALH-0521 | P1 | 전체 문서 임베딩 | 통과 | `process_and_embed_documents`가 기본 6문서를 청크한 뒤 각 청크의 `embedding`에 `embed_text` 결과를 넣는다. |
