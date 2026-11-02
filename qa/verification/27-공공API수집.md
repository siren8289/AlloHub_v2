# 공공API수집 코드검증

- 범위: ALH-0687 ~ ALH-0712 (26건)
- 대상: `data/etl/fetch.py`, `data/etl/config.py`
- 방법: 소스 대조. `need_key`, `as_list`, `shorten_row`, 페이지 루프, 상장일 탐색은 가짜 응답으로 실행했다. 공개 API는 호출하지 않았다.
- 판정: 통과 22, 실패 1, 부분 3, 확인불가 0

## 실패·부분

- ALH-0703 부분. `response.json()`이 깨지면 예외가 그대로 올라가 파이프라인은 멈춘다. 실패를 남기는 로그 호출은 없다.
- ALH-0710 부분. 정상 `print`에는 인증키가 없다. `raise_for_status`의 HTTPError 문자열에는 요청 URL의 `serviceKey`가 들어간다.
- ALH-0711 부분. 429는 `HTTPError`로 끝난다. 재시도, 대기, 429만 구분하는 보고는 없다. 페이지 사이 `sleep(0.05)`는 성공한 다음 페이지 전에만 있다.
- ALH-0712 실패. 1페이지와 2페이지가 같은 행이어도 `rows.extend`로 그대로 붙인다. 중복 제거나 품질 검사가 없다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0687 | P1 | 인증키 누락 | 통과 | `need_key`는 `SERVICE_KEY`가 비어 있으면 `RuntimeError`를 낸다. 빈 문자열로 실행해 확인했다. |
| ALH-0688 | P1 | API 성공 코드00 | 통과 | `resultCode`가 `"00"`이면 예외 없이 `(rows, totalCount)`를 돌려준다. |
| ALH-0689 | P1 | API 성공 코드000 | 통과 | 성공 코드 집합이 `("00", "000")`이다. `"000"`도 행과 건수를 반환했다. |
| ALH-0690 | P1 | API 실패 코드 | 통과 | `"99"`는 `RuntimeError("API 오류 99: ...")`다. `resultMsg`가 메시지에 포함된다. |
| ALH-0691 | P1 | 한건 응답 | 통과 | `as_list`가 딕셔너리를 길이 1 리스트로 감싼다. |
| ALH-0692 | P1 | 다건 응답 | 통과 | 리스트는 그대로 반환한다. |
| ALH-0693 | P1 | 빈 응답 | 통과 | `item`이 `None`이면 `as_list`가 `[]`이다. 페이지 결과도 빈 목록과 total 0이다. |
| ALH-0694 | P1 | 긴 첨부내용 제거 | 통과 | `DROP_KEYS`의 `rptFileCtt`는 `shorten_row`에서 빠진다. |
| ALH-0695 | P1 | 첨부 경로 제거 | 통과 | `rptFilePthCtt`도 같은 집합에서 제거된다. |
| ALH-0696 | P1 | 텍스트 301자 | 통과 | 300자를 넘으면 `text[:300]`이다. 301자 입력의 결과가 길이 300이었다. |
| ALH-0697 | P1 | 중첩 list 필드 | 통과 | 값이 `list` 또는 `dict`이면 그 키를 건너뛴다. |
| ALH-0698 | P1 | None 원시 필드 | 통과 | `None`은 빈 문자열로 저장한다. 키 자체는 남긴다. |
| ALH-0699 | P1 | 첫 페이지 1000건 | 통과 | 받은 행 수가 `totalCount` 이상이면 다음 페이지를 요청하지 않는다. total 1000에서 호출은 1회였다. |
| ALH-0700 | P1 | 전체 1001건 | 통과 | 1페이지 1000건, total 1001이면 2페이지를 받아 1001건이 된다. |
| ALH-0701 | P1 | 빈 페이지 조기 종료 | 통과 | `page_rows`가 비면 `break`한다. total이 남아 있어도 빈 2페이지에서 멈췄다. |
| ALH-0702 | P1 | API 서버 타임아웃 | 통과 | `requests.get(..., timeout=90)`의 `Timeout`을 삼키지 않는다. `fetch`는 파일을 쓰지 않아 여기서 회사 CSV가 깨지지는 않는다. 재시도는 없다. |
| ALH-0703 | P1 | JSON 포맷 파손 | 부분 | JSON 파싱 예외는 파이프라인을 끝내지만, 실패 로그는 없다. |
| ALH-0704 | P1 | 상장 목록 최근 평일 | 통과 | `recent_weekdays(14)`는 토·일을 빼고 평일 14개를 만든다. 실행 결과에도 주말이 없었다. |
| ALH-0705 | P1 | 상장 목록 total<100 | 통과 | 건수 확인 요청에서 `total_count < 100`이면 이전 평일로 넘어간다. 1건은 건너뛰었다. |
| ALH-0706 | P1 | 상장 목록 total>=100 | 통과 | 100건 이상이면 그 `basDt`로 `fetch_pages`를 호출해 전체 목록을 받는다. |
| ALH-0707 | P1 | 14일 모두 미수집 | 통과 | 평일 14개가 모두 100건 미만이면 `RuntimeError`다. |
| ALH-0708 | P1 | 공시 5종 모두 호출 | 통과 | `DISCLOSURE_URLS` 키가 dividend, default, suspend, rehab, reduction이고 `fetch_disclosures`가 전부를 돈다. |
| ALH-0709 | P1 | 200 응답 본문 없음 | 통과 | 본문이 JSON이 아니면 파싱 예외로 실패한다. 헤더만 있고 `resultCode`가 성공이면 빈 목록과 total 0으로 처리한다. |
| ALH-0710 | P1 | 서비스키 로그 비노출 | 부분 | 애플리케이션 `print`는 키를 찍지 않는다. HTTP 오류 메시지에는 URL의 `serviceKey`가 남는다. |
| ALH-0711 | P1 | rate limit | 부분 | 429는 `raise_for_status`의 `HTTPError`다. 재시도와 429 전용 보고는 없다. |
| ALH-0712 | P1 | 중복 페이지 | 실패 | 페이지 내용이 같아도 건수와 빈 페이지만 보고 누적한다. 중복 행 두 건이 그대로 남았다. |
