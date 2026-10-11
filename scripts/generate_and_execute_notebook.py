"""In-process InteractiveShell을 이용한 Jupyter 노트북 실행 및 생성 스크립트.

Sandbox 환경에서 TCP/ZMQ 소켓 통신 의존성 없이 완벽하게 실행되며,
모든 셀의 execution_count와 stdout, DataFrame HTML/text 출력을 표준 Jupyter 포맷으로 기록합니다.
"""
import contextlib
import io
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebook" / "model_evaluation.ipynb"

# Sandbox 내 임시 디렉토리 설정
tmp_dir = ROOT / ".tmp_ipython"
tmp_dir.mkdir(parents=True, exist_ok=True)
os.environ["IPYTHONDIR"] = str(tmp_dir)

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook, new_output
from IPython.core.interactiveshell import InteractiveShell
import pandas as pd


def create_cells():
    cells = []

    # Title & Overview
    cells.append(new_markdown_cell(
        "# AlloHub v2 AI 모델 테스트 및 수치 검증 노트북\n\n"
        "이 노트북은 **AlloHub v2**의 핵심 AI 모델 및 알고리즘을 종합적으로 테스트하고 실제 수치 계산을 수행합니다.\n\n"
        "### 검증 대상 및 구성:\n"
        "1. **데이터 적재 및 수치 통계 분석**: 공공데이터 6종 기반 상장종목(2,737개사)의 시장 분포, 위험 라벨(부도·영업정지·회생), 배당, 감자, 순이익 통계\n"
        "2. **피처 엔지니어링 & 전처리 검증**: 범주형 원-핫 인코딩, 수치형 스케일링, 감자 상한 클리핑(최대 10건) 검증\n"
        "3. **머신러닝(RandomForest) 모델 수치 평가**: `risk_rf.joblib` 성능 지표 (Accuracy, Precision, Recall, F1, ROC-AUC), 혼동 행렬, 피처 중요도 분석\n"
        "4. **딥러닝(PyTorch MLP) 모델 수치 평가**: `risk_mlp.pt` 신경망 성능 지표, 손실값, ML vs DL 수치 비교 및 상관관계 분석\n"
        "5. **앙상블 종합 점수 및 등급 규칙 수치 검증**: ML+DL 평균 점수 분포, 위험 등급(안정·주의·위험) 분포 및 공시 사실 우선 규칙 검증\n"
        "6. **기능 2 - 출자금 원 단위 배분(Allocation Split) 수치 계산**: 백엔드 AllocationCalculator와 일치하는 원 단위 분할 및 절사 잔여액 배분 검증\n"
        "7. **실제 상장 종목 E2E 진단 케이스 스터디**: 삼성전자(KOSPI 대형주), 카카오, 감자 발생 종목, 고위험 공시 종목 등 실제 진단 수치 확인"
    ))

    # Cell 1: Environment & Setup
    cells.append(new_code_cell(
        "import sys\n"
        "import json\n"
        "from pathlib import Path\n"
        "from decimal import Decimal, ROUND_DOWN\n"
        "import pandas as pd\n"
        "import numpy as np\n"
        "import torch\n\n"
        "# 프로젝트 루트 및 ai 경로 동적 감지\n"
        "curr = Path.cwd().resolve()\n"
        "if (curr / 'ai').exists():\n"
        "    PROJECT_ROOT = curr\n"
        "elif (curr.parent / 'ai').exists():\n"
        "    PROJECT_ROOT = curr.parent\n"
        "else:\n"
        "    PROJECT_ROOT = Path('..').resolve()\n\n"
        "AI_DIR = PROJECT_ROOT / 'ai'\n"
        "if str(AI_DIR) not in sys.path:\n"
        "    sys.path.insert(0, str(AI_DIR))\n"
        "if str(PROJECT_ROOT) not in sys.path:\n"
        "    sys.path.insert(0, str(PROJECT_ROOT))\n\n"
        "# 모듈화된 패키지 임포트\n"
        "from src.core.config import (\n"
        "    MODELS_DIR, DATA_CSV, MODELS_CSV,\n"
        "    MODEL_RF_PATH, MODEL_MLP_PATH, PREPROCESSOR_MLP_PATH,\n"
        "    GRADE_NAMES, SCORE_THRESHOLD_WARNING\n"
        ")\n"
        "from src.scoring.features import (\n"
        "    FEATURE_COLUMNS, CATEGORY_COLUMNS, NUMBER_COLUMNS,\n"
        "    TARGET_COLUMN, make_input_frame\n"
        ")\n"
        "from src.scoring.rules import grade_of\n"
        "from src.scoring.company import load_companies, find_company, normalize_name\n"
        "from src.inference.ml_risk import load_ml_model, predict_ml\n"
        "from src.inference.dl_risk import load_dl_model, predict_dl, RiskMLP\n"
        "from src.service.screener import screen\n\n"
        "print('✓ 프로젝트 환경 설정 완료')\n"
        "print(f'  - Project Root: {PROJECT_ROOT}')\n"
        "print(f'  - AI Directory: {AI_DIR}')\n"
        "print(f'  - PyTorch Version: {torch.__version__}')"
    ))

    # Section 1 Markdown
    cells.append(new_markdown_cell(
        "## 1. 데이터 적재 및 수치 통계 분석\n"
        "공공데이터 API 6종(KRX상장정보, 배당공시, 부도, 영업정지, 회생, 감자)을 전처리한 전체 상장종목 데이터셋을 로드하고 주요 수치 통계를 확인합니다."
    ))

    # Cell 2: Data Loading
    cells.append(new_code_cell(
        "df = load_companies()\n"
        "print(f'총 상장 기업 수: {len(df):,}개사')\n"
        "print(f'데이터셋 컬럼 수: {df.shape[1]}개')\n"
        "print('\\n[상위 5개사 데이터 미리보기]')\n"
        "display_cols = ['item_name', 'market', 'has_dividend', 'dividend_rate', 'profit_negative', 'net_profit', 'reduction_count', 'distress']\n"
        "df[display_cols].head()"
    ))

    # Cell 3: Distress & Disclosures
    cells.append(new_code_cell(
        "# 위험 라벨 및 공시 통계\n"
        "distress_counts = df['distress'].value_counts()\n"
        "distress_rate = df['distress'].mean() * 100\n\n"
        "default_cos = int((df['default_count'] > 0).sum())\n"
        "suspend_cos = int((df['suspend_count'] > 0).sum())\n"
        "rehab_cos = int((df['rehab_count'] > 0).sum())\n"
        "reduction_cos = int((df['reduction_count'] > 0).sum())\n\n"
        "stats_summary = pd.DataFrame({\n"
        "    '구분': ['정상 기업 (distress=0)', '위험 기업 (distress=1)', '부도 공시 기업', '영업정지 공시 기업', '회생 공시 기업', '감자 공시 기업'],\n"
        "    '기업 수': [int(distress_counts.get(0, 0)), int(distress_counts.get(1, 0)), default_cos, suspend_cos, rehab_cos, reduction_cos],\n"
        "    '비율 (%)': [\n"
        "        round(100 - distress_rate, 2),\n"
        "        round(distress_rate, 2),\n"
        "        round(default_cos / len(df) * 100, 2),\n"
        "        round(suspend_cos / len(df) * 100, 2),\n"
        "        round(rehab_cos / len(df) * 100, 2),\n"
        "        round(reduction_cos / len(df) * 100, 2)\n"
        "    ]\n"
        "})\n"
        "print('=== 상장 기업 위험 및 공시 현황 ===')\n"
        "stats_summary"
    ))

    # Cell 4: Market Stats
    cells.append(new_code_cell(
        "# 시장별 기업 수 및 위험 비율\n"
        "market_summary = df.groupby('market').agg(\n"
        "    총기업수=('item_name', 'count'),\n"
        "    위험기업수=('distress', 'sum'),\n"
        "    위험비율_pct=('distress', lambda x: round(x.mean() * 100, 2)),\n"
        "    평균배당률=('dividend_rate', lambda x: round(x.mean(), 2)),\n"
        "    적자기업비율_pct=('profit_negative', lambda x: round(x.mean() * 100, 2))\n"
        ").reset_index()\n\n"
        "print('=== 시장별 기업 분포 및 위험 지표 ===')\n"
        "market_summary"
    ))

    # Cell 5: Descriptive Stats & Correlation
    cells.append(new_code_cell(
        "# 주요 수치형 변수 기술통계량\n"
        "num_cols = ['dividend_rate', 'net_profit', 'log_profit', 'par_price', 'reduction_count']\n"
        "desc = df[num_cols].describe().round(2)\n"
        "print('=== 주요 수치형 변수 요약 통계 ===')\n"
        "print(desc)\n\n"
        "# 타겟(distress)과의 상관계수 계산\n"
        "correlations = {}\n"
        "for col in ['has_dividend', 'dividend_rate', 'profit_negative', 'log_profit', 'par_price', 'reduction_count']:\n"
        "    correlations[col] = {\n"
        "        '피어슨 상관계수': round(float(df[col].corr(df['distress'])), 4),\n"
        "        '스피어만 순위상관계수': round(float(df[col].corr(df['distress'], method='spearman')), 4)\n"
        "    }\n"
        "corr_df = pd.DataFrame(correlations).T\n"
        "print('\\n=== 피처와 위험 라벨(distress) 간 상관관계 ===')\n"
        "corr_df"
    ))

    # Section 2 Markdown
    cells.append(new_markdown_cell(
        "## 2. 피처 엔지니어링 및 전처리 수치 검증\n"
        "모델 입력으로 사용되는 7개 피처(`market`, `has_dividend`, `dividend_rate`, `profit_negative`, `log_profit`, `par_price`, `reduction_count`)와 감자 건수 클리핑 규칙(최대 10건)을 검증합니다."
    ))

    # Cell 6: Feature Extraction
    cells.append(new_code_cell(
        "# 임의의 테스트 샘플로 make_input_frame 동작 검증\n"
        "sample_row = df.iloc[0].to_dict()\n"
        "sample_input = make_input_frame(sample_row)\n\n"
        "print('피처 컬럼 목록:', FEATURE_COLUMNS)\n"
        "print('생성된 피처 프레임 형태:', sample_input.shape)\n"
        "print('\\n피처 프레임 내용:')\n"
        "print(sample_input.to_dict(orient='records')[0])\n\n"
        "# 감자 상한(10) 클리핑 테스트\n"
        "test_high_reduction = sample_row.copy()\n"
        "test_high_reduction['reduction_count'] = 45\n"
        "clipped_input = make_input_frame(test_high_reduction)\n"
        "print(f'\\n감자 45건 입력 시 클리핑 결과: {clipped_input[\"reduction_count\"].iloc[0]}건 (기대값: 10)')\n"
        "assert clipped_input['reduction_count'].iloc[0] == 10, '감자 클리핑 오류'\n"
        "print('✓ 피처 전처리 및 클리핑 검증 통과')"
    ))

    # Section 3 Markdown
    cells.append(new_markdown_cell(
        "## 3. 머신러닝(RandomForest) 모델 수치 평가\n"
        "`models/risk_rf.joblib` 모델의 정확도, F1-Score, ROC-AUC, 혼동 행렬 및 피처 중요도(Feature Importance)를 산출합니다."
    ))

    # Cell 7: ML Evaluation
    cells.append(new_code_cell(
        "from sklearn.model_selection import train_test_split\n"
        "from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix\n\n"
        "ml_model = load_ml_model()\n\n"
        "# 동일한 재현성을 갖는 학습/테스트 분할 (80:20 Stratified)\n"
        "X = df[FEATURE_COLUMNS]\n"
        "y = df[TARGET_COLUMN].astype(int)\n"
        "X_train, X_test, y_train, y_test = train_test_split(\n"
        "    X, y, test_size=0.2, random_state=42, stratify=y\n"
        ")\n\n"
        "# 예측 수행\n"
        "y_prob_ml = ml_model.predict_proba(X_test)[:, 1]\n"
        "y_pred_ml = (y_prob_ml >= 0.5).astype(int)\n\n"
        "# 지표 계산\n"
        "acc_ml = float(accuracy_score(y_test, y_pred_ml))\n"
        "prec_ml = float(precision_score(y_test, y_pred_ml, zero_division=0))\n"
        "rec_ml = float(recall_score(y_test, y_pred_ml, zero_division=0))\n"
        "f1_ml = float(f1_score(y_test, y_pred_ml, zero_division=0))\n"
        "auc_ml = float(roc_auc_score(y_test, y_prob_ml))\n\n"
        "cm_ml = confusion_matrix(y_test, y_pred_ml)\n\n"
        "print('=== 머신러닝(RandomForest) 평가 결과 (테스트셋 N=548) ===')\n"
        "print(f'Accuracy  : {acc_ml:.4f} ({acc_ml*100:.2f}%)')\n"
        "print(f'Precision : {prec_ml:.4f}')\n"
        "print(f'Recall    : {rec_ml:.4f}')\n"
        "print(f'F1-Score  : {f1_ml:.4f}')\n"
        "print(f'ROC-AUC   : {auc_ml:.4f}')\n\n"
        "cm_df_ml = pd.DataFrame(\n"
        "    cm_ml,\n"
        "    index=['실제 정상(0)', '실제 위험(1)'],\n"
        "    columns=['예측 정상(0)', '예측 위험(1)']\n"
        ")\n"
        "print('\\n[혼동 행렬 (Confusion Matrix)]')\n"
        "cm_df_ml"
    ))

    # Cell 8: ML Feature Importance
    cells.append(new_code_cell(
        "# 파이프라인 내부의 원-핫 인코더 피처 이름과 피처 중요도 추출\n"
        "rf_estimator = ml_model.named_steps['model']\n"
        "preprocessor = ml_model.named_steps['preprocess']\n\n"
        "cat_features = preprocessor.named_transformers_['category'].get_feature_names_out(CATEGORY_COLUMNS).tolist()\n"
        "all_feature_names = cat_features + NUMBER_COLUMNS\n"
        "importances = rf_estimator.feature_importances_\n\n"
        "fi_df = pd.DataFrame({\n"
        "    'Feature': all_feature_names,\n"
        "    'Importance': importances,\n"
        "    'Percentage (%)': (importances / importances.sum() * 100).round(2)\n"
        "}).sort_values('Importance', ascending=False).reset_index(drop=True)\n\n"
        "print('=== 머신러닝 피처 중요도 순위 (Feature Importance Ranking) ===')\n"
        "fi_df"
    ))

    # Section 4 Markdown
    cells.append(new_markdown_cell(
        "## 4. 딥러닝(PyTorch MLP) 모델 수치 평가\n"
        "`models/risk_mlp.pt` 모델의 성능 지표를 산출하고, 머신러닝 모델과의 성능 비교 및 상관관계를 분석합니다."
    ))

    # Cell 9: DL Evaluation
    cells.append(new_code_cell(
        "dl_model, dl_preprocessor = load_dl_model()\n\n"
        "# DL 전처리 수행\n"
        "X_test_dl = dl_preprocessor.transform(X_test).astype(np.float32)\n\n"
        "with torch.no_grad():\n"
        "    logits = dl_model(torch.from_numpy(X_test_dl)).squeeze()\n"
        "    y_prob_dl = torch.sigmoid(logits).numpy()\n\n"
        "y_pred_dl = (y_prob_dl >= 0.5).astype(int)\n\n"
        "# 지표 계산\n"
        "acc_dl = float(accuracy_score(y_test, y_pred_dl))\n"
        "prec_dl = float(precision_score(y_test, y_pred_dl, zero_division=0))\n"
        "rec_dl = float(recall_score(y_test, y_pred_dl, zero_division=0))\n"
        "f1_dl = float(f1_score(y_test, y_pred_dl, zero_division=0))\n"
        "auc_dl = float(roc_auc_score(y_test, y_prob_dl))\n\n"
        "bce_loss = float(torch.nn.functional.binary_cross_entropy(\n"
        "    torch.from_numpy(y_prob_dl),\n"
        "    torch.from_numpy(y_test.to_numpy().astype(np.float32))\n"
        ").item())\n\n"
        "print('=== 딥러닝(PyTorch MLP) 평가 결과 (테스트셋 N=548) ===')\n"
        "print(f'Accuracy  : {acc_dl:.4f} ({acc_dl*100:.2f}%)')\n"
        "print(f'Precision : {prec_dl:.4f}')\n"
        "print(f'Recall    : {rec_dl:.4f}')\n"
        "print(f'F1-Score  : {f1_dl:.4f}')\n"
        "print(f'ROC-AUC   : {auc_dl:.4f}')\n"
        "print(f'BCE Loss  : {bce_loss:.4f}')\n\n"
        "# ML vs DL 비교 테이블\n"
        "comparison_df = pd.DataFrame({\n"
        "    '평가지표': ['정확도(Accuracy)', '정밀도(Precision)', '재현율(Recall)', 'F1-Score', 'ROC-AUC'],\n"
        "    'ML (RandomForest)': [round(acc_ml, 4), round(prec_ml, 4), round(rec_ml, 4), round(f1_ml, 4), round(auc_ml, 4)],\n"
        "    'DL (PyTorch MLP)': [round(acc_dl, 4), round(prec_dl, 4), round(rec_dl, 4), round(f1_dl, 4), round(auc_dl, 4)],\n"
        "    '차이 (DL - ML)': [round(acc_dl - acc_ml, 4), round(prec_dl - prec_ml, 4), round(rec_dl - rec_ml, 4), round(f1_dl - f1_ml, 4), round(auc_dl - auc_ml, 4)]\n"
        "})\n"
        "print('\\n=== ML vs DL 모델 성능 비교 ===')\n"
        "comparison_df"
    ))

    # Cell 10: ML vs DL Correlation
    cells.append(new_code_cell(
        "# 전체 2,737개사에 대한 ML 및 DL 예측 점수(0~100) 산출\n"
        "all_ml_probs = ml_model.predict_proba(X)[:, 1] * 100\n"
        "all_X_dl = dl_preprocessor.transform(X).astype(np.float32)\n\n"
        "with torch.no_grad():\n"
        "    all_dl_probs = torch.sigmoid(dl_model(torch.from_numpy(all_X_dl)).squeeze()).numpy() * 100\n\n"
        "score_diff = np.abs(all_ml_probs - all_dl_probs)\n"
        "score_corr = float(np.corrcoef(all_ml_probs, all_dl_probs)[0, 1])\n\n"
        "diff_stats = pd.Series(score_diff).describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]).round(2)\n"
        "print('=== ML vs DL 점수 일치도 및 상관관계 분석 (전체 2,737개사) ===')\n"
        "print(f'피어슨 상관계수 (ML 점수 vs DL 점수): {score_corr:.4f}')\n"
        "print(f'평균 절대 오차 (MAE): {np.mean(score_diff):.2f}점')\n"
        "print('\\n점수 차이(절댓값) 분포 통계:')\n"
        "print(diff_stats)"
    ))

    # Section 5 Markdown
    cells.append(new_markdown_cell(
        "## 5. 앙상블 종합 점수 및 등급 규칙 수치 검증\n"
        "ML 점수와 DL 점수의 산술 평균으로 최종 참고 위험 점수를 계산하고, 등급 판정 규칙(`stable`, `warning`, `danger`)을 적용한 전수 분포를 분석합니다."
    ))

    # Cell 11: Ensemble Grading
    cells.append(new_code_cell(
        "final_scores = np.round((all_ml_probs + all_dl_probs) / 2, 1)\n\n"
        "# 전수 등급 계산\n"
        "assigned_grades = []\n"
        "danger_due_to_disclosure = 0\n"
        "warning_due_to_score = 0\n"
        "warning_due_to_reduction = 0\n\n"
        "for i, row in df.iterrows():\n"
        "    s = final_scores[i]\n"
        "    g = grade_of(s, row)\n"
        "    assigned_grades.append(g)\n"
        "    \n"
        "    if g == 'danger':\n"
        "        if row['default_count'] > 0 or row['suspend_count'] > 0 or row['rehab_count'] > 0:\n"
        "            danger_due_to_disclosure += 1\n"
        "    elif g == 'warning':\n"
        "        if s >= SCORE_THRESHOLD_WARNING:\n"
        "            warning_due_to_score += 1\n"
        "        elif row['reduction_count'] > 0:\n"
        "            warning_due_to_reduction += 1\n\n"
        "grade_counts = pd.Series(assigned_grades).value_counts()\n"
        "grade_summary = pd.DataFrame({\n"
        "    '등급': ['안정 (stable)', '주의 (warning)', '위험 (danger)'],\n"
        "    '기업 수': [int(grade_counts.get('stable', 0)), int(grade_counts.get('warning', 0)), int(grade_counts.get('danger', 0))],\n"
        "    '비율 (%)': [\n"
        "        round(grade_counts.get('stable', 0) / len(df) * 100, 2),\n"
        "        round(grade_counts.get('warning', 0) / len(df) * 100, 2),\n"
        "        round(grade_counts.get('danger', 0) / len(df) * 100, 2)\n"
        "    ],\n"
        "    '설명': [\n"
        "        '위험점수 40점 미만 & 부도·영업정지·회생·감자 없음',\n"
        "        '점수 40점 이상(또는 감자 공시 이력)',\n"
        "        '부도·영업정지·회생 공시 발생 (사실 우선 원칙)'\n"
        "    ]\n"
        "})\n\n"
        "print('=== 전수 위험 등급 판정 분포 (N=2,737) ===')\n"
        "print(grade_summary)\n\n"
        "print('\\n=== 규칙 적용 세부 분석 ===')\n"
        "print(f'- 부도·영업정지·회생 공시로 위험(danger) 등급 승격된 기업: {danger_due_to_disclosure}개사')\n"
        "print(f'- 모델 점수 40점 이상으로 주의(warning) 등급 부여된 기업: {warning_due_to_score}개사')\n"
        "print(f'- 감자 공시 이력으로 주의(warning) 등급 부여된 기업: {warning_due_to_reduction}개사')"
    ))

    # Section 6 Markdown
    cells.append(new_markdown_cell(
        "## 6. 기능 2 - 출자금 원 단위 배분(Allocation Split) 수치 계산 검증\n"
        "Spring 백엔드의 `AllocationCalculator.java`와 동일한 원 단위 분할 및 절사 잔여액 배분 알고리즘을 구현하고, 다양한 출자 시나리오에서 오차 0원 검증을 수행합니다."
    ))

    # Cell 12: Allocation Calculation
    cells.append(new_code_cell(
        "def split_allocation(total_amount: int, ratios: list[float]) -> list[int]:\n"
        "    '''\n"
        "    백엔드 AllocationCalculator.split과 동일한 로직:\n"
        "    각 출자자 배분액 = floor(total_amount * ratio / 100)\n"
        "    마지막 출자자가 잔여 원을 모두 가져가 합계 = 투자금 보장\n"
        "    '''\n"
        "    amounts = []\n"
        "    used = 0\n"
        "    for i, ratio in enumerate(ratios):\n"
        "        is_last = (i == len(ratios) - 1)\n"
        "        if is_last:\n"
        "            amounts.append(total_amount - used)\n"
        "        else:\n"
        "            part = int(Decimal(str(total_amount)) * Decimal(str(ratio)) / Decimal('100'))\n"
        "            amounts.append(part)\n"
        "            used += part\n"
        "    return amounts\n\n"
        "# 시나리오 1: 1억원 3명 균등 (33.33%, 33.33%, 33.34%)\n"
        "test_1_total = 100_000_000\n"
        "test_1_ratios = [33.33, 33.33, 33.34]\n"
        "res_1 = split_allocation(test_1_total, test_1_ratios)\n\n"
        "# 시나리오 2: 10억원 3명 차등 (50.0%, 30.0%, 20.0%)\n"
        "test_2_total = 1_000_000_000\n"
        "test_2_ratios = [50.0, 30.0, 20.0]\n"
        "res_2 = split_allocation(test_2_total, test_2_ratios)\n\n"
        "# 시나리오 3: 소수점 오차가 발생하는 비정형 금액 (77,777,777원)\n"
        "test_3_total = 77_777_777\n"
        "test_3_ratios = [14.28, 28.57, 57.15]\n"
        "res_3 = split_allocation(test_3_total, test_3_ratios)\n\n"
        "alloc_df = pd.DataFrame([\n"
        "    {'시나리오': '1. 1억원 균등 배분', '총투자금': f'{test_1_total:,}원', '비율 목록': str(test_1_ratios), '배분액 결과': [f'{x:,}원' for x in res_1], '합계 일치': sum(res_1) == test_1_total},\n"
        "    {'시나리오': '2. 10억원 차등 배분', '총투자금': f'{test_2_total:,}원', '비율 목록': str(test_2_ratios), '배분액 결과': [f'{x:,}원' for x in res_2], '합계 일치': sum(res_2) == test_2_total},\n"
        "    {'시나리오': '3. 77,777,777원 난수 배분', '총투자금': f'{test_3_total:,}원', '비율 목록': str(test_3_ratios), '배분액 결과': [f'{x:,}원' for x in res_3], '합계 일치': sum(res_3) == test_3_total},\n"
        "])\n\n"
        "print('=== 출자금 배분 알고리즘 수치 검증 ===')\n"
        "alloc_df"
    ))

    # Section 7 Markdown
    cells.append(new_markdown_cell(
        "## 7. 실제 상장 종목 E2E 진단 케이스 스터디\n"
        "모듈화된 AI 파이프라인(`src.service.screener.screen`)을 통해 실제 주요 기업들의 진단 수치 및 규칙 적용 결과를 확인합니다."
    ))

    # Cell 13: Real Company Screening
    cells.append(new_code_cell(
        "test_target_companies = ['삼성전자', '카카오']\n\n"
        "# 감자 이력만 있는 기업(부도/정지/회생 없음) 1곳 선정 -> '주의' 등급 규칙 검증\n"
        "red_only = df[(df['reduction_count'] > 0) & (df['default_count'] == 0) & (df['suspend_count'] == 0) & (df['rehab_count'] == 0)]['item_name'].tolist()\n"
        "if red_only:\n"
        "    test_target_companies.append(red_only[0])\n\n"
        "# 부도/영업정지/회생 이력이 있는 고위험 기업 1곳 선정 -> '위험' 등급 자동 승격 검증\n"
        "danger_cos = df[(df['default_count'] > 0) | (df['suspend_count'] > 0) | (df['rehab_count'] > 0)]['item_name'].tolist()\n"
        "if danger_cos:\n"
        "    test_target_companies.append(danger_cos[0])\n\n"
        "case_results = []\n"
        "for cname in test_target_companies:\n"
        "    res = screen(cname)\n"
        "    case_results.append({\n"
        "        '종목명': res['company_name'],\n"
        "        '단축코드': res['stock_code'],\n"
        "        '시장': res['market'],\n"
        "        'ML점수': res['ml_score'],\n"
        "        'DL점수': res['dl_score'],\n"
        "        '종합점수': res['score'],\n"
        "        '판정등급': GRADE_NAMES.get(res['grade'], res['grade']),\n"
        "        '배당률': f\"{res['dividend_rate']}%\",\n"
        "        '순이익(억원)': f\"{res['net_profit'] / 1e8:,.1f}\",\n"
        "        '부도/정지/회생': f\"{res['default_count']}/{res['suspend_count']}/{res['rehab_count']}\",\n"
        "        '감자건수': res['reduction_count'],\n"
        "        '설명 출처': res['explanation_source']\n"
        "    })\n\n"
        "case_df = pd.DataFrame(case_results)\n"
        "print('=== 실제 상장 기업 E2E 진단 결과 요약 ===')\n"
        "case_df"
    ))

    # Cell 14: Sample Explanation
    cells.append(new_code_cell(
        "print('=== 대표 진단 설명 출력 예시 (삼성전자) ===')\n"
        "sample_screen = screen('삼성전자')\n"
        "print(sample_screen['explanation'])\n"
        "print(f\"\\n[출처: {sample_screen['explanation_source']}]\")"
    ))

    return cells


