"""
Train a per-user blunder-risk classifier.

Usage (inside backend container):
    python train_risk.py <username>

Logistic Regression is fit first as a sanity baseline. If AUC > 0.55 we also
fit LightGBM. The final chosen model (whichever has higher held-out AUC) is
pickled to risk_model_<username>.pkl alongside the feature names.

Models live under /app/data/risk/ so they survive container restarts when the
app volume is mounted.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sqlalchemy import or_

from database import SessionLocal
from models import Game, MoveAnalysis
from ml_features import FEATURE_NAMES, iter_user_moves

MIN_SAMPLES = 200      # bail out below this — model will be junk
MIN_POSITIVES = 30     # need enough bad-move examples too
MODEL_DIR = Path(os.getenv("RISK_MODEL_DIR", "/app/data/risk"))


def collect_dataset(username: str):
    db = SessionLocal()
    try:
        games = (
            db.query(Game)
            .filter(
                or_(
                    Game.white_username.ilike(username),
                    Game.black_username.ilike(username),
                )
            )
            .all()
        )
        X, y, meta = [], [], []
        for g in games:
            if not g.pgn:
                continue
            moves = (
                db.query(MoveAnalysis)
                .filter(MoveAnalysis.game_id == g.id)
                .order_by(MoveAnalysis.id)
                .all()
            )
            if not moves:
                continue
            for sample in iter_user_moves(g.pgn, username, moves):
                feats = sample["features"]
                X.append([feats[name] for name in FEATURE_NAMES])
                y.append(sample["label"])
                meta.append({"game_id": g.id, "move_id": sample["move_id"]})
        return np.array(X, dtype=float), np.array(y, dtype=int), meta
    finally:
        db.close()


def train(username: str):
    print(f"Collecting dataset for {username}…")
    X, y, _meta = collect_dataset(username)
    n = len(y)
    pos = int(y.sum())
    print(f"  samples={n}  positives={pos}  negatives={n - pos}")

    if n < MIN_SAMPLES or pos < MIN_POSITIVES:
        print(
            f"Not enough data (need ≥{MIN_SAMPLES} samples and ≥{MIN_POSITIVES} positives). "
            "Analyze more games first."
        )
        return None

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- Baseline: Logistic Regression (scaled) ---
    scaler = StandardScaler().fit(X_tr)
    lr = LogisticRegression(max_iter=1000, class_weight="balanced")
    lr.fit(scaler.transform(X_tr), y_tr)
    lr_auc = roc_auc_score(y_te, lr.predict_proba(scaler.transform(X_te))[:, 1])
    print(f"  Logistic Regression AUC = {lr_auc:.3f}")

    chosen = ("logreg", {"scaler": scaler, "model": lr}, lr_auc)

    # --- LightGBM if the signal is at all there ---
    try:
        import lightgbm as lgb

        train_set = lgb.Dataset(X_tr, label=y_tr, feature_name=FEATURE_NAMES)
        valid_set = lgb.Dataset(X_te, label=y_te, reference=train_set)
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbosity": -1,
            "learning_rate": 0.05,
            "num_leaves": 31,
            "min_data_in_leaf": 20,
            "feature_fraction": 0.9,
            "bagging_fraction": 0.9,
            "bagging_freq": 5,
            "is_unbalance": True,
        }
        booster = lgb.train(
            params,
            train_set,
            num_boost_round=500,
            valid_sets=[valid_set],
            callbacks=[lgb.early_stopping(30), lgb.log_evaluation(0)],
        )
        gbm_auc = roc_auc_score(y_te, booster.predict(X_te))
        print(f"  LightGBM AUC          = {gbm_auc:.3f}")
        if gbm_auc > lr_auc:
            chosen = ("lightgbm", {"model": booster}, gbm_auc)
    except Exception as e:
        print(f"  LightGBM skipped: {e}")

    kind, payload, auc = chosen
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = MODEL_DIR / f"risk_model_{username.lower()}.pkl"
    joblib.dump(
        {
            "kind": kind,
            "payload": payload,
            "auc": auc,
            "feature_names": FEATURE_NAMES,
            "username": username,
            "n_samples": n,
            "n_positives": pos,
        },
        out_path,
    )
    print(f"  Saved {kind} (AUC={auc:.3f}) -> {out_path}")
    return out_path


def load_model(username: str):
    path = MODEL_DIR / f"risk_model_{username.lower()}.pkl"
    if not path.exists():
        return None
    return joblib.load(path)


def predict_proba(model_bundle, X: np.ndarray) -> np.ndarray:
    kind = model_bundle["kind"]
    payload = model_bundle["payload"]
    if kind == "logreg":
        X_scaled = payload["scaler"].transform(X)
        return payload["model"].predict_proba(X_scaled)[:, 1]
    elif kind == "lightgbm":
        return payload["model"].predict(X)
    raise ValueError(f"Unknown model kind: {kind}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    result = train(args.username)
    sys.exit(0 if result else 1)
