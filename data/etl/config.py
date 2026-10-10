"""데이터 수집 설정값을 한 곳에 모아 둔다.

사용하는 공공데이터 API 6개 (금융위원회, 모두 활용 승인된 개발계정)
  1. KRX 상장종목정보          어떤 회사가 상장돼 있는지
  2. 배당 공시                배당률, 당기순이익
  3. 부도발생 공시            위험 신호
  4. 영업정지 공시            위험 신호
  5. 회생절차 개시신청 공시    위험 신호
  6. 감자 결정 공시            자본이 줄었다는 신호

크라우드펀딩, 자산운용사, 사회적금융 등은 이번 두 기능(기업 진단, 출자 배분)에
쓰지 않아서 수집하지 않는다.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# data/ 폴더 위치. 어디서 실행해도 같은 폴더를 가리키도록 파일 기준으로 계산한다.
DATA_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = DATA_DIR / "raw"              # API 원본
PROCESSED_DIR = DATA_DIR / "processed"  # 전처리가 끝난 CSV

# data/.env 에서 인증키를 읽는다. (.env 는 git에 올리지 않는다)
load_dotenv(DATA_DIR / ".env")
SERVICE_KEY = os.getenv("DATA_GO_KR_KEY", "")

# 금융위원회 API 공통 주소
FSC = "https://apis.data.go.kr/1160100"

# 1. 상장 종목. basDt(기준일자)를 넣으면 그 날 상장 목록만 온다.
KRX_ITEM_URL = f"{FSC}/GetKrxListedInfoService_V2/getItemInfo_V2"

# 2~6. 공시. 날짜를 비우면 저장된 전체 기간이 온다.
DISCLOSURE_URLS = {
    "dividend": f"{FSC}/service/GetDiscInfoService_V2/getDiviDiscInfo_V2",
    "default": f"{FSC}/service/GetDiscInfoService_V2/getDishDiscInfo_V2",
    "suspend": f"{FSC}/service/GetDiscInfoService_V2/getBusiSuspDiscInfo_V2",
    "rehab": f"{FSC}/service/GetDiscInfoService_V2/getReviProcDiscInfo_V2",
    "reduction": f"{FSC}/service/GetDiscInfoService_V2/getReduCapiDiscInfo_V2",
}

# 한 번 호출할 때 받을 최대 건수
ROWS_PER_PAGE = 1000

# 상장 목록은 휴일·데이터 반영 전에 0건일 수 있다. 최근 평일을 최대 이 만큼 거슬러 본다.
LISTING_LOOKBACK_DAYS = 14
