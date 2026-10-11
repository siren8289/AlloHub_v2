"""3단계: 전처리된 표를 CSV 파일로 저장한다."""
from data.etl.config import PROCESSED_DIR, RAW_DIR


def save_raw_csv(name, rows):
    """원본 행 리스트를 data/raw/{name}.csv 로 저장한다. (git에는 올리지 않는다)"""
    import pandas as pd

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"{name}.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def save_companies(frame):
    """진단·학습에 쓰는 최종 표를 data/processed/companies.csv 로 저장한다."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    path = PROCESSED_DIR / "companies.csv"
    frame.to_csv(path, index=False)
    return path
