"""전체 실행: 수집 → 전처리 → 저장.

저장소 루트에서
    python -m data.etl.run
"""
from data.etl.fetch import fetch_disclosures, fetch_listings
from data.etl.load import save_companies, save_raw_csv
from data.etl.transform import build_companies


def run_pipeline():
    print("[1/3] 상장 종목 수집")
    listings, bas_dt = fetch_listings()
    save_raw_csv("krx_listed", listings)
    print(f"  {bas_dt} 상장 {len(listings)}건")

    print("[2/3] 공시 수집 · 전처리")
    disclosures = fetch_disclosures()
    for name, rows in disclosures.items():
        save_raw_csv(name, rows)

    companies = build_companies(listings, disclosures)

    print("[3/3] CSV 저장")
    path = save_companies(companies)
    distress = int(companies["distress"].sum())
    print(f"완료: {path}")
    print(f"  종목 {len(companies)}개, 위험 라벨(부도·영업정지·회생) {distress}개")


if __name__ == "__main__":
    run_pipeline()
