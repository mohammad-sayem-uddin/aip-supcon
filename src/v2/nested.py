"""E5: nested cross-validation for the headline 8M comparison (lambda=0 vs CV-selected lambda).

Outer: make_folds(y, seed) 5 folds for seeds 0-4. Inner: 3-fold StratifiedKFold on the outer-training part selects
lambda > 0 from the pre-specified grid by mean inner-validation MCC. Both the lambda=0 model and the selected-lambda
model are then trained on the outer-training part (early stopping on a 10% hold-out of it) and scored on the outer fold,
which never touched selection or early stopping.
"""
from __future__ import annotations

import multiprocessing as mp
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import StratifiedKFold, train_test_split

from src.evaluate import compute_metrics
from src.train import Config, _fit_scaler, _predict, load_benchmark, make_folds, train_fold
from src.utils import Timer, setup_logging
from src.v2.common import V2, mark

log = setup_logging("nested")
LAMS = [0.1, 0.25, 0.5, 1.0, 2.0]
SEEDS = (0, 1, 2, 3, 4)
CKPT = "esm2_t6_8M"


def _fit_eval(Xtr, ytr, Xte, yte, lam, seed, tau=0.07):
    """Train with early stopping on a 10% hold-out of (Xtr, ytr); return (probs on Xte, metrics)."""
    a, b = train_test_split(np.arange(len(ytr)), test_size=0.1, stratify=ytr, random_state=seed)
    sc = _fit_scaler(Xtr[a])
    cfg = Config(name="n", checkpoint=CKPT, lambda_supcon=lam, temperature=tau)
    model, _ = train_fold(sc.transform(Xtr[a]), ytr[a], sc.transform(Xtr[b]), ytr[b], cfg, seed=seed)
    p = _predict(model, torch.as_tensor(sc.transform(Xte), dtype=torch.float32))
    return p, compute_metrics(yte, (p >= 0.5).astype(int), p)


def outer_unit(task):
    torch.set_num_threads(1)
    seed, fold = task
    X, y, _ = load_benchmark(CKPT)
    tr, te = make_folds(y, seed)[fold]
    inner = StratifiedKFold(3, shuffle=True, random_state=seed)
    inner_scores = {}
    for lam in [0.0] + LAMS:
        ms = []
        for itr, iva in inner.split(np.zeros(len(tr)), y[tr]):
            _, m = _fit_eval(X[tr][itr], y[tr][itr], X[tr][iva], y[tr][iva], lam, 1000 * seed + fold)
            ms.append(m["mcc"])
        inner_scores[lam] = float(np.mean(ms))
    best = max(LAMS, key=lambda l: (inner_scores[l], -l))
    _, m0 = _fit_eval(X[tr], y[tr], X[te], y[te], 0.0, 1000 * seed + fold)
    _, mb = _fit_eval(X[tr], y[tr], X[te], y[te], best, 1000 * seed + fold)
    return {"seed": seed, "fold": fold, "selected_lambda": best, "inner_mcc_lambda0": inner_scores[0.0],
            "inner_mcc_selected": inner_scores[best], "outer_mcc_lambda0": m0["mcc"], "outer_mcc_selected": mb["mcc"],
            "outer_auroc_lambda0": m0["auroc"], "outer_auroc_selected": mb["auroc"]}


def run(n_jobs: int = 6, budget: float | None = None) -> pd.DataFrame | None:
    """Resumable and foreground-sliced: each finished outer fold is appended to nested_cv_8M_partial.csv."""
    import os
    from datetime import datetime
    from src.v2.phaseB import rolling
    t = Timer()
    out, part = V2 / "nested_cv_8M.csv", V2 / "nested_cv_8M_partial.csv"
    if out.exists():
        return pd.read_csv(out)
    done = set()
    if part.exists():
        d = pd.read_csv(part)
        done = {(int(s), int(f)) for s, f in zip(d["seed"], d["fold"])}
    tasks = [(s, f) for s in SEEDS for f in range(5) if (s, f) not in done]
    log_path = V2.parent / "phase_e_progress.log"

    def on_result(r):
        pd.DataFrame([r]).to_csv(part, mode="a", header=not part.exists(), index=False)
        with open(log_path, "a") as fh:
            fh.write(f"{datetime.now().isoformat(timespec='seconds')}, nested seed={r['seed']} fold={r['fold']} lambda*={r['selected_lambda']:g} "
                     f"outer MCC lam0={r['outer_mcc_lambda0']:.4f} selected={r['outer_mcc_selected']:.4f}\n")
            fh.flush()
            os.fsync(fh.fileno())

    left = rolling(tasks, outer_unit, on_result, n_jobs, budget)
    if left:
        return None
    df = pd.read_csv(part).sort_values(["seed", "fold"])
    df.to_csv(out, index=False)
    mark("E5_nested", "complete", t.elapsed(), f"{len(df)} outer folds")
    return df


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    d = run(a.jobs, a.budget)
    if d is None:
        print("slice ended; rerun to continue")
    else:
        diff = d["outer_mcc_selected"] - d["outer_mcc_lambda0"]
        print(d[["outer_mcc_lambda0", "outer_mcc_selected"]].mean().round(4).to_dict(), "diff", round(diff.mean(), 4), "sd", round(diff.std(), 4))
        print(d["selected_lambda"].value_counts().to_dict())
