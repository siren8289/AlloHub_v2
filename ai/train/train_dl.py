"""DL 학습: PyTorch MLP로 '위험 회사일 확률'을 예측하는 모델을 만든다.

실행 (저장소 루트에서)
    python -m ai.train.train_dl
"""
import json

import joblib
import numpy as np
import torch
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from torch import nn

from ai.src.dl_model import RiskMLP
from ai.src.features import CATEGORY_COLUMNS, FEATURE_COLUMNS, NUMBER_COLUMNS, TARGET_COLUMN
from ai.train.common import MODELS_DIR, copy_companies_for_server, load_companies

EPOCHS = 40
BATCH_SIZE = 64
LEARNING_RATE = 0.001


def main():
    torch.manual_seed(42)
    df = load_companies()
    x_all = df[FEATURE_COLUMNS]
    y_all = df[TARGET_COLUMN].astype(int)

    x_train_df, x_test_df, y_train, y_test = train_test_split(
        x_all, y_all, test_size=0.2, random_state=42, stratify=y_all,
    )

    # 신경망은 숫자 크기에 민감하다 → 숫자 컬럼은 표준화(평균 0, 표준편차 1)
    preprocessor = ColumnTransformer([
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORY_COLUMNS),
        ("number", StandardScaler(), NUMBER_COLUMNS),
    ])
    x_train = preprocessor.fit_transform(x_train_df).astype(np.float32)
    x_test = preprocessor.transform(x_test_df).astype(np.float32)
    y_train_np = y_train.to_numpy().astype(np.float32)
    y_test_np = y_test.to_numpy().astype(np.float32)

    x_tensor = torch.from_numpy(x_train)
    y_tensor = torch.from_numpy(y_train_np).unsqueeze(1)

    model = RiskMLP(input_size=x_train.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)

    # 위험 회사가 적으면, 그 쪽을 놓쳤을 때 벌점을 더 크게 준다.
    positive = max(float(y_train_np.sum()), 1.0)
    negative = float(len(y_train_np) - y_train_np.sum())
    loss_fn = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([negative / positive]))

    for epoch in range(1, EPOCHS + 1):
        model.train()
        order = torch.randperm(len(x_tensor))
        total_loss = 0.0
        for start in range(0, len(order), BATCH_SIZE):
            index = order[start:start + BATCH_SIZE]
            optimizer.zero_grad()
            loss = loss_fn(model(x_tensor[index]), y_tensor[index])
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(index)
        if epoch % 10 == 0:
            print(f"epoch {epoch:2d} / loss {total_loss / len(order):.4f}")

    model.eval()
    with torch.no_grad():
        probability = torch.sigmoid(model(torch.from_numpy(x_test)).squeeze(1)).numpy()
    predicted = (probability >= 0.5).astype(int)
    metrics = {
        "rows": int(len(df)),
        "distress_rows": int(y_all.sum()),
        "accuracy": round(float(accuracy_score(y_test_np, predicted)), 4),
        "f1": round(float(f1_score(y_test_np, predicted, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_test_np, probability)), 4),
    }
    print("DL 평가:", metrics)

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(preprocessor, MODELS_DIR / "risk_mlp_preprocessor.joblib")
    torch.save(
        {"input_size": int(x_train.shape[1]), "model_state_dict": model.state_dict()},
        MODELS_DIR / "risk_mlp.pt",
    )
    (MODELS_DIR / "metrics_dl.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    copy_companies_for_server()
    print("저장 완료:", MODELS_DIR / "risk_mlp.pt")


if __name__ == "__main__":
    main()
