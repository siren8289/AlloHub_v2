# AlloHub v2

출자할 **상장기업의 위험**을 공공데이터로 진단하고, **출자 비율대로 투자금을 배분**하는 서비스입니다.
공공데이터 API 6개를 모아서 전처리하고, 머신러닝·딥러닝·LLM을 모두 사용합니다.

## 메인 기능 2개

| 기능 | 하는 일 | 사용 기술 |
| --- | --- | --- |
| 1. 기업 위험 진단 | 종목명으로 상장 정보와 공시(부도·영업정지·회생·감자·배당)를 찾고, 위험 점수와 쉬운 설명을 보여 줌 | **ML** + **DL** + **LLM** |
| 2. 출자금 배분 | 출자 비율대로 원 단위 금액을 나누고, 마지막 출자자가 남은 원을 받아 합계가 투자금과 같게 맞춤. 그 기업의 진단 결과도 같이 보여 줌 | 금액 규칙 + **ML** + **DL** + **LLM** |

- 위험 점수 0~100. 높을수록, 부도·영업정지·회생 공시가 있었던 회사와 특징이 비슷하다는 뜻입니다.
- 그 공시가 실제로 있으면 모델 점수와 상관없이 단계를 `위험`으로 올립니다.
- 감자 공시만 있거나 점수가 40 이상이면 `주의`, 아니면 `안정`입니다.
- 이 점수는 투자 권유가 아닙니다.

## 폴더 구조

IF_v2 처럼 역할별로 나눴습니다. (`ai` / `front` / `back` / `data`)

```text
AlloHub_v2/
├── data/                  공공데이터 수집·전처리
│   ├── etl/
│   │   ├── config.py      API 주소, 설정값
│   │   ├── fetch.py       1단계: API에서 받아 오기
│   │   ├── transform.py   2단계: 전처리 (숫자 정리, 법인별 최신 배당, 위험 라벨)
│   │   ├── load.py        3단계: CSV로 저장
│   │   └── run.py         전체 실행 (수집 → 전처리 → 저장)
│   ├── raw/               API 원본 (git 제외)
│   ├── processed/         전처리 결과 CSV
│   └── tests/
├── ai/                    AI 서버 (FastAPI, Python)
│   ├── train/             모델 학습 코드 (ML, DL)
│   ├── models/            학습된 모델 파일, 회사 표
│   ├── src/               서버 코드 (ML·DL 예측, 단계 규칙, LLM 설명)
│   └── tests/
├── back/                  백엔드 (Spring Boot, Java)
│   └── src/main/java/com/allohub/
│       ├── screen/        기능 1: 기업 진단
│       ├── allocation/    기능 2: 출자 배분
│       ├── ai/            AI 서버 호출
│       └── global/        오류 처리, 설정
├── front/                 프론트 (React + Vite, TypeScript)
│   └── src/
│       ├── pages/         진단 입력, 진단 결과, 배분 화면
│       └── api/           Spring 서버 호출 함수
├── compose.yaml           전체를 한 번에 실행 (Docker)
└── .env.example           환경변수 예시
```

데이터 흐름: `공공데이터 API → data(전처리) → ai(학습) → ai 서버 ← back(Spring) ← front(Vite)`

## 사용한 공공데이터 API 6개

| # | API | 용도 |
| --- | --- | --- |
| 1 | 금융위원회 KRX상장종목정보 `getItemInfo_V2` | 진단 대상 종목 목록 |
| 2 | 금융위원회 공시정보 배당 `getDiviDiscInfo_V2` | 배당률, 당기순이익, 액면가 |
| 3 | 부도발생 `getDishDiscInfo_V2` | 위험 라벨 |
| 4 | 영업정지 `getBusiSuspDiscInfo_V2` | 위험 라벨 |
| 5 | 회생절차개시신청 `getReviProcDiscInfo_V2` | 위험 라벨 |
| 6 | 감자결정 `getReduCapiDiscInfo_V2` | 모델 입력(특징) |

같은 인증키로 승인된 크라우드펀딩, 자산운용사, 자금지원·회수, 개인사업자평가, 사회적금융 API는 위 두 기능에 쓰지 않습니다.

KRX상장종목정보는 공공누리 제4유형(출처표시, 상업적 이용금지, 변경금지)입니다. 화면 아래에 출처를 적었습니다.

