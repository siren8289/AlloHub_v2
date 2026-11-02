# Docker배포 코드검증

- 범위: ALH-0793 ~ ALH-0815 (23건)
- 대상: `compose.yaml`, `front/Dockerfile`, `back/Dockerfile`, `ai/Dockerfile`, `front/nginx.conf`, `ai/src/api/routes.py`, `back/src/main/java/com/allohub/ai/AiClient.java`
- 방법: 배포 정의와 헬스·프록시 코드를 대조했다. `docker compose config --quiet`는 비밀번호 없이 실패하고, `DB_PASSWORD=ci-check`이면 종료코드 0이었다. 컨테이너는 기동하지 않았다.
- 판정: 통과 17, 실패 1, 부분 5, 확인불가 0

## 실패·부분

- ALH-0793 부분. 파일 구조는 맞지만, 저장소에 `.env`가 없으면 필수 변수 때문에 그 명령이 실패한다. 값을 넣으면 같은 명령이 성공한다.
- ALH-0797 부분. `back`은 `db`의 `service_healthy` 뒤에 뜨지만, 헬스체크는 `pg_isready`라 비밀번호 불일치를 보지 못한다. 볼륨의 옛 비밀번호와 `.env`가 다르면 `back`만 실패한다.
- ALH-0808 부분. `db`는 healthy를 기다리지만 `ai`는 `service_started`만 기다린다. `/health`가 통과하기 전에 `back`이 AI를 호출할 수 있다.
- ALH-0810 부분. 이미지는 `postgres:16-alpine`이고 pgvector가 없다. AI 서비스에 `DATABASE_URL`도 없어 공시 검색은 메모리 폴백이다. DB 검색을 켜면 확장이 없어 실패한다.
- ALH-0813 부분. `compose.yaml`에 로그 드라이버나 오류 포맷이 없다. 앱은 stdout이라 기본 수집으로 `docker compose logs`는 가능하지만, 실패 로그를 재현하지는 않았다.
- ALH-0815 실패. 스키마 롤백, 백업, 복구 절차가 없다. `ddl-auto: update`와 `db-data` 볼륨만 있고 `scripts/deploy.sh`는 빌드 후 `up`만 한다.

## 전체 결과

