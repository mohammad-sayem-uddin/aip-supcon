"""Baselines 1-4 on the same folds as the deep model, then Regime A/B/C independent evaluation.

  AAC_SVM          AAC + length, RBF SVM, C/gamma by inner 3-fold CV on the training fold
  AAC_RF           AAC + length, Random Forest (500 trees)
  AAC_DPC_CTD_LGBM AAC+DPC+CTD+length, LightGBM, early stopping on an inner 10% of the training fold
  <ckpt>_LR        frozen ESM-2 embedding + logistic regression (C by inner CV)
"""
from __future__ import annotations

import argparse
import time
import warnings

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from src.embed import get_embeddings
from src.evaluate import METRIC_NAMES
from src.features import combine
from src.train import (PROC, RESULT_COLUMNS, RESULTS, Config, _result_row, append_results, make_folds)
from src.utils import Timer, mark_stage, setup_logging

log = setup_logging("baselines")

SEEDS = (0, 1, 2, 3, 4)
TEST_SETS = ("ind_425", "ind_1049")
REGIMES = ("A", "B", "C")
HANDCRAFTED = {"AAC_SVM": ("aac", "len"), "AAC_RF": ("aac", "len"), "AAC_DPC_CTD_LGBM": ("aac", "dpc", "ctd", "len")}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def features_for(model: str, seqs: list[str]) -> np.ndarray:
    if model in HANDCRAFTED:
        return combine(seqs, HANDCRAFTED[model])
    return get_embeddings(model.removesuffix("_LR"), seqs).astype(np.float32)


def fit_predict(model: str, Xtr: np.ndarray, ytr: np.ndarray, Xtests: list[np.ndarray], seed: int) -> list[np.ndarray]:
    """Fit on the training data only (scaler included) and return P(AIP) for each array in Xtests."""
    sc = StandardScaler().fit(Xtr)
    Xs = sc.transform(Xtr)
    tests = [sc.transform(x) for x in Xtests]
    if model == "AAC_SVM":
        inner = StratifiedKFold(3, shuffle=True, random_state=seed)
        gs = GridSearchCV(SVC(kernel="rbf", class_weight="balanced"),
                          {"C": [1, 10, 100], "gamma": [0.003, 0.01, 0.03, 0.1]}, scoring="roc_auc", cv=inner, n_jobs=1)
        gs.fit(Xs, ytr)
        return [_sigmoid(gs.best_estimator_.decision_function(t)) for t in tests]
    if model == "AAC_RF":
        rf = RandomForestClassifier(500, random_state=seed, n_jobs=1, class_weight="balanced").fit(Xs, ytr)
        return [rf.predict_proba(t)[:, 1] for t in tests]
    if model == "AAC_DPC_CTD_LGBM":
        import lightgbm as lgb
        a, b = train_test_split(np.arange(len(ytr)), test_size=0.1, stratify=ytr, random_state=seed)
        clf = lgb.LGBMClassifier(n_estimators=2000, learning_rate=0.05, num_leaves=15, subsample=0.8, subsample_freq=1,
                                 colsample_bytree=0.5, is_unbalance=True, random_state=seed, n_jobs=1, verbose=-1)
        clf.fit(Xs[a], ytr[a], eval_set=[(Xs[b], ytr[b])], eval_metric="auc",
                callbacks=[lgb.early_stopping(50, verbose=False)])
        return [clf.predict_proba(t)[:, 1] for t in tests]
    if model.endswith("_LR"):
        lr = LogisticRegressionCV(Cs=[0.0003, 0.001, 0.003, 0.01, 0.03, 0.1, 1.0], cv=3, scoring="roc_auc",
                                  max_iter=3000, class_weight="balanced", random_state=seed, n_jobs=1).fit(Xs, ytr)
        return [lr.predict_proba(t)[:, 1] for t in tests]
    raise ValueError(model)


def _cfg(model: str) -> Config:
    ckpt = model.removesuffix("_LR") if model.endswith("_LR") else "none"
    return Config(name=model, checkpoint=ckpt, lambda_supcon=float("nan"), temperature=float("nan"))


def _finish(row: dict, model: str) -> dict:
    row["config_key"] = model
    row["config"] = "{}"
    return row


