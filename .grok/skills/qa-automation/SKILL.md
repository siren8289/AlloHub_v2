---
name: qa-automation
description: >
  AlloHub에서 기능을 추가·수정·리팩터링하거나 버그를 고치고 배포 설정·API·보안을
  바꿀 때 항상 적용한다. 사용자가 QA를 말하지 않아도 qa-policy.md를 따르고
  python3 scripts/qa/run_qa.py를 실행한다. 검사 없이 완료로 보고하지 않는다.
---

# QA automation skill

권위 있는 규칙은 저장소 루트의 `qa-policy.md`다. QA Agent는 `.grok/agents/qa-agent.md`다.

## Areas

- `01_unit_integration`
- `02_web_api`
- `03_security_quality`
- `04_infra_deploy`

Results: `qa/results/{area}/{feature}/{YYYY-MM-DD}/` with `test_sheet.xlsx`, `pass.md`, `fail.md`, `risk.md`, `summary.tsv`.
Top-level master: `qa/master_test_sheet.xlsx` only. Catalog: `qa/input/testcases.tsv`.

Folder and file names are English snake_case. Report bodies are Korean.

## Run

```bash
python3 scripts/qa/run_qa.py
python3 scripts/qa/run_qa.py --with-regression
```

Use AI only for new TCs, impact analysis, and complex failure diagnosis.
Excel/Markdown generation and routine execution are script-only.

Do not report complete if FAIL/ERROR/BLOCKED exist or HIGH/CRITICAL is OPEN.