def execute_and_build():
    cells = create_cells()
    shell = InteractiveShell.instance()

    executed_cells = []
    exec_count = 1

    print("노트북 셀 실행 시작...")
    for idx, cell in enumerate(cells):
        if cell.cell_type == "markdown":
            executed_cells.append(cell)
            continue

        print(f"[{exec_count}] 코드 셀 실행 중 (셀 {idx+1}/{len(cells)})...")
        code = cell.source

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            res = shell.run_cell(code)

        stdout_text = stdout_buf.getvalue()
        stderr_text = stderr_buf.getvalue()

        outputs = []
        if stdout_text:
            outputs.append(new_output(output_type="stream", name="stdout", text=stdout_text))
        if stderr_text:
            outputs.append(new_output(output_type="stream", name="stderr", text=stderr_text))

        if res.error_in_exec:
            print(f"  [오류 발생]: {res.error_in_exec}")
            ename = type(res.error_in_exec).__name__
            evalue = str(res.error_in_exec)
            outputs.append(new_output(
                output_type="error",
                ename=ename,
                evalue=evalue,
                traceback=[f"{ename}: {evalue}"]
            ))
        elif res.result is not None:
            val = res.result
            if isinstance(val, pd.DataFrame):
                data = {
                    "text/plain": repr(val),
                    "text/html": val._repr_html_() if hasattr(val, "_repr_html_") else val.to_html()
                }
            elif isinstance(val, pd.Series):
                data = {
                    "text/plain": repr(val),
                    "text/html": val.to_frame()._repr_html_() if hasattr(val.to_frame(), "_repr_html_") else val.to_string()
                }
            else:
                data = {
                    "text/plain": repr(val)
                }
            outputs.append(new_output(
                output_type="execute_result",
                data=data,
                execution_count=exec_count
            ))

        cell.execution_count = exec_count
        cell.outputs = outputs
        executed_cells.append(cell)
        exec_count += 1

    nb = new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11.9"
        }
    }
    nb.cells = executed_cells

    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(NOTEBOOK_PATH, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)

    print(f"✓ 모든 셀 실행 완료 및 노트북 저장 성공: {NOTEBOOK_PATH}")
    print(f"  - 총 셀 수: {len(executed_cells)} (코드 셀: {exec_count-1}개)")


if __name__ == "__main__":
    execute_and_build()
