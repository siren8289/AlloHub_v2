"""AlloHub AI 서버 (FastAPI). Spring 백엔드가 내부에서 호출한다.

POST /api/v1/screen   상장기업 위험 진단 (ML + DL + LLM)
"""
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, Field

from src.service import screen

# ai/.env 에서 GEMINI_API_KEY 를 읽는다. (없으면 LLM 대신 기본 문장을 쓴다)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="AlloHub AI", version="2.0.0")


class ScreenRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=100, examples=["삼성전자"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/screen")
def screen_api(request: ScreenRequest):
    return screen(request.company_name.strip())
