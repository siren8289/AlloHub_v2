"""ML·DL 모델이 함께 쓰는 입력 컬럼 정의 및 피처 추출.

학습과 추론 시 동일한 컬럼 순서 및 전처리 로직이 적용되어야 합니다.
정답(distress)과 부도·영업정지·회생 건수는 모델 입력에 포함하지 않습니다.
"""
import pandas as pd

from src.core.config import MAX_REDUCTION_COUNT_INPUT

# 글자로 된 값(범주형) → 원-핫 인코딩
CATEGORY_COLUMNS = ["market"]

# 숫자로 된 값(수치형)
NUMBER_COLUMNS = [
    "has_dividend",
    "dividend_rate",
    "profit_negative",
    "log_profit",
    "par_price",
    "reduction_count",
]

FEATURE_COLUMNS = CATEGORY_COLUMNS + NUMBER_COLUMNS
TARGET_COLUMN = "distress"  # 1 = 부도·영업정지·회생 공시가 있음


def make_input_frame(row: pd.Series | dict) -> pd.DataFrame:
    """회사 1곳의 특성을 모델 입력용 DataFrame(1행)으로 생성합니다."""
    return pd.DataFrame([{
        "market": row["market"],
        "has_dividend": int(row["has_dividend"]),
        "dividend_rate": float(row["dividend_rate"]),
        "profit_negative": int(row["profit_negative"]),
        "log_profit": float(row["log_profit"]),
        "par_price": float(row["par_price"]),
        "reduction_count": min(int(row["reduction_count"]), MAX_REDUCTION_COUNT_INPUT),
    }])
