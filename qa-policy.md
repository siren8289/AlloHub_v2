# AlloHub QA·Security Policy

이 파일이 검사 절차의 기준이다. `AGENTS.md`, `.grok/agents/qa-agent.md`, `.grok/skills/qa-automation/SKILL.md`는 여기로 보낸다.

기능 추가, 수정, 버그 수정, 리팩터링, 배포·CI 설정 변경마다 적용한다. 사용자가 매번 QA를 요청하지 않아도 된다.

## 1. QA 테스트 영역

QA는 다음 4개 영역으로 고정한다.

1. 단위·통합 테스트 (`01_unit_integration`)
2. 웹·API 테스트 (`02_web_api`)
3. 보안·품질 검사 (`03_security_quality`)
4. 인프라·배포 검사 (`04_infra_deploy`)

## 2. 파일 및 폴더 명명 규칙

- 모든 파일명과 폴더명은 반드시 영어로 작성한다.
- 한글 파일명 및 한글 폴더명은 사용하지 않는다.
- 폴더명과 파일명에는 소문자와 `snake_case`를 권장한다.
- 기능별 섹션명도 영어로 작성한다. 예: `user_management`, `authentication`, `deployment`
- 날짜 폴더는 `YYYY-MM-DD` 형식으로 생성한다.
- Excel 시트 이름과 TC ID도 영어로 작성한다.
- 테스트 설명, 예상 결과, 오류 분석 및 보고서 본문은 한국어로 작성한다.
- 코드의 변수명, 명령어, 설정 키 등 기술 식별자는 영어로 유지한다.

## 3. QA 폴더 구조

```
qa/
├── master_test_sheet.xlsx
├── input/
│   └── testcases.tsv
└── results/
    ├── 01_unit_integration/
    ├── 02_web_api/
    ├── 03_security_quality/
    └── 04_infra_deploy/
```

각 테스트 영역 안에 기능별 섹션 폴더를 생성하고, 날짜별로 테스트 결과를 저장한다.

예시:

```
qa/results/
└── 01_unit_integration/
    └── user_management/
        └── 2026-11-03/
            ├── test_sheet.xlsx
            ├── pass.md
            ├── fail.md
            ├── risk.md
            └── summary.tsv
```

각 날짜 폴더에는 위 5개 파일을 생성한다.

`qa/master_test_sheet.xlsx`는 전체 테스트 영역과 섹션의 TC 현황을 통합 관리한다. 최상단에 전체 현황 Excel 파일을 중복 생성하지 않는다. TC 카탈로그는 `qa/input/testcases.tsv`다. 실행용 `qa/contract/`, `qa/requirements.txt`는 유지한다. 운영 메타는 `scripts/qa/latest.json`에 둔다.

경로: `qa/results/{area}/{feature}/{YYYY-MM-DD}/`

## 4. 이중 테스트 규칙

- 모든 TC는 가능한 한 서로 다른 두 가지 검증 방법으로 테스트한다.
- 두 검증은 서로 다른 관점이나 계층에서 동작을 확인해야 한다.
- 각 TC의 1차·2차 실행 명령, 예상 결과, 실제 결과를 각각 기록한다.
- 두 검증 모두 통과한 경우에만 최종 PASS로 처리한다.
- 하나라도 실패하면 FAIL로 처리한다.
- 검증이 불가능하거나 미실행된 경우 RISK 또는 NOT_RUN으로 구분한다.
- 실행하지 않은 테스트를 PASS로 기록하지 않는다.

종료 코드:

- 0: 필수 TC가 PASS이고 이번 실행의 HIGH/CRITICAL이 열려 있지 않다.
- 1: FAIL, BLOCKED, 필수 NOT_RUN, 또는 미해결 HIGH/CRITICAL.
- 2: 도구 ERROR만 있는 경우.

`TC-UNIT-AI-SUITE`는 선택 검사다. torch가 없으면 로컬에서는 SKIPPED이고, `--ci`에서는 ERROR다.

## 5. 자동화 및 AI 토큰 절약

- QA Agent 1개(`.grok/agents/qa-agent.md`)와 QA Skill 1개(`.grok/skills/qa-automation/SKILL.md`)를 사용한다.
- 신규 TC 작성, 변경 영향 분석, 복잡한 실패 원인 분석에만 AI를 사용한다.
- 기존 테스트 실행과 결과 판정은 자동화 스크립트로 처리한다.
- 테스트 실행 시 전체 프로젝트와 TSV를 매번 AI에 전달하지 않는다.
- TC를 순차적으로 실행하고 결과 시트를 갱신한다.
- Excel 및 Markdown 보고서 생성은 AI 호출 없이 수행한다.

```bash
python3 scripts/qa/run_qa.py
python3 scripts/qa/run_qa.py --with-regression
python3 scripts/qa/run_qa.py --ci --with-regression
```

| 영역 | 도구 A | 도구 B |
| --- | --- | --- |
| Python unit | `python -m pytest qa/contract/test_contracts.py data/tests --junitxml` | `python scripts/qa/tools/independent_unit.py` |
| Java allocation | `./gradlew test` JUnit XML | `javac` + `java AllocationCrossCheck` |
| API | Gradle MockMvc | bootRun HTTP on port 18080 |
| Security | `python scripts/qa/tools/security_scan.py` | `python -m bandit -r ai/src data -f json` |
| Infra | `docker compose -f compose.yaml config --quiet` | `compose_cross_check.py` |
| CI | `ci_workflow_check.py --tool a` | `ci_workflow_check.py --tool b` |

## 6. 지속적인 QC

- 신규 기능 개발 시 해당 기능의 TC를 자동 생성한다.
- 기능 수정 시 변경된 코드와 연결된 TC를 재실행한다.
- 실패한 TC 수정 후 관련 회귀 테스트를 수행한다.
- PR 및 배포 전 전체 회귀 테스트를 실행한다.
- 필수 테스트 실패 시 CI에서 병합 또는 배포를 차단한다.
- 실행 결과와 테스트 이력을 보존한다. 같은 날 재실행은 RUN_ID로 누적하고 덮어쓰지 않는다.

## 7. 최종 보고

모든 테스트가 종료되면 다음 내용을 기록한다.

- 전체 TC 수
- PASS / FAIL / RISK / NOT_RUN
- 1차 및 2차 검증 결과
- 실패 원인과 재현 절차
- 추가 테스트가 필요한 항목
- 테스트 실행 일시 및 관련 코드 위치

모든 테스트 기록의 본문은 한국어로 작성하되, 파일명·폴더명·기술 식별자는 영어를 사용한다.

`summary.tsv` 열:

`RUN_ID`, `TC_ID`, `executed_at`, `feature`, `test_type`, `tool_a`, `tool_a_result`, `tool_b`, `tool_b_result`, `final_status`, `git_commit`, `file`, `function`, `line`, `issue_id`, `risk_id`, `detail`

상태 값: `PASS`, `FAIL`, `BLOCKED`, `ERROR`, `NOT_RUN`, `SKIPPED`
