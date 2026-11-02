# AI서비스API 코드검증

- 범위: ALH-0471 ~ ALH-0477, ALH-0494 ~ ALH-0504
- 대상: `ai/src/service/screener.py`, `ai/src/api/routes.py`, `ai/src/api/schemas.py`, 라우터 등록 `ai/src/main.py`
- 방법: 소스 대조. 평균식 `round((ml_score + dl_score) / 2, 1)`을 실행했다. `/health`와 요청 검증·없는 회사 404는 실제 라우터로 호출했다. 삼성전자 200은 가중치를 다시 로드하지 않고 조회와 스키마로 판단했다.
- 판정: 통과 18, 실패 0, 부분 0, 확인불가 0

재현 출력: `(0+0)/2` → `0.0`, `(0+100)/2` → `50.0`, `(10+20)/2` → `15.0`, `(39.9+40.1)/2` → `40.0`, `(80+90)/2` → `85.0`, `(100+100)/2` → `100.0`, `(12.3+14.7)/2` → `13.5`. `GET /health` → `200 {"status":"ok"}`. 빈 이름·누락·101자·객체 → 422. `없는회사XYZ` → 404.

## 실패·부분

없음.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0471 | P1 | ML 0 + DL 0 평균 | 통과 | `screen`은 `round((ml_score + dl_score) / 2, 1)`이라 0과 0은 `0.0`이다. 이어서 `grade_of`를 호출한다. |
| ALH-0472 | P0 | ML 0 + DL 100 평균 | 통과 | 0과 100의 평균은 `50.0`이다. 공시가 없으면 이 점수는 `warning`이다. |
| ALH-0473 | P1 | ML 10 + DL 20 평균 | 통과 | 10과 20의 평균은 `15.0`이다. |
| ALH-0474 | P0 | ML 39.9 + DL 40.1 평균 | 통과 | `(39.9+40.1)/2`는 `40.0`이다. 임계값 이상이라 공시가 없으면 `warning`으로 이어진다. |
| ALH-0475 | P1 | ML 80 + DL 90 평균 | 통과 | 80과 90의 평균은 `85.0`이다. |
| ALH-0476 | P1 | ML 100 + DL 100 평균 | 통과 | 100과 100의 평균은 `100.0`이다. |
| ALH-0477 | P1 | ML 12.3 + DL 14.7 평균 | 통과 | 12.3과 14.7의 평균은 `13.5`이다. |
| ALH-0494 | P1 | 헬스체크 | 통과 | `GET /health`는 `{"status":"ok"}`이고 실행 결과는 200이다. |
| ALH-0495 | P1 | 기업진단 | 통과 | `POST /api/v1/screen`은 `screen()` 결과를 `ScreenResponse`로 검증한다. `삼성전자`는 `A005930`으로 조회된다. `tests/test_api.py`의 `test_screen_samsung`이 200을 고정한다. 이번 검증에서는 가중치를 다시 로드하지 않았다. |
| ALH-0496 | P1 | 기업명 빈 값 | 통과 | `company_name`은 `min_length=1`이라 `""`는 422 `string_too_short`다. |
| ALH-0497 | P1 | 회사명 누락 | 통과 | `{}`는 422 `Field required`다. |
| ALH-0498 | P1 | 101자 회사명 | 통과 | `max_length=100`이라 `"A"*101`은 422 `string_too_long`이다. 100자는 스키마를 통과한다. |
| ALH-0499 | P1 | 없는 회사명 | 통과 | `없는회사XYZ`는 `find_company`의 HTTP 404가 그대로 응답된다. |
| ALH-0500 | P1 | 잘못된 요청 타입 | 통과 | `company_name`이 객체이면 422 `string_type`이다. 숫자 123도 문자로 바꾸지 않고 422다. |
| ALH-0501 | P1 | 결과 등급 타입 | 통과 | `grade`는 `Literal["stable","warning","danger"]`다. `danger`는 통과하고 `high`는 거부된다. `grade_of`도 이 세 값만 반환한다. |
| ALH-0502 | P1 | 점수 타입 | 통과 | `ml_score`·`dl_score`·`score`는 `float`다. 추론 점수도 `round`의 `float`다. |
| ALH-0503 | P1 | 기준일자 | 통과 | 응답은 `str(company["bas_dt"])`다. 배포 CSV 2737행은 모두 8자이고 표본은 `20261007`이다. |
| ALH-0504 | P1 | 공시 RAG 라우터 등록 | 통과 | `main.py`는 기존 `router`와 공시 라우터를 둘 다 붙인다. 공시 접두어는 `/api/v1/disclosure`라 `/api/v1/screen` 정의는 `routes.py`에 그대로다. |