| ID | 우선순위 | 항목 | 판정 | 근거 |
| --- | --- | --- | --- | --- |
| ALH-0793 | P1 | Compose 설정 유효 | 부분 | 비밀번호 없이 실행하면 `DB_PASSWORD` 필수 보간 오류로 종료코드 1이다. `DB_PASSWORD=ci-check`이면 `config --quiet`가 0이다. |
| ALH-0794 | P1 | DB_PASSWORD 누락 | 통과 | `POSTGRES_PASSWORD`가 `${DB_PASSWORD:?...}`다. 값이 없으면 compose가 기동 전에 중단된다. 그 오류 문구를 확인했다. |
| ALH-0795 | P1 | DB 비밀번호 설정 | 통과 | 같은 변수가 Postgres와 `SPRING_DATASOURCE_PASSWORD`에 들어간다. `ci-check`로 config를 풀면 양쪽 모두 그 값이다. |
| ALH-0796 | P1 | PostgreSQL healthcheck | 통과 | `pg_isready -U allo -d allohub`, 간격 5초, 타임아웃 3초, 재시도 20회다. 준비되면 healthy가 되는 정의다. 실제 기동은 하지 않았다. |
| ALH-0797 | P1 | DB 기동 실패 | 부분 | healthy 의존성은 있으나 자격 증명을 검사하지 않는다. 잘못된 비밀번호는 `back` 로그에서만 드러난다. |
| ALH-0798 | P1 | DB 볼륨 | 통과 | `db-data`가 `/var/lib/postgresql/data`에 마운트된 네임드 볼륨이다. 컨테이너를 지워도 볼륨을 지우지 않으면 데이터가 남는다. |
| ALH-0799 | P1 | AI 헬스체크 | 통과 | compose가 컨테이너 안 `http://127.0.0.1:8000/health`를 연다. `ai/src/api/routes.py`의 `GET /health`는 `{"status":"ok"}`를 200으로 돌려준다. |
| ALH-0800 | P1 | AI 불건전 상태 | 통과 | `urlopen`은 HTTP 500이면 예외가 나고 헬스체크가 실패해 unhealthy가 된다. 현재 핸들러는 프로세스가 살아 있으면 200만 준다. |
| ALH-0801 | P1 | back 서비스 이름 | 통과 | `APP_AI_BASE_URL=http://ai:8000`이다. `AiClient`는 `app.ai.base-url`로 이 주소를 쓴다. 서비스 이름 `ai`는 기본 네트워크 DNS다. |
| ALH-0802 | P1 | back DB 연결 | 통과 | `SPRING_DATASOURCE_URL`이 `jdbc:postgresql://db:5432/allohub`다. `localhost`가 아니다. |
| ALH-0803 | P1 | front 프록시 | 통과 | 프록시 규칙은 `compose.yaml`이 아니라 `front/nginx.conf`다. `location /api/`가 `proxy_pass http://back:8080`이고, compose의 `back` 서비스로 전달된다. |
| ALH-0804 | P1 | SPA 리프레시 | 통과 | `nginx.conf`의 `try_files $uri $uri/ /index.html`이 `/screens/1`을 화면 진입점으로 보낸다. compose는 그 설정을 담은 front 이미지를 띄운다. |
| ALH-0805 | P1 | AI 포트 localhost bind | 통과 | 포트가 `127.0.0.1:8000:8000`이다. config 결과의 `host_ip`도 `127.0.0.1`이다. |
| ALH-0806 | P1 | Spring 포트 localhost bind | 통과 | 포트가 `127.0.0.1:8080:8080`이다. 호스트 외부 인터페이스에 바로 열리지 않는다. |
| ALH-0807 | P1 | nginx HTTP 포트 | 통과 | `"80:80"`이라 호스트 `0.0.0.0:80`이다. UI 진입 포트로 맞다. |
| ALH-0808 | P1 | 종속성 ready | 부분 | `ai` 의존 조건이 `service_started`다. 헬스체크가 있어도 `back` 기동 조건에 연결되지 않는다. |
| ALH-0809 | P1 | 서비스 다운 재기동 | 통과 | `ai`를 포함한 네 서비스가 `restart: unless-stopped`다. `docker kill` 뒤에는 이 정책으로 다시 뜬다. 직접 kill은 하지 않았다. |
| ALH-0810 | P1 | Postgres 일반 이미지 | 부분 | `postgres:16-alpine`에는 pgvector가 없고, compose도 그 확장을 설치하지 않는다. RAG의 DB 경로는 환경변수가 없으면 쓰이지 않는다. |
| ALH-0811 | P1 | 환경변수 분리 | 통과 | `GEMINI_API_KEY`는 `${GEMINI_API_KEY:-}` 런타임 값이다. 이미지 Dockerfile에 키가 없고, 실패 로그는 예외 타입만 출력한다. 미설정 config에서는 빈 문자열이다. |
| ALH-0812 | P1 | 네트워크 분리 | 통과 | 사용자 정의 네트워크는 없고 compose 기본 네트워크 하나다. `db`, `ai`, `back` 이름으로 DNS 통신은 된다. 서비스 간 차단은 없다. |
| ALH-0813 | P1 | Docker 로그 확인 | 부분 | 로깅 블록이 없다. Java, uvicorn, nginx, Postgres는 stdout이라 기본 드라이버로 로그 명령이 동작한다. 오류 재현은 없다. |
| ALH-0814 | P1 | 이미지 재빌드 | 통과 | `ai`, `back`, `front`에 `build.context`가 있고 Dockerfile이 소스를 복사한다. `docker compose up --build`가 그 변경을 이미지에 넣는다. 빌드는 실행하지 않았다. |
| ALH-0815 | P1 | 롤백 테스트 | 실패 | 배포 전후 스키마를 되돌리는 절차, 덤프, 이전 이미지 태그가 없다. `update`는 앞으로만 맞춘다. |