def _cv_unit(model: str, seed: int, fold: int, seqs: list[str], y: np.ndarray) -> dict:
    tr, va = make_folds(y, seed)[fold]
    X = features_for(model, seqs)
    t0 = time.time()
    prob = fit_predict(model, X[tr], y[tr], [X[va]], seed)[0]
    secs = time.time() - t0
    row = _result_row(_cfg(model), model, "baseline", "cv", "cv", seed, fold, 0, 0, secs, 0.5, y[va], prob)
    return _finish(row, model)


def _final_unit(model: str, seed: int, seqs: list[str], y: np.ndarray) -> list[tuple]:
    """Train on all benchmark_clean with this seed; predict every (test set, regime)."""
    X = features_for(model, seqs)
    tests = []
    keys = []
    for ts in TEST_SETS:
        for rg in REGIMES:
            df = pd.read_csv(PROC / f"{ts}_regime_{rg.lower()}.csv")
            tests.append(features_for(model, df["sequence"].tolist()))
            keys.append((ts, rg, df))
    t0 = time.time()
    probs = fit_predict(model, X, y, tests, seed)
    secs = time.time() - t0
    return [(ts, rg, df, p, secs) for (ts, rg, df), p in zip(keys, probs)]


def save_predictions(model: str, ts: str, rg: str, df: pd.DataFrame, probs: np.ndarray) -> None:
    out = pd.DataFrame({"sequence": df["sequence"], "y_true": df["label"], "y_prob": probs,
                        "y_pred": (probs >= 0.5).astype(int)})
    d = RESULTS / "predictions"
    d.mkdir(parents=True, exist_ok=True)
    out.to_csv(d / f"{model}_{ts}_{rg}.csv", index=False)


def run_model(model: str, seeds=SEEDS, n_jobs: int = 4) -> None:
    t = Timer()
    bench = pd.read_csv(PROC / "benchmark_clean.csv")
    seqs, y = bench["sequence"].tolist(), bench["label"].to_numpy()
    log.info("baseline %s: CV (%d seeds x 5 folds)", model, len(seeds))
    rows = Parallel(n_jobs=n_jobs)(delayed(_cv_unit)(model, s, f, seqs, y) for s in seeds for f in range(5))
    cv = pd.DataFrame(rows)[RESULT_COLUMNS]
    log.info("baseline %s CV: MCC %.4f AUROC %.4f", model, cv["mcc"].mean(), cv["auroc"].mean())

    log.info("baseline %s: final models for independent sets", model)
    finals = Parallel(n_jobs=n_jobs)(delayed(_final_unit)(model, s, seqs, y) for s in seeds)
    fin_rows = []
    ens: dict[tuple, list] = {}
    for s, res in zip(seeds, finals):
        for ts, rg, df, p, secs in res:
            row = _result_row(_cfg(model), model, "baseline", ts, rg, s, -1, 0, 0, secs, 0.5, df["label"].to_numpy(), p)
            fin_rows.append(_finish(row, model))
            ens.setdefault((ts, rg), [df, []])[1].append(p)
    for (ts, rg), (df, ps) in ens.items():
        save_predictions(model, ts, rg, df, np.mean(ps, axis=0))
    fin = pd.DataFrame(fin_rows)[RESULT_COLUMNS]
    # one file per run keeps the append-only rule simple; consumers concatenate cv + independent rows
    prev = RESULTS / "baseline_results.csv"
    if prev.exists():
        old = pd.read_csv(prev, usecols=["model"])
        if model in set(old["model"]):
            log.warning("%s already in baseline_results.csv; not appending duplicates", model)
            return
    append_results(pd.concat([cv, fin]), prev)
    log.info("baseline %s done in %.1fs", model, t.elapsed())


def available_esm() -> list[str]:
    from src.embed import EMB_DIR, CHECKPOINTS
    return [c for c in CHECKPOINTS if (EMB_DIR / f"{c}_all.npy").exists()]


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--models", nargs="+")
    ap.add_argument("--n-jobs", type=int, default=4)
    a = ap.parse_args()
    t = Timer()
    models = a.models or (list(HANDCRAFTED) + [c + "_LR" for c in available_esm()])
    failed = []
    for m in models:
        try:
            run_model(m, n_jobs=a.n_jobs)
        except Exception:
            failed.append(m)
            import traceback
            from src.utils import append_note
            append_note("BLOCKERS.md", f"S6 baseline {m} failed", "```\n" + traceback.format_exc() + "\n```")
            log.exception("baseline %s failed", m)
    mark_stage("S6", "partial" if failed else "complete", t.elapsed(),
               "models: " + ", ".join(models) + (f"; FAILED: {failed}" if failed else ""))
