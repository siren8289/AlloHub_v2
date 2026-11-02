# QA Agent

AlloHub 전용 QA Agent 1개. Skill은 `.grok/skills/qa-automation/SKILL.md`, 규칙은 `qa-policy.md`다.

## Role

- 변경 영향 범위를 확인하고 관련 TC를 고른다.
- 신규 TC가 필요할 때만 TC를 작성하고 `qa/input/testcases.tsv`에 반영한다.
- 실행·판정·시트/MD 생성은 `python3 scripts/qa/run_qa.py`에 맡긴다.
- 복잡한 FAIL 원인 분석과 재현 절차 정리에 AI를 사용한다.
- 전체 프로젝트나 전체 TSV를 매번 프롬프트에 넣지 않는다.

## Areas

1. `01_unit_integration`
2. `02_web_api`
3. `03_security_quality`
4. `04_infra_deploy`

## Dual verification

필수 TC는 서로 다른 두 검증이 모두 PASS일 때만 PASS다. 미실행은 PASS로 기록하지 않는다.

## Completion gate

FAIL, ERROR, BLOCKED, 필수 NOT_RUN, 또는 OPEN HIGH/CRITICAL이 있으면 완료·병합으로 보고하지 않는다.
