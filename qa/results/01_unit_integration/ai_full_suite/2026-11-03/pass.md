# PASS


## QA-20261103-021407-252 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:14:07+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / PASS
- 2차 검증: python -c import torch / PASS
- 최종 상태: PASS
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. pytest와 torch import로 교차 확인
- 입력값: -
- 기대 결과: ai/tests PASS + torch import PASS
- 실제 결과: PASS
- 오류: -
- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: -
- 재검증: 두 도구 일치
- 근거: A[PASS] stclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
22 passed, 1 warning in 1.44s
 || B[PASS] torch import ok
## QA-20261103-021426-955 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:14:26+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / PASS
- 2차 검증: python -c import torch / PASS
- 최종 상태: PASS
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. pytest와 torch import로 교차 확인
- 입력값: -
- 기대 결과: ai/tests PASS + torch import PASS
- 실제 결과: PASS
- 오류: -
- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: -
- 재검증: 두 도구 일치
- 근거: regression-rerun. A[PASS] stclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
22 passed, 1 warning in 1.51s
 || B[PASS] torch import ok
