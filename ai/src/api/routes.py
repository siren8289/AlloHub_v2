"""FastAPI 라우터 정의."""
from fastapi import APIRouter

from src.api.schemas import HealthResponse, ScreenRequest, ScreenResponse
from src.service.screener import screen

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    """서버 헬스체크 엔드포인트."""
    return {"status": "ok"}


@router.post("/api/v1/screen", response_model=ScreenResponse, tags=["Screen"])
def screen_api(request: ScreenRequest):
    """상장기업 위험 진단 (ML + DL + LLM 종합 평가)."""
    return screen(request.company_name.strip())
