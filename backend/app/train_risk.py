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
from sklearn.calibration import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import GroupKFold, train_test_split
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


def _cv_auc(X, y, groups, model_fn, n_splits=5):
    """Game-level K-fold CV. `model_fn() -> (fit(X,y), predict_proba(X))` factory.

    Returns (mean_auc, std_auc, per_fold_aucs). Splits never put two moves
    from the same game in different folds, so AUC reflects generalization to
    *new games*, not just new moves in seen games.
    """
    kf = GroupKFold(n_splits=n_splits)
    aucs = []
    for tr, te in kf.split(X, y, groups=groups):
        fit, proba = model_fn()
        fit(X[tr], y[tr])
        aucs.append(roc_auc_score(y[te], proba(X[te])))
    aucs = np.array(aucs)
    return aucs.mean(), aucs.std(), aucs


def train(username: str):
    print(f"Collecting dataset for {username}…")
    X, y, meta = collect_dataset(username)
    n = len(y)
    pos = int(y.sum())
    print(f"  samples={n}  positives={pos}  negatives={n - pos}")

    if n < MIN_SAMPLES or pos < MIN_POSITIVES:
        print(
            f"Not enough data (need ≥{MIN_SAMPLES} samples and ≥{MIN_POSITIVES} positives). "
            "Analyze more games first."
        )
        return None

    groups = np.array([m["game_id"] for m in meta])
    n_games = len(set(groups))
    print(f"  games={n_games}")

    # --- Honest game-level CV (does not leak ply from same game) ---
    def make_lr():
        def fit_fn(Xt, yt):
            sc = StandardScaler().fit(Xt)
            m = LogisticRegression(max_iter=1000, class_weight="balanced")
            m.fit(sc.transform(Xt), yt)
            fit_fn.sc = sc
            fit_fn.m = m
        def pred_fn(Xv):
            return fit_fn.m.predict_proba(fit_fn.sc.transform(Xv))[:, 1]
        return fit_fn, pred_fn

    cv_mean, cv_std, cv_folds = _cv_auc(X, y, groups, make_lr, n_splits=5)
    print(f"  LR 5-fold game-level CV AUC = {cv_mean:.3f} ± {cv_std:.3f}  (folds: {[f'{a:.3f}' for a in cv_folds]})")

    # Same for LightGBM if available
    try:
        import lightgbm as lgb

        def make_lgbm():
            def fit_fn(Xt, yt):
                params = {
                    "objective": "binary", "metric": "auc", "verbosity": -1,
                    "learning_rate": 0.05, "num_leaves": 31,
                    "min_data_in_leaf": 20, "feature_fraction": 0.9,
                    "bagging_fraction": 0.9, "bagging_freq": 5,
                    "is_unbalance": True,
                }
                ds = lgb.Dataset(Xt, label=yt, feature_name=FEATURE_NAMES)
                fit_fn.b = lgb.train(params, ds, num_boost_round=100)
            def pred_fn(Xv):
                return fit_fn.b.predict(Xv)
            return fit_fn, pred_fn

        gbm_mean, gbm_std, gbm_folds = _cv_auc(X, y, groups, make_lgbm, n_splits=5)
        print(f"  LightGBM 5-fold game-level CV AUC = {gbm_mean:.3f} ± {gbm_std:.3f}  (folds: {[f'{a:.3f}' for a in gbm_folds]})")
    except Exception as e:
        print(f"  LightGBM CV skipped: {e}")

    # --- Final model: train on a single random 80/20 split for the saved pkl ---
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # --- Baseline: Logistic Regression (scaled) ---
    scaler = StandardScaler().fit(X_tr)
    lr = LogisticRegression(max_iter=1000, class_weight="balanced")
    lr.fit(scaler.transform(X_tr), y_tr)
    lr_auc = roc_auc_score(y_te, lr.predict_proba(scaler.transform(X_te))[:, 1])
    print(f"  Logistic Regression AUC = {lr_auc:.3f}")

    # Top LR coefficients by absolute weight (scaled features so magnitudes compare).
    coefs = sorted(zip(FEATURE_NAMES, lr.coef_[0]), key=lambda kv: abs(kv[1]), reverse=True)
    print("  LR feature importance (top 8):")
    for name, w in coefs[:8]:
        print(f"    {name:>22}  {w:+.3f}")

    chosen = ("logreg", {"scaler": scaler, "model": lr}, lr_auc, cv_mean)

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
        gains = sorted(zip(FEATURE_NAMES, booster.feature_importance(importance_type="gain")),
                       key=lambda kv: kv[1], reverse=True)
        print("  LightGBM feature importance (top 8 by gain):")
        for name, g in gains[:8]:
            print(f"    {name:>22}  {g:.1f}")

        # Probability calibration: raw LightGBM scores can be over/under-
        # confident. Fit an isotonic mapping on the held-out fold so the
        # final predict_proba is calibrated (Brier score reported below).
        raw_proba = booster.predict(X_te)
        iso = IsotonicRegression(out_of_bounds="clip").fit(raw_proba, y_te)
        cal_proba = iso.predict(raw_proba)
        raw_brier = brier_score_loss(y_te, raw_proba)
        cal_brier = brier_score_loss(y_te, cal_proba)
        print(f"  Brier (raw → calibrated) = {raw_brier:.4f} → {cal_brier:.4f}")

        if gbm_auc > lr_auc:
            chosen = ("lightgbm", {"model": booster, "calibrator": iso}, gbm_auc, gbm_mean)
    except Exception as e:
        print(f"  LightGBM skipped: {e}")

    kind, payload, auc, cv_auc = chosen
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    out_path = MODEL_DIR / f"risk_model_{username.lower()}.pkl"
    joblib.dump(
        {
            "kind": kind,
            "payload": payload,
            "auc": cv_auc,          # game-level CV AUC — honest generalization estimate
            "auc_test": auc,        # random split test AUC (kept for reference)
            "feature_names": FEATURE_NAMES,
            "username": username,
            "n_samples": n,
            "n_positives": pos,
        },
        out_path,
    )
    print(f"  Saved {kind} (CV AUC={cv_auc:.3f}, test AUC={auc:.3f}) -> {out_path}")
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
        raw = payload["model"].predict(X)
        cal = payload.get("calibrator")
        return cal.predict(raw) if cal is not None else raw
    raise ValueError(f"Unknown model kind: {kind}")


def explain_predictions(model_bundle, X: np.ndarray, top_k: int = 3):
    """Return per-row top-k SHAP contributions.

    For LightGBM we use the built-in `pred_contrib=True` (exact tree SHAP, no
    extra dep call at predict time). For LR we approximate with
    (coef × scaled_feature). Returns a list of [(feature_name, signed_contrib),...]
    per input row, sorted by |contrib| descending, capped at top_k.
    """
    kind = model_bundle["kind"]
    payload = model_bundle["payload"]
    names = FEATURE_NAMES

    if kind == "lightgbm":
        contribs = payload["model"].predict(X, pred_contrib=True)
        # last column is the bias; drop it.
        contribs = contribs[:, :-1]
    elif kind == "logreg":
        scaler = payload["scaler"]
        coef = payload["model"].coef_[0]
        contribs = scaler.transform(X) * coef[np.newaxis, :]
    else:
        raise ValueError(f"Unknown model kind: {kind}")

    out = []
    for row in contribs:
        order = np.argsort(-np.abs(row))[:top_k]
        out.append([(names[i], float(row[i])) for i in order])
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    args = parser.parse_args()
    result = train(args.username)
    sys.exit(0 if result else 1)
