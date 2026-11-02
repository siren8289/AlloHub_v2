# FAIL

## QA-20261103-015350-724 TC-API-001

- 실행 시각: 2026-11-03T01:53:50+09:00
- 기능: company_screen_api
- 영역: 02_web_api
- 테스트 종류: api
- 1차 검증: ./gradlew test / PASS
- 2차 검증: ./gradlew --no-daemon bootRun --args=--server.port=18080 / ERROR
- 최종 상태: ERROR
- Git Commit: f7421b7ba3a4617a5b22ffbfc12a6970e28d5d2c+dirty
- 파일: back/src/main/java/com/allohub/screen/controller/ScreenController.java
- 함수: create
- 줄 번호: 35
- ISSUE_ID: -
- RISK_ID: -
- 목적: MockMvc와 기동한 서버를 교차 확인
- 입력값: POST /api/screens {"companyName":""} -> 400 VALIDATION_ERROR
- 기대 결과: POST /api/screens {"companyName":""} -> 400 VALIDATION_ERROR
- 실제 결과: ERROR
- 오류: bootRun이 180초 안에 /api/health를 열지 못함 To honour the JVM settings for this build a single-use Daemon process will be forked. For more on this, please refer to https://docs.gradle.org/8.9/userguide/gradle_daemon.html#sec:disabling_the_daemon in the Gradle documentation.
Daemon will be stopped at the end of the build 
> Task :compileJava UP-TO-DATE
> Task :processResources UP-TO-DATE
> Task :classes UP-TO-DATE
> Task :resolveMainClassName UP-TO-DATE

- 재현: ./gradlew test ; ./gradlew --no-daemon bootRun --args=--server.port=18080
- 원인: -
- 수정 위치: 수정하지 않음
- 재검증: 이번 실행이 현재 검증
- 근거: A[PASS] junit || B[ERROR] bootRun이 180초 안에 /api/health를 열지 못함 To honour the JVM settings for this build a single-use Daemon process will be forked. For more on this, please refer to https://docs.gradle.org/8.9/userguide/gradle_daemon.html#sec:disabling_the_daemon in the Gradle documentation.
Daemon will be stopped at the end of the build 
> Task :compileJava UP-TO-DATE
> Task :processResources UP-TO-DATE
> Task :classes UP-TO-DATE
> Task :resolveMainClassName UP-TO-DATE

