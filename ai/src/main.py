"""AlloHub AI 서버 (FastAPI). Spring 백엔드가 내부에서 호출한다.

POST /api/v1/screen   상장기업 위험 진단 (ML + DL + LLM)
GET  /health          서버 상태 확인
"""
from dotenv import load_dotenv
from fastapi import FastAPI

from src.api.routes import router
from src.core.config import ENV_PATH

# 환경변수 로드 (.env 파일이 존재하는 경우)
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

app = FastAPI(
    title="AlloHub AI",
    version="2.0.0",
    description="상장기업 위험 진단 및 출자금 배분 지원 AI 서비스",
)

app.include_router(router)
