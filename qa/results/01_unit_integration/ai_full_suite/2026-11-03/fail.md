# FAIL

## QA-20261103-015350-724 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T01:53:50+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / SKIPPED
- 2차 검증: python -c import torch / SKIPPED
- 최종 상태: SKIPPED
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. torch가 있을 때만 pytest를 실행
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: SKIPPED
- 오류: torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). | Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: -
- 재검증: 이번 실행이 현재 검증
- 근거: A[SKIPPED] torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). || B[SKIPPED] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

## QA-20261103-020048-675 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:00:48+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / SKIPPED
- 2차 검증: python -c import torch / SKIPPED
- 최종 상태: SKIPPED
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. torch가 있을 때만 pytest를 실행
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: SKIPPED
- 오류: torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). | Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: -
- 재검증: 이번 실행이 현재 검증
- 근거: A[SKIPPED] torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). || B[SKIPPED] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

## QA-20261103-020548-152 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:05:48+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / ERROR
- 2차 검증: python -c import torch / ERROR
- 최종 상태: ERROR
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. torch가 있을 때만 pytest를 실행
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: ERROR
- 오류: torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). | Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: A[ERROR] torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). || B[ERROR] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

## QA-20261103-020706-866 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:07:06+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / ERROR
- 2차 검증: python -c import torch / ERROR
- 최종 상태: ERROR
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. torch가 있을 때만 pytest를 실행
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: ERROR
- 오류: torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). | Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: regression-rerun. A[ERROR] torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). || B[ERROR] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

## QA-20261103-020935-329 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:09:35+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / ERROR
- 2차 검증: python -c import torch / ERROR
- 최종 상태: ERROR
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. torch가 있을 때만 pytest를 실행
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: ERROR
- 오류: torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). | Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: A[ERROR] torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). || B[ERROR] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

## QA-20261103-021000-562 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:10:00+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / ERROR
- 2차 검증: python -c import torch / ERROR
- 최종 상태: ERROR
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. torch가 있을 때만 pytest를 실행
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: ERROR
- 오류: torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). | Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: -
- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: regression-rerun. A[ERROR] torch를 가져오지 못함. CI에서는 오류, 로컬에서는 미실행(SKIPPED). || B[ERROR] Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'torch'

## QA-20261103-021147-653 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:11:47+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / FAIL
- 2차 검증: python -c import torch / NOT_RUN
- 최종 상태: FAIL
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. 한 도구 결과만 있어 PASS로 확정하지 않음
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: FAIL
- 오류: e/screener.py:7: in <module>
    from src.inference.dl_risk import predict_dl
src/inference/__init__.py:2: in <module>
    from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
src/inference/dl_risk.py:4: in <module>
    import joblib
E   ModuleNotFoundError: No module named 'joblib'
 | 전체 스위트를 다시 실행하는 두 번째 러너가 없음
- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: e/screener.py:7: in <module>
    from src.inference.dl_risk import predict_dl
src/inference/__init__.py:2: in <module>
    from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
src/inference/dl_risk.py:4: in <module>
    import joblib
E   ModuleNotFoundError: No module named 'joblib'

- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: A[FAIL] e/screener.py:7: in <module>
    from src.inference.dl_risk import predict_dl
src/inference/__init__.py:2: in <module>
    from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
src/inference/dl_risk.py:4: in <module>
    import joblib
E   ModuleNotFoundError: No module named 'joblib'
 || B[NOT_RUN] 전체 스위트를 다시 실행하는 두 번째 러너가 없음
## QA-20261103-021222-293 TC-UNIT-AI-SUITE

- 실행 시각: 2026-11-03T02:12:22+09:00
- 기능: ai_full_suite
- 영역: 01_unit_integration
- 테스트 종류: unit
- 1차 검증: python -m pytest ai/tests / FAIL
- 2차 검증: python -c import torch / NOT_RUN
- 최종 상태: FAIL
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: UNKNOWN
- 함수: UNKNOWN
- 줄 번호: UNKNOWN
- ISSUE_ID: -
- RISK_ID: -
- 목적: 선택 검사. 한 도구 결과만 있어 PASS로 확정하지 않음
- 입력값: -
- 기대 결과: 두 도구 모두 PASS
- 실제 결과: FAIL
- 오류: e/screener.py:7: in <module>
    from src.inference.dl_risk import predict_dl
src/inference/__init__.py:2: in <module>
    from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
src/inference/dl_risk.py:4: in <module>
    import joblib
E   ModuleNotFoundError: No module named 'joblib'
 | 전체 스위트를 다시 실행하는 두 번째 러너가 없음
- 재현: python -m pytest ai/tests ; python -c import torch
- 원인: e/screener.py:7: in <module>
    from src.inference.dl_risk import predict_dl
src/inference/__init__.py:2: in <module>
    from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
src/inference/dl_risk.py:4: in <module>
    import joblib
E   ModuleNotFoundError: No module named 'joblib'

- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: regression-rerun. A[FAIL] e/screener.py:7: in <module>
    from src.inference.dl_risk import predict_dl
src/inference/__init__.py:2: in <module>
    from src.inference.dl_risk import RiskMLP, load_dl_model, predict_dl
src/inference/dl_risk.py:4: in <module>
    import joblib
E   ModuleNotFoundError: No module named 'joblib'
 || B[NOT_RUN] 전체 스위트를 다시 실행하는 두 번째 러너가 없음
