"""FastAPI 요청 및 응답 Pydantic 스키마."""
from typing import Literal
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok", examples=["ok"])


class ScreenRequest(BaseModel):
    company_name: str = Field(
        min_length=1,
        max_length=100,
        description="진단 대상 상장기업 종목명 또는 법인명",
        examples=["삼성전자"],
    )


class ScreenResponse(BaseModel):
    company_name: str = Field(description="종목명", examples=["삼성전자"])
    corp_name: str = Field(description="법인명", examples=["삼성전자(주)"])
    stock_code: str = Field(description="단축코드", examples=["005930"])
    market: str = Field(description="시장구분", examples=["KOSPI"])
    bas_dt: str = Field(description="기준일자", examples=["20261010"])
    ml_score: float = Field(description="머신러닝(RF) 위험점수 (0~100)", examples=[15.2])
    dl_score: float = Field(description="딥러닝(MLP) 위험점수 (0~100)", examples=[18.4])
    score: float = Field(description="종합 위험점수 (0~100)", examples=[16.8])
    grade: Literal["stable", "warning", "danger"] = Field(
        description="진단 등급 (stable: 안정, warning: 주의, danger: 위험)",
        examples=["stable"],
    )
    dividend_rate: float = Field(description="최근 현금배당수익률 (%)", examples=[2.1])
    net_profit: float = Field(description="당기순이익 (원)", examples=[15000000000000.0])
    default_count: int = Field(description="부도 공시 건수", examples=[0])
    suspend_count: int = Field(description="영업정지 공시 건수", examples=[0])
    rehab_count: int = Field(description="회생절차 공시 건수", examples=[0])
    reduction_count: int = Field(description="감자 공시 건수", examples=[0])
    explanation: str = Field(description="진단 결과 요약 및 설명 문장")
    explanation_source: Literal["gemini", "basic"] = Field(
        description="설명 생성 출처 ('gemini' 또는 'basic')",
        examples=["basic"],
    )
