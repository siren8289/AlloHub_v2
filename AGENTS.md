# AlloHub working rules

기능 추가, 수정, 버그 수정, 리팩터링, 배포·CI 설정 변경은 사용자가 QA를 다시 말하지 않아도 `qa-policy.md`를 따른다.

1. 바꾼 파일과 영향 범위를 확인한다. 요구사항이 불명확하면 추측하지 않고 RISK로 남긴다.
2. 기존 TC를 재사용하고, 없을 때만 TC를 추가한다. TC 카탈로그는 `qa/input/testcases.tsv`다.
3. 코드를 수정하기 전에 발견한 FAIL과 RISK를 `qa/results/{area}/{feature}/{YYYY-MM-DD}/`에 기록한다.
4. 관련 검사를 실행한다. 개발 중에는 변경 기능의 관련 TC를 실행하고, PR·배포 전에는 `--with-regression`으로 전체 회귀를 수행한다. 완료 전에는 서로 다른 도구 최소 2개로 교차 검증한다.

```bash
python3 scripts/qa/run_qa.py
python3 scripts/qa/run_qa.py --with-regression
```

5. 필수 검사가 PASS가 아니거나 이번 실행의 HIGH/CRITICAL이 OPEN이면 완료·병합으로 보고하지 않는다.
6. NOT_RUN, ERROR, SKIPPED, 도구 오류는 PASS가 아니다. 실행하지 않은 검증은 PASS로 적지 않는다.
7. QA 영역은 `01_unit_integration`, `02_web_api`, `03_security_quality`, `04_infra_deploy`로 고정한다. 파일·폴더명은 영어 `snake_case`다. 보고서 본문은 한국어다. `qa/` 최상단 통합 시트는 `master_test_sheet.xlsx` 하나뿐이다.

상태 정의, TSV 열, 도구 명령, 종료 코드는 `qa-policy.md`에 있다.
