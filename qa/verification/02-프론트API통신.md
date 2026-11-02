# 프론트API통신 코드검증

- 범위: ALH-0013 ~ ALH-0021, ALH-0162 ~ ALH-0174
- 대상: `front/src/api/api.ts`, 호출부 `front/src/pages/ScreenPage.tsx`, `front/src/pages/AllocatePage.tsx`
- 방법: 소스 대조. `gradeLabel`/`won`은 Node `toLocaleString("ko-KR")`로 재현했다.
- 판정: 통과 18, 실패 4, 부분 0, 확인불가 0

재현 출력: `0원`, `1원`, `1,000원`, `100,000,000원`, `-1,000원`.

## 실패·부분

- ALH-0170 실패. HTTP 204는 `response.ok`라 `response.json()`으로 넘어간다. 빈 본문이면 `request` 안에서 잡지 않고 `SyntaxError`가 난다.
- ALH-0172 실패. `createScreen`은 본문을 그대로 반환하고, `ScreenPage`는 `result.id`를 검사하지 않은 채 `` `/screens/${result.id}` ``로 이동한다. `id`가 없으면 `/screens/undefined`다.
- ALH-0173 실패. `fetch`에 `AbortSignal`이나 제한 시간이 없다. 무응답 동안 버튼만 비활성화되고, 재시도 안내 문구는 없다.
- ALH-0174 실패. `getScreen`이 `id`를 `` `/api/screens/${id}` ``에 그대로 붙인다. `encodeURIComponent`가 없어 `1?a=b`는 쿼리가 된다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0013 | P1 | 등급 코드 stable 표시 | 통과 | `gradeLabel`이 `stable`이면 `안정`을 반환한다. |
| ALH-0014 | P1 | 등급 코드 warning 표시 | 통과 | `warning`이면 `주의`. |
| ALH-0015 | P1 | 등급 코드 danger 표시 | 통과 | `danger`이면 `위험`. |
| ALH-0016 | P1 | 등급 코드 unknown 표시 | 통과 | 세 코드가 아니면 입력 문자열을 그대로 반환한다. `unknown`은 `unknown`이다. |
| ALH-0017 | P1 | 원화 포맷 0 | 통과 | `` `${amount.toLocaleString("ko-KR")}원` ``. Node 재현 결과는 `0원`. |
| ALH-0018 | P1 | 원화 포맷 1 | 통과 | 재현 결과 `1원`. |
| ALH-0019 | P1 | 원화 포맷 1000 | 통과 | 재현 결과 `1,000원`. |
| ALH-0020 | P1 | 원화 포맷 100000000 | 통과 | 재현 결과 `100,000,000원`. |
| ALH-0021 | P1 | 원화 포맷 -1000 | 통과 | 재현 결과 `-1,000원`. |
| ALH-0162 | P1 | 기본 API_URL | 통과 | `import.meta.env.VITE_API_URL ?? "http://localhost:8080"`. 미설정이면 `http://localhost:8080`. |
| ALH-0163 | P1 | 배포 API_URL 빈 문자열 | 통과 | `??`는 `""`를 바꾸지 않는다. prefix가 빈 문자열이면 요청 경로는 `/api/...` 상대 경로가 된다. |
| ALH-0164 | P1 | POST 진단 메서드 | 통과 | `createScreen`은 `POST /api/screens`와 `JSON.stringify({ companyName })`다. |
| ALH-0165 | P1 | GET 진단 | 통과 | `getScreen("1")`은 method를 지정하지 않아 `GET /api/screens/1`이다. |
| ALH-0166 | P1 | POST 배분 | 통과 | `createAllocation`은 `POST /api/allocations`와 `{ companyName, totalAmount, investors }` JSON이다. |
| ALH-0167 | P1 | HTTP 400 JSON 오류 | 통과 | `response.ok`가 아니면 `body.message`를 `Error`로 던진다. |
| ALH-0168 | P1 | HTTP 404 JSON 오류 | 통과 | 상태 코드와 무관하게 같은 `body.message` 경로다. |
| ALH-0169 | P1 | HTTP 500 nonJSON | 통과 | JSON 파싱이 실패하면 `요청에 실패했습니다.`를 쓴다. |
| ALH-0170 | P1 | HTTP 204 빈 응답 | 실패 | 204도 `ok`라 `response.json()`을 호출한다. 빈 본문 보호가 없다. |
| ALH-0171 | P1 | network offline | 통과 | `fetch` 거부는 `request`가 삼키지 않는다. `ScreenPage`와 `AllocatePage`의 `catch`가 `e.message`를 화면에 넣는다. |
| ALH-0172 | P1 | 응답 구조 결손 | 실패 | `id` 누락을 거부하지 않아 `/screens/undefined`로 이동할 수 있다. |
| ALH-0173 | P1 | 시간 초과 | 실패 | 클라이언트 제한 시간과 재시도 안내가 없다. |
| ALH-0174 | P1 | URL path escaping | 실패 | 경로 파라미터를 인코딩하지 않는다. |
