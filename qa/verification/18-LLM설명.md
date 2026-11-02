# LLM설명 코드검증

- 범위: ALH-0478 ~ ALH-0493
- 대상: `ai/src/llm/explainer.py`, `ai/src/llm/prompts.py`, 설정 `ai/src/core/config.py`
- 방법: 소스 대조. `basic_explanation`, `make_prompt`, `explain`의 키 없음·빈 키·호출 실패 분기를 실행했다. Gemini API는 호출하지 않았다.
- 판정: 통과 14, 실패 0, 부분 2, 확인불가 0

재현 출력: 키 없음·공백 키 → `basic`. 가짜 키는 `ModuleNotFoundError` 후 `basic`. `GEMINI_MODEL=custom-model-x`가 그대로 읽힌다. 기본 모델은 `gemini-3.8-flash`, 타임아웃 상수는 `15000`. 등급 문구는 `'안정'`·`'주의'`·`'위험'`.

## 실패·부분

- ALH-0487 부분. `basic_explanation`은 등급을 다시 계산하지 않는다. `default_count=1`만 넣고 `grade`를 비우면 문장은 `'안정'`이고 `부도 공시 1건`만 말한다. `screen()`이 `grade_of`로 `danger`를 넣은 뒤에 호출하면 `'위험'`이 들어간다.
- ALH-0492 부분. 기본 설명은 회사명 문자열을 실행하지 않고 템플릿에 넣는다. 다만 `make_prompt`도 그 문자열을 그대로 붙이며, Gemini 응답에서 지시문 이행을 거르지 않는다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0478 | P1 | API 키 없음 | 통과 | `get_gemini_api_key()`가 빈 문자열이면 `basic_explanation`과 `"basic"`을 반환한다. 미설정과 공백 키 모두 실행에서 `basic`이었다. |
| ALH-0479 | P1 | Gemini 정상 응답 | 통과 | `response.text`가 있으면 `response.text.strip()`과 `"gemini"`를 반환한다. API는 호출하지 않았다. |
| ALH-0480 | P1 | Gemini 빈 응답 | 통과 | `text=""`는 거짓이라 그 분기 아래 `basic_explanation`, `"basic"`으로 떨어진다. |
| ALH-0481 | P1 | Gemini 제한 초과 | 통과 | 호출부 전체가 `except Exception`이다. 429도 여기서 기본 설명으로 떨어진다. 상태 코드를 따로 나누지는 않는다. |
| ALH-0482 | P1 | Gemini 타임아웃 | 통과 | `HttpOptions(timeout=GEMINI_TIMEOUT_MS)`이고 값은 15000밀리초다. 시간 초과 예외도 같은 `except`에서 `basic`이 된다. |
| ALH-0483 | P1 | Gemini 인증 실패 | 통과 | 401도 잡히지 않은 채 올라오면 같은 `except`가 기본 설명을 반환한다. 가짜 키의 import 실패도 `basic`이었다. |
| ALH-0484 | P1 | 모델명 환경변수 | 통과 | `get_gemini_model()`은 `GEMINI_MODEL`을 읽고, 없으면 `gemini-3.8-flash`다. `generate_content(model=...)`에 그 값을 넘긴다. |
| ALH-0485 | P1 | 등급 stable | 통과 | `grade=stable`이면 문장에 `'안정' 단계`가 있다. 점수 10으로 실행했다. |
| ALH-0486 | P1 | 등급 warning | 통과 | `grade=warning`이면 `'주의' 단계`가 있다. |
| ALH-0487 | P1 | 등급 danger | 부분 | 건수만으로는 `'위험'`이 생기지 않는다. `grade="danger"`일 때만 `'위험' 단계`가 들어간다. |
| ALH-0488 | P1 | 부도 설명 | 통과 | `default_count=2`이면 `부도 공시 2건`이 문장에 있다. |
| ALH-0489 | P1 | 감자 설명 | 통과 | `reduction_count=1`이면 `감자 공시 1건`이 문장에 있다. |
| ALH-0490 | P1 | 공시 없음 문구 | 통과 | 네 건수가 모두 0이면 `수집한 공시에서는 부도·영업정지·회생·감자가 보이지 않습니다.`다. |
| ALH-0491 | P1 | 점수 투자권유 금지 | 통과 | 기본 설명은 점수와 무관하게 `이 점수는 출자 여부를 대신 정해 주지 않으며`를 붙인다. 프롬프트도 `매수·매도·투자 권유는 하지 마라`이다. |
| ALH-0492 | P1 | 기밀 프롬프트 유출 | 부분 | 기본 경로는 명령을 실행하지 않는다. 회사명은 프롬프트에 그대로 들어가고 출력 필터는 없다. |
| ALH-0493 | P1 | 프롬프트 숫자 일치 | 통과 | 기본 문장과 `make_prompt`가 `37.6`, `33`, `42.2`를 그대로 넣는다. 프롬프트는 `숫자는 그대로 인용해라`라고 지시한다. |
