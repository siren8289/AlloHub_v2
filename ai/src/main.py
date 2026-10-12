"""AlloHub AI 서버 (FastAPI). Spring 백엔드가 내부에서 호출한다.

POST /api/v1/screen              상장기업 위험 진단 (ML + DL + LLM)
GET  /health                     서버 상태 확인
POST /api/v1/disclosure/explain  공시 RAG 기반 재무 위험 설명 및 출처 인용
POST /api/v1/disclosure/search   공시 하이브리드 검색
POST /api/v1/disclosure/evaluate 공시 RAG 5대 품질 평가 메트릭 측정
"""
from dotenv import load_dotenv
from fastapi import FastAPI

from src.api.routes import router
from src.core.config import ENV_PATH
from src.features.disclosure_rag_001.router import router as disclosure_router

# 환경변수 로드 (.env 파일이 존재하는 경우)
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

app = FastAPI(
    title="AlloHub AI",
    version="2.0.0",
    description="상장기업 위험 진단 및 출자금 배분 지원 AI 서비스",
)

app.include_router(router)
app.include_router(disclosure_router)
