#!/usr/bin/env bash
# 서버에서 docker compose 로 배포한다.
# 사용: bash scripts/deploy.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

compose() {
  docker compose --progress quiet -f compose.yaml "$@"
}

echo "=== 1. 설정 확인 ==="
if [ ! -f .env ]; then
  cp .env.example .env
  echo ".env 를 만들었습니다. DB_PASSWORD 를 채운 뒤 다시 실행하세요."
  exit 1
fi
if ! grep -q '^DB_PASSWORD=.' .env; then
  echo "DB_PASSWORD=$(openssl rand -hex 16)" >> .env
  echo ".env 에 DB_PASSWORD 를 만들었습니다."
fi
compose config --quiet

echo "=== 2. 이미지 빌드 ==="
compose build front
compose build back
compose build ai

echo "=== 3. 컨테이너 실행 ==="
compose up -d --remove-orphans
compose ps

echo "=== 4. 헬스 체크 ==="
wait_http() {
  local url="$1"
  local name="$2"
  for i in $(seq 1 60); do
    if curl -fsS --max-time 5 "$url" > /dev/null 2>&1; then
      echo "$name OK"
      return 0
    fi
    sleep 2
  done
  echo "$name 가 응답하지 않습니다."
  return 1
}

wait_http "http://127.0.0.1:8000/health" "AI"
wait_http "http://127.0.0.1:8080/api/health" "Spring"
wait_http "http://127.0.0.1/" "Front"
echo "배포 완료: http://127.0.0.1"