### 전처리 순서 (`data/etl/transform.py`)

1. 숫자 문자열 정리 (`"1,383"` → `1383`)
2. 법인등록번호가 없는 종목 제거
3. 배당 공시는 법인마다 가장 최근 1건만 사용
4. 부도·영업정지·회생·감자 건수를 법인등록번호로 붙임
5. 파생 변수 (배당 여부, 적자 여부, 순이익 로그, 위험 라벨)
6. 배당률은 0~100, 액면가는 0~100000 으로 자름

위험 라벨은 **부도·영업정지·회생이 1건이라도 있으면 1** 입니다. 이 라벨과 그 건수 자체는 모델 입력에 넣지 않습니다. (넣으면 모델이 정답을 외웁니다.)

## AI 모델

둘 다 같은 입력(시장, 배당 여부, 배당률, 적자 여부, 순이익 로그, 액면가, 감자 건수)으로 위험 확률을 예측하고, 0~100 점으로 바꿉니다.

| 구분 | 모델 | 파일 |
| --- | --- | --- |
| ML | scikit-learn 랜덤포레스트 | `ai/src/ml_model.py`, `ai/train/train_ml.py` |
| DL | PyTorch 다층 신경망(MLP) | `ai/src/dl_model.py`, `ai/train/train_dl.py` |
| LLM | Google Gemini (키가 없으면 기본 문장) | `ai/src/llm_explain.py` |

화면에 보이는 점수는 ML과 DL의 평균입니다. 성능 숫자는 `ai/models/metrics_ml.json`, `metrics_dl.json`에 있습니다.
위험 회사가 전체의 약 8%라서 정확도는 높아도 F1은 낮을 수 있습니다. 그래서 실제 부도·영업정지·회생 공시가 있으면 모델 점수보다 그 사실을 우선합니다.

## 실행 방법

### 0. 준비

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r data/requirements.txt -r ai/requirements.txt
pip install torch
cp data/.env.example data/.env     # 공공데이터 인증키를 채운다
cp ai/.env.example ai/.env         # (선택) Gemini 키
```

`data/.env`에 넣을 키

- `DATA_GO_KR_KEY`: 공공데이터포털(data.go.kr) 일반 인증키 (Decoding)

### 1. 데이터 수집·전처리 (저장소 루트에서)

```bash
python -m data.etl.run
```

최근 평일 상장 목록과 공시 전체를 받아 `data/processed/companies.csv`를 만듭니다.

### 2. 모델 학습

```bash
python -m ai.train.train_ml
python -m ai.train.train_dl
```

### 3. 서버 실행 (터미널 3개)

```bash
# AI 서버 (8000)
cd ai && python -m uvicorn src.main:app --port 8000

# 백엔드 (8080) - 로컬에서는 H2 메모리 DB를 쓴다
cd back && ./gradlew bootRun

# 프론트 (5173)
cd front && npm install && npm run dev
```

브라우저에서 http://localhost:5173 접속.

### Docker로 한 번에 실행

```bash
cp .env.example .env      # DB_PASSWORD, (선택) GEMINI_API_KEY 입력
docker compose up --build
# 또는 서버에서
bash scripts/deploy.sh
```

http://localhost 접속. 컨테이너 안에서는 front(nginx)가 `/api`를 Spring으로 넘긴다.

## CI

푸시하면 GitHub Actions가 data / ai / back / front 테스트와 `docker compose config`를 실행한다. (`.github/workflows/ci.yml`)

## API

| 메서드 | 주소 | 설명 |
| --- | --- | --- |
| POST | `/api/screens` | 기업 진단 실행 + 저장 |
| GET | `/api/screens/{id}` | 진단 결과 조회 |
| GET | `/api/screens` | 최근 진단 10건 |
| POST | `/api/allocations` | 출자금 배분 + 기업 진단 |
| GET | `/api/allocations/{id}` | 배분 결과 조회 |
| GET | `/api/allocations` | 최근 배분 10건 |
| GET | `/api/health` | 서버 상태 확인 |

AI 서버(FastAPI)는 Spring만 호출합니다: `POST /api/v1/screen`

## 테스트

```bash
python -m pytest data/tests          # 전처리
cd ai && python -m pytest            # AI 서버
cd back && ./gradlew test            # 백엔드
cd front && npm run build            # 프론트 (타입 검사 + 빌드)
```
