"""ML 학습: 랜덤포레스트로 '위험 회사일 확률'을 예측하는 모델을 만든다.

실행 (저장소 루트에서, data 파이프라인을 먼저 돌려야 한다)
    python -m ai.train.train_ml
"""
import json

import joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from ai.src.scoring.features import CATEGORY_COLUMNS, FEATURE_COLUMNS, NUMBER_COLUMNS, TARGET_COLUMN
from ai.train.common import MODELS_DIR, copy_companies_for_server, load_companies


def build_pipeline():
    # 글자 컬럼은 원-핫 인코딩, 숫자 컬럼은 그대로 통과
    preprocessor = ColumnTransformer([
        ("category", OneHotEncoder(handle_unknown="ignore"), CATEGORY_COLUMNS),
        ("number", "passthrough", NUMBER_COLUMNS),
    ])
    # 위험 회사가 적으므로 class_weight='balanced' 로 적게 나온 쪽을 더 중요하게 본다.
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
    )
    return Pipeline([("preprocess", preprocessor), ("model", model)])


def main():
    df = load_companies()
    x = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.2, random_state=42, stratify=y,
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    probability = pipeline.predict_proba(x_test)[:, 1]
    predicted = (probability >= 0.5).astype(int)
    metrics = {
        "rows": int(len(df)),
        "distress_rows": int(y.sum()),
        "accuracy": round(float(accuracy_score(y_test, predicted)), 4),
        "f1": round(float(f1_score(y_test, predicted, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test, probability)), 4),
    }
    print("ML 평가:", metrics)

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(pipeline, MODELS_DIR / "risk_rf.joblib", compress=3)
    (MODELS_DIR / "metrics_ml.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    copy_companies_for_server()
    print("저장 완료:", MODELS_DIR / "risk_rf.joblib")


if __name__ == "__main__":
    main()
