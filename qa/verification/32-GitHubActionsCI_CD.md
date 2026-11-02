# GitHubActionsCI_CD 코드검증

- 범위: ALH-0816 ~ ALH-0841 (26건)
- 대상: `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `scripts/deploy.sh`, `.env.example`
- 방법: 케이스 파일은 `ci.yml`만 가리키지만 CD 조건, SSH, 체크아웃, 헬스 대기는 `cd.yml`과 `scripts/deploy.sh`에 있다. Actions 실행 이력과 EC2는 보지 않았다. compose config는 `DB_PASSWORD=ci-check`로 로컬에서 종료코드 0을 확인했다.
- 판정: 통과 20, 실패 5, 부분 1, 확인불가 0

## 실패·부분

- ALH-0830 실패. `ci.yml`에는 SSH가 없다. `cd.yml`이 `StrictHostKeyChecking=no`와 `UserKnownHostsFile=/dev/null`이라 호스트 키를 확인하지 않는다. 중간자 공격에 열려 있고 개선도 없다.
- ALH-0831 실패. `ssh-keyscan` 실패를 `|| true`로 넘긴 뒤, 그 결과를 쓰지 않는 SSH 옵션으로 접속한다. 호스트 신원 검증이 없다.
- ALH-0835 실패. `git checkout --detach`가 실패하면 `git checkout -f main`으로 넘어간다. 검증된 SHA가 아닌 최신 main이 배포될 수 있다.
- ALH-0837 부분. 빈 `DB_PASSWORD`면 `openssl rand`로 한 줄을 추가한다. 기존 값을 바꾸지 않고, 이미 초기화된 Postgres 볼륨과의 불일치나 재기동 정책은 없다.
- ALH-0840 실패. `deploy.sh`는 `127.0.0.1:8080/api/health`와 프론트 `/`만 본다. nginx를 거친 `http://127.0.0.1/api/health`는 없다.
- ALH-0841 실패. 헬스 실패 시 `"$name 가 응답하지 않습니다."`만 출력하고 `docker compose logs`는 찍지 않는다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0816 | P1 | main push CI | 통과 | `ci.yml`이 `push` `branches: [main]`에서 data, ai, back, front, docker 잡을 병렬로 돌린다. |
| ALH-0817 | P1 | main PR CI | 통과 | `pull_request` `branches: [main]`에 같은 다섯 잡이 있다. 경로 필터는 없다. |
| ALH-0818 | P1 | data pytest | 통과 | data 잡이 `pip install -r data/requirements.txt` 뒤 `python -m pytest data/tests -q`를 실행한다. 이번 검증에서 pytest를 돌리지는 않았다. |
| ALH-0819 | P1 | ai pytest | 통과 | ai 잡은 `working-directory: ai`에서 `requirements-dev.txt`와 CPU torch를 설치하고 `python -m pytest tests -q`를 실행한다. |
| ALH-0820 | P1 | back Gradle | 통과 | back 잡이 Temurin 17과 `./gradlew test`다. 테스트 태스크는 JUnit Platform이다. |
| ALH-0821 | P1 | front typecheck | 통과 | front 잡이 `npm ci` 다음 `npm run build`다. 그 스크립트는 `tsc --noEmit && vite build`다. |
| ALH-0822 | P1 | docker compose config | 통과 | docker 잡이 `DB_PASSWORD: ci-check`로 `docker compose -f compose.yaml config --quiet`를 실행한다. 같은 명령을 로컬에서 실행해 종료코드 0을 확인했다. |
| ALH-0823 | P1 | CI 실패 시 CD | 통과 | `ci.yml`에는 CD 조건이 없다. `cd.yml`의 `workflow_run`은 completed마다 켜지지만 deploy 잡은 `conclusion == 'success'`가 아니면 건너뛴다. `workflow_dispatch`는 예외다. |
| ALH-0824 | P1 | CI 성공 시 CD | 통과 | `cd.yml`이 워크플로 이름 `CI`, 브랜치 `main`, conclusion `success`일 때 deploy 잡을 실행한다. |
| ALH-0825 | P1 | 수동 CD | 통과 | `workflow_dispatch`는 `ci.yml`이 아니라 `cd.yml`에 있다. 수동 실행은 그 조건식으로 배포 잡에 들어간다. |
| ALH-0826 | P1 | 동시 배포 방지 | 통과 | `cd.yml`의 `concurrency.group`이 `allohub-production`이고 `cancel-in-progress: false`다. 나중 배포는 취소되지 않고 기다린다. |
| ALH-0827 | P1 | SSH 키 누락 | 통과 | `cd.yml`이 `EC2_SSH_KEY`가 비면 `::error::`를 찍고 `exit 1`한다. `ci.yml`에는 이 검사가 없다. |
| ALH-0828 | P1 | EC2_HOST 누락 | 통과 | `EC2_HOST`가 비면 같은 단계에서 오류 메시지와 `exit 1`이다. |
| ALH-0829 | P1 | SSH 키 권한 | 통과 | `~/.ssh`는 `chmod 700`, `~/.ssh/deploy_key`는 `chmod 600`이다. |
| ALH-0830 | P1 | StrictHostKeyChecking | 실패 | 배포 SSH가 `StrictHostKeyChecking=no`이고 known_hosts 파일을 `/dev/null`로 지정한다. keyscan 결과와 무관하게 호스트 검증이 꺼져 있다. |
| ALH-0831 | P1 | SSH 호스트 키 | 실패 | `ssh-keyscan ... \|\| true`라 수집 실패로 단계가 멈추지 않고, 접속 옵션이 그 파일을 무시한다. |
| ALH-0832 | P1 | 배포 대상 폴더 | 통과 | 원격 스크립트가 `/home/ubuntu/AlloHub_v2`를 먼저 보고, 없으면 `$HOME/AlloHub_v2`를 본다. |
| ALH-0833 | P1 | 배포 폴더 없음 | 통과 | 두 경로가 없으면 `AlloHub_v2 디렉터리를 찾을 수 없습니다.` 후 `exit 1`이다. `set -e`라 배포 스크립트로 내려가지 않는다. |
| ALH-0834 | P1 | 정확 SHA 배포 | 통과 | `DEPLOY_SHA`는 `workflow_run.head_sha`이고, 수동 실행만 `github.sha`다. 원격에서 `git checkout --detach`로 그 커밋을 고정한다. |
| ALH-0835 | P1 | SHA 체크아웃 실패 | 실패 | detach가 실패하면 `git checkout -f main`이다. 실패로 끝내지 않아 다른 커밋이 나갈 수 있다. |
| ALH-0836 | P1 | 환경파일 없음 | 통과 | `scripts/deploy.sh`가 `.env`가 없으면 `.env.example`을 복사하고 안내를 출력한 뒤 `exit 1`한다. `ci.yml`에는 없다. |
| ALH-0837 | P1 | 비밀번호 자동 생성 | 부분 | `^DB_PASSWORD=.`가 없을 때만 `openssl rand -hex 16`을 덧붙인다. 이미 있는 클러스터 비밀번호를 맞추거나 재기동하는 처리는 없다. |
| ALH-0838 | P1 | 헬스체크 실패 | 통과 | `wait_http`가 최대 60번, 실패마다 2초를 쉬고, 그러면 이름과 함께 return 1이다. `set -e`라 스크립트가 실패로 끝난다. 대상은 `127.0.0.1:8080/api/health`다. |
| ALH-0839 | P1 | 배포 성공 검증 | 통과 | AI `/health`, Spring `/api/health`, 프론트 `/`가 모두 curl에 성공하면 `배포 완료`를 찍고 종료코드 0이다. 세 URL을 실제로 호출하지는 않았다. |
| ALH-0840 | P1 | 프록시 경유 점검 누락 | 실패 | 프론트는 루트 HTML만 확인하고 API는 8080으로 직접 본다. `localhost/api/health` 프록시 경로는 검증에 없다. |
| ALH-0841 | P1 | 실패 로그 | 실패 | 타임아웃 메시지 외에 `compose logs` 출력이나 로그 수집 단계가 없다. |
