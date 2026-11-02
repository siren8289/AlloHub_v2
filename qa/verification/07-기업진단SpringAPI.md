# 기업진단SpringAPI 코드검증

- 범위: ALH-0175 ~ ALH-0194 (20건)
- 대상: `ScreenController`, `ScreenService`, `ScreenRequest`, `CompanyScreen`, `CompanyScreenRepository`, `AiClient`, `GlobalExceptionHandler`, `ScreenControllerTest`
- 방법: 소스 대조. Jackson 2.15.4(Spring Boot 3.2.5) 기본 `ObjectMapper`로 숫자 회사명 역직렬화만 따로 확인했다. 서버는 다시 띄우지 않았다.
- 판정: 통과 15, 실패 5, 부분 0, 확인불가 0

## 실패·부분

- ALH-0180 실패. `ScreenRequest`에는 `@NotBlank`만 있고 길이 제한이 없다. 101자는 FastAPI `max_length=100`의 422로 가고, `AiClient`는 404가 아닌 상태를 전부 `ApiException.aiError`(502 `AI_ERROR`)로 바꾼다. 길이 오류가 클라이언트 검증 오류로 전달되지 않는다.
- ALH-0184 실패. `GET /api/screens/abc`는 `Long` 변환 실패다. `GlobalExceptionHandler`의 `@ExceptionHandler(Exception.class)`가 먼저 잡아 500 `INTERNAL_ERROR`를 준다. 4xx가 아니다.
- ALH-0191 실패. AI 422도 같은 `aiError` 경로라 502다. 5xx로 오분류한다.
- ALH-0193 실패. `text/plain`은 Jackson 컨버터가 거절하지만, 그 `HttpMediaTypeNotSupportedException`도 포괄 핸들러가 500으로 바꾼다. 415가 아니다.
- ALH-0194 실패. `POST /api/screens/{id}` 매핑은 없다. 셀렉터가 없는 `@RestControllerAdvice`는 핸들러가 없어도 적용되어, 405 대신 500 `INTERNAL_ERROR`가 나간다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0175 | P0 | companyName="삼성전자" POST | 통과 | `ScreenController.create`가 `@ResponseStatus(CREATED)`로 `ScreenService.screen` 결과를 반환한다. `CompanyScreen`은 `GenerationType.IDENTITY`라 저장 시 id가 생긴다. `ScreenControllerTest.createAndGet`도 201과 `$.id`를 본다. |
| ALH-0176 | P0 | companyName="" POST | 통과 | `ScreenRequest.companyName`의 `@NotBlank`와 `@Valid`가 빈 문자열을 막는다. `GlobalExceptionHandler`가 400 `VALIDATION_ERROR`를 준다. 서비스 저장 전에 끝난다. 테스트 `blankNameReturns400`과 같다. |
| ALH-0177 | P0 | companyName="   " POST | 통과 | `@NotBlank`는 trim 후 길이가 0이면 실패한다. 공백만 있는 이름도 400 `VALIDATION_ERROR`이고 저장되지 않는다. |
| ALH-0178 | P0 | companyName=null POST | 통과 | JSON null은 필드 null이다. `@NotBlank`가 null을 거절해 400 `VALIDATION_ERROR`다. |
| ALH-0179 | P1 | companyName=1234 POST | 통과 | 프로젝트에 스칼라 강제 변환 설정은 없다. Jackson 2.15 기본값이 숫자 `1234`를 문자열 `"1234"`로 바꾼다. `@NotBlank`를 통과하면 진단이 진행된다. 정책은 거부 없이 문자로 받는 것이다. |
| ALH-0180 | P1 | companyName="A"*101 POST | 실패 | Spring은 101자를 그대로 `company_name`으로 보낸다. FastAPI 422는 `AiClient`에서 502 `AI_ERROR`가 되고, `detail`은 응답에 실리지 않는다. |
| ALH-0181 | P1 | 생성 HTTP 응답코드 | 통과 | `create`의 `@ResponseStatus(HttpStatus.CREATED)`가 201이다. |
| ALH-0182 | P1 | 단건 조회 | 통과 | `GET /{id}`가 `ScreenService.get` → `findById`다. 있으면 200과 엔티티 JSON이다. |
| ALH-0183 | P1 | 미존재 ID | 통과 | 없으면 `ApiException.notFound`다. 핸들러가 404 `NOT_FOUND`와 메시지를 준다. |
| ALH-0184 | P1 | 비숫자 ID | 실패 | 경로 변수가 `Long`이라 `abc`는 타입 불일치다. 포괄 핸들러가 500 `INTERNAL_ERROR`로 삼킨다. |
| ALH-0185 | P1 | 최근 목록 | 통과 | `CompanyScreenRepository.findTop10ByOrderByIdDesc`다. `IDENTITY`라 id 내림차순이 최신 10건이다. |
| ALH-0186 | P1 | 10건보다 적은 목록 | 통과 | `findTop10`은 상한만 둔다. 3건이면 3건을 반환한다. |
| ALH-0187 | P1 | 11건 저장 | 통과 | 같은 쿼리가 11건 중 id가 큰 10건만 반환한다. |
| ALH-0188 | P1 | 서버 응답 구조 검증 | 통과 | 201 본문은 저장한 `CompanyScreen`이다. id와 서비스가 AI 노드에서 채운 필드가 그대로 나간다. 별도 응답 DTO는 없다. |
| ALH-0189 | P1 | AI 서비스 통신 불가 | 통과 | 연결 실패는 `RestClientException`이다. `AiClient`가 502 `AI_ERROR`를 던지고, 5xx라 로그도 남긴다. 저장은 `screen` 호출 뒤라 실행되지 않는다. |
| ALH-0190 | P1 | AI 404 | 통과 | HTTP 404만 `ApiException.notFound(readDetail)`이다. JSON `detail`이 있으면 그 문장을 404 본문에 넣는다. |
| ALH-0191 | P1 | AI 422 | 실패 | 422는 404 분기에 없다. 502 `AI_ERROR`로 올라간다. |
| ALH-0192 | P1 | 잘못된 JSON | 통과 | 깨진 본문은 `HttpMessageNotReadableException`이다. 핸들러가 400 `INVALID_JSON`을 준다. |
| ALH-0193 | P1 | Content-Type 오류 | 실패 | `text/plain`은 415로 끝나야 하나, 포괄 `Exception` 핸들러가 500 `INTERNAL_ERROR`를 만든다. |
| ALH-0194 | P1 | GET 목록 메서드 제한 | 실패 | `/{id}`에는 `GET`만 있다. 메서드 불일치는 405여야 하나, 같은 포괄 핸들러가 500으로 바꾼다. |
