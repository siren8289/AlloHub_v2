# 출자배분SpringAPI 코드검증

- 범위: ALH-0195 ~ ALH-0219 (25건)
- 대상: `AllocationController`, `AllocationService`, `AllocationRequest`, `InvestorRequest`, `Allocation`, `AllocationCalculator`, `AiClient`, `GlobalExceptionHandler`, `AllocationControllerTest`
- 방법: 소스 대조. `totalAmount`의 `1.5`, `1e3`, `"100"`은 Jackson 2.15.4 기본 `ObjectMapper`로 역직렬화 결과를 확인했다. 서버는 다시 띄우지 않았다.
- 판정: 통과 23, 실패 2, 부분 0, 확인불가 0

## 실패·부분

- ALH-0201 실패. `totalAmount`는 `Long`이고 `ACCEPT_FLOAT_AS_INT` 기본값이 켜져 있다. `1.5`는 `1`로 잘린 뒤 `@Min(1)`을 통과한다. 400이 아니고, 1원으로 저장될 수 있다.
- ALH-0202 실패. JSON `1e3`은 `1000`으로 파싱된다. 4xx나 검증 오류 없이 이후 로직으로 간다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0195 | P0 | companyName="" 검증 | 통과 | `AllocationRequest.companyName`의 `@NotBlank`다. `@Valid`가 메서드 진입 전에 400 `VALIDATION_ERROR`를 만들고 `allocate`는 호출되지 않는다. |
| ALH-0196 | P0 | companyName=null 검증 | 통과 | null도 `@NotBlank` 실패다. 400 `VALIDATION_ERROR`, 저장 없음. |
| ALH-0197 | P0 | totalAmount=None 검증 | 통과 | JSON null은 `@NotNull` 실패다. 400 `VALIDATION_ERROR`, 저장 없음. |
| ALH-0198 | P0 | totalAmount=0 검증 | 통과 | `@Min(1)`이 0을 거절한다. 400 `VALIDATION_ERROR`, 저장 없음. |
| ALH-0199 | P0 | totalAmount=-1 검증 | 통과 | `@Min(1)`이 음수를 거절한다. 400 `VALIDATION_ERROR`, 저장 없음. |
| ALH-0200 | P0 | totalAmount=1 검증 | 통과 | `@Min(1)`은 1을 허용한다. 나머지 필드가 맞으면 `CREATED`로 201과 저장 id가 난다. |
| ALH-0201 | P0 | totalAmount=1.5 검증 | 실패 | 소수 `1.5`가 `Long` 1로 잘린다. 검증을 통과하면 1원 배분이 저장된다. 400이 아니다. |
| ALH-0202 | P0 | totalAmount=1e3 검증 | 실패 | `1e3`은 `Long` 1000이다. 거절하지 않는다. |
| ALH-0203 | P0 | investors=None 검증 | 통과 | `@NotEmpty`는 null을 거절한다. 400 `VALIDATION_ERROR`, 저장 없음. |
| ALH-0204 | P0 | investors=[] 검증 | 통과 | 빈 리스트도 `@NotEmpty` 실패다. 400, 저장 없음. |
| ALH-0205 | P0 | investors=[{'name': '김', 'ratio': 100}] 검증 | 통과 | 이름 `@NotBlank`, 비율 `@DecimalMin(0.01)` `@DecimalMax(100)`을 통과한다. 합 100이라 `AllocationService`의 0.05 허용 오차도 통과하고 201로 저장된다. |
| ALH-0206 | P0 | investors=[{'name': '김', 'ratio': 0}] 검증 | 통과 | `@DecimalMin("0.01")`가 0을 거절한다. 400 `VALIDATION_ERROR`, 저장 없음. |
| ALH-0207 | P0 | investors=[{'name': '김', 'ratio': 100.01}] 검증 | 통과 | `@DecimalMax("100")`가 100.01을 거절한다. 400, 저장 없음. |
| ALH-0208 | P0 | investors=[{'name': '', 'ratio': 100}] 검증 | 통과 | `InvestorRequest.name`의 `@NotBlank`다. `@Valid`가 중첩에 적용되어 400, 저장 없음. |
| ALH-0209 | P0 | investors=[{'name': '김', 'ratio': None}] 검증 | 통과 | `ratio`의 `@NotNull`이 null을 거절한다. 400, 저장 없음. |
| ALH-0210 | P1 | 정상 생성 응답코드 | 통과 | `AllocationController.create`가 201이다. `Allocation.id`는 `IDENTITY`다. `AllocationControllerTest`가 201과 금액을 확인한다. |
| ALH-0211 | P1 | 단건 조회 | 통과 | `GET /{id}`가 `AllocationService.get`다. `lines`는 `FetchType.EAGER`라 200 본문에 금액과 라인이 같이 있다. `open-in-view`는 false다. |
| ALH-0212 | P1 | 없는 ID | 통과 | 없으면 `ApiException.notFound` → 404 `NOT_FOUND`. |
| ALH-0213 | P1 | 최근 10건 | 통과 | `AllocationRepository.findTop10ByOrderByIdDesc`다. 최대 10건, id 내림차순이다. |
| ALH-0214 | P1 | 총액 문자열 입력 | 통과 | 거부 설정은 없다. Jackson 기본 강제가 `"100"`을 `Long` 100으로 읽는다. 그 다음 `@Min(1)`을 탄다. 정책은 숫자 문자열을 역직렬화하는 쪽이다. |
| ALH-0215 | P1 | 출자자 20명 | 통과 | `@Size(max=20)`은 20을 허용한다. 합이 100이면 서비스 검사를 통과하고 201이다. |
| ALH-0216 | P1 | 출자자 21명 | 통과 | `@Size(max=20)`이 21명을 거절한다. 400 `VALIDATION_ERROR`이고 메시지는 `investors` 필드 안내를 포함한다. 저장 전에 끝난다. |
| ALH-0217 | P1 | 유효성 오류 메시지 | 통과 | `ratio=-1`은 `@DecimalMin` 실패다. 본문은 `errorCode=VALIDATION_ERROR`와 `investors[0].ratio: 출자 비율은 0보다 커야 합니다.` 형태다. |
| ALH-0218 | P1 | JSON 오류 | 통과 | 깨진 JSON은 `HttpMessageNotReadableException` → 400 `INVALID_JSON`. |
| ALH-0219 | P1 | AI 호출 실패 | 통과 | `allocate`는 비율 검사와 금액 계산 뒤에 `aiClient.screen`을 부르고, 그 다음 `allocationRepository.save`를 한다. AI 예외면 save에 닿지 않고 502 `AI_ERROR`가 나간다. |
