"""ML·DL 모델이 함께 쓰는 입력 컬럼 정의.

학습할 때와 예측할 때 컬럼 이름·순서가 같아야 하므로 한 파일에 모아 둔다.

정답(distress)과 부도·영업정지·회생 건수는 입력에 넣지 않는다.
그 값을 넣으면 모델이 정답을 그냥 외우기 때문이다.
감자는 정답이 아니므로 입력으로 쓴다.
"""
import pandas as pd

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


def make_input_frame(row):
    """회사 1곳의 특징을 모델 입력용 표(1행)로 만든다."""
    return pd.DataFrame([{
        "market": row["market"],
        "has_dividend": int(row["has_dividend"]),
        "dividend_rate": float(row["dividend_rate"]),
        "profit_negative": int(row["profit_negative"]),
        "log_profit": float(row["log_profit"]),
        "par_price": float(row["par_price"]),
        # 감자 공시가 아주 많은 회사도 10건까지만 반영한다.
        "reduction_count": min(int(row["reduction_count"]), 10),
    }])
