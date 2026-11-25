"""Phase C: C1 pooling ablation (frozen ESM-2 650M) and C2 feature fusion (ESM-2 || AAC || DPC || CTD).

Every model uses make_folds, seeds 0-4, and is evaluated under Regimes A, B, C on both independent sets.
Usage: python -m src.v2.phaseC c1|c2|all   (results appended to results/v2/repr_results_v2.csv; resumable)
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache

import numpy as np
import pandas as pd

from src.evaluate import METRIC_NAMES, compute_metrics
from src.features import combine
from src.train import PROC, Config, _fit_scaler, _predict, make_folds, train_fold
from src.utils import ProgressLogger, Timer, setup_logging
from src.v2.common import R, V2, block, decide, mark
from src.v2.embed_res import load_residue_cache

warnings.filterwarnings("ignore")
log = setup_logging("phaseC")
SEEDS = (0, 1, 2, 3, 4)
TESTS = [(ts, rg) for ts in ("ind_425", "ind_1049") for rg in ("A", "B", "C")]
FEAT = V2 / "features"
OUT = V2 / "repr_results_v2.csv"
COLS = (["model", "phase", "features", "classifier", "eval_set", "regime", "seed", "fold", "epoch_stopped", "train_seconds",
         "analysis_tier"] + METRIC_NAMES + ["n_eval"])
N_JOBS = 6


# ----------------------------------------------------------- feature sets


def pooled_all(ckpt: str) -> tuple[list[str], dict[str, np.ndarray]]:
    idx, res, cls = load_residue_cache(ckpt)
    seqs, off, ln = idx["sequences"], idx["offsets"], idx["lengths"]
    names = ["mean", "max", "meanmax", "cls", "firstlast"]
    out = {k: [] for k in names}
    for o, L in zip(off, ln):
        r = np.asarray(res[o : o + L], dtype=np.float32)
        mean, mx = r.mean(0), r.max(0)
        out["mean"].append(mean)
        out["max"].append(mx)
        out["meanmax"].append(np.concatenate([mean, mx]))
        out["firstlast"].append(np.concatenate([r[:3].ravel(), r[-3:].ravel()]))
    out["cls"] = list(cls)
    return seqs, {k: np.stack(v).astype(np.float32) for k, v in out.items()}


def _sets() -> dict:
    b = pd.read_csv(PROC / "benchmark_clean.csv")
    d = {"bench": (b["sequence"].tolist(), b["label"].to_numpy())}
    for ts, rg in TESTS:
        t = pd.read_csv(PROC / f"{ts}_regime_{rg.lower()}.csv")
        d[(ts, rg)] = (t["sequence"].tolist(), t["label"].to_numpy())
    return d


def materialise(name: str, builder) -> None:
    """Write feature arrays for benchmark + every (test set, regime) to results/v2/features/{name}/ (npy)."""
    d = FEAT / name
    if (d / "done").exists():
        return
    d.mkdir(parents=True, exist_ok=True)
    for key, (seqs, y) in _sets().items():
        tag = "bench" if key == "bench" else f"{key[0]}_{key[1]}"
        np.save(d / f"{tag}_X.npy", builder(seqs).astype(np.float32))
        np.save(d / f"{tag}_y.npy", y)
    (d / "done").write_text("ok")


def esm_builder(ckpt: str, pooling: str):
    seqs, feats = pooled_all(ckpt)
    lookup = {s: i for i, s in enumerate(seqs)}
    mat = feats[pooling]
    return lambda ss: mat[[lookup[s] for s in ss]]


def hand_builder():
    return lambda ss: combine(ss, ("aac", "dpc", "ctd", "len"))


def fusion_builder(ckpt: str):
    e, h = esm_builder(ckpt, "mean"), hand_builder()
    return lambda ss: np.hstack([e(ss), h(ss)])


@lru_cache(maxsize=8)
def _load(name: str, tag: str):
    d = FEAT / name
    return np.load(d / f"{tag}_X.npy"), np.load(d / f"{tag}_y.npy")


# ------------------------------------------------------------- classifiers


def fit_predict(clf: str, Xtr, ytr, Xtests: list[np.ndarray], seed: int):
    """Returns (list of P(AIP) per test array, epoch_stopped)."""
    sc = _fit_scaler(Xtr)
    Xs, tests = sc.transform(Xtr), [sc.transform(x) for x in Xtests]
    if clf == "rf":
        from sklearn.ensemble import RandomForestClassifier
        m = RandomForestClassifier(500, random_state=seed, n_jobs=1, class_weight="balanced").fit(Xs, ytr)
        return [m.predict_proba(t)[:, 1] for t in tests], 0
    if clf == "lgbm":
        import lightgbm as lgb
        from sklearn.model_selection import train_test_split
        a, b = train_test_split(np.arange(len(ytr)), test_size=0.1, stratify=ytr, random_state=seed)
        m = lgb.LGBMClassifier(n_estimators=2000, learning_rate=0.05, num_leaves=15, subsample=0.8, subsample_freq=1,
                               colsample_bytree=0.5, is_unbalance=True, random_state=seed, n_jobs=1, verbose=-1)
        m.fit(Xs[a], ytr[a], eval_set=[(Xs[b], ytr[b])], eval_metric="auc", callbacks=[lgb.early_stopping(50, verbose=False)])
        return [m.predict_proba(t)[:, 1] for t in tests], int(m.best_iteration_ or 0)
    if clf == "mlp":
        import torch
        from sklearn.model_selection import train_test_split
        a, b = train_test_split(np.arange(len(ytr)), test_size=0.1, stratify=ytr, random_state=seed)
        cfg = Config(name="c", checkpoint="feat", lambda_supcon=0.0)
        model, hist = train_fold(Xs[a], ytr[a], Xs[b], ytr[b], cfg, seed=seed)
        return [_predict(model, torch.as_tensor(t, dtype=torch.float32)) for t in tests], hist[0]["best_epoch"]
    raise ValueError(clf)


def _row(model, phase, feats, clf, eval_set, regime, seed, fold, ep, secs, y, p, tier="exploratory"):
    r = {"model": model, "phase": phase, "features": feats, "classifier": clf, "eval_set": eval_set, "regime": regime,
         "seed": seed, "fold": fold, "epoch_stopped": ep, "train_seconds": round(secs, 2), "analysis_tier": tier}
    r.update(compute_metrics(y, (p >= 0.5).astype(int), p))
    r["n_eval"] = len(y)
    return r


def cv_task(task):
    import torch
    torch.set_num_threads(1)
    feats, clf, phase, seed, fold = task
    X, y = _load(feats, "bench")
    tr, va = make_folds(y, seed)[fold]
    t0 = time.time()
    # the MLP path early-stops on an inner 10% of the training fold, so the validation fold is never used for stopping
    (p,), ep = fit_predict(clf, X[tr], y[tr], [X[va]], 1000 * seed + fold)
    return _row(f"{feats}|{clf}", phase, feats, clf, "cv", "cv", seed, fold, ep, time.time() - t0, y[va], p)


def final_task(task):
    import torch
    torch.set_num_threads(1)
    feats, clf, phase, seed = task
    X, y = _load(feats, "bench")
    tests = [_load(feats, f"{ts}_{rg}")[0] for ts, rg in TESTS]
    t0 = time.time()
    ps, ep = fit_predict(clf, X, y, tests, seed)
    return {"feats": feats, "clf": clf, "phase": phase, "seed": seed, "ep": ep, "secs": time.time() - t0, "probs": ps}


def run_models(models: list[tuple[str, str, str]], tag: str) -> None:
    """models: [(features_name, classifier, phase)]. CV (25 runs) + final (5 seeds) per model; resumable."""
    t = Timer()
    done = set()
    if OUT.exists():
        d = pd.read_csv(OUT, usecols=["model", "eval_set", "seed", "fold"])
        done = set(map(tuple, d.to_numpy()))
    cv_tasks = [(f, c, ph, s, k) for f, c, ph in models for s in SEEDS for k in range(5) if (f"{f}|{c}", "cv", s, k) not in done]
    fin_tasks = [(f, c, ph, s) for f, c, ph in models for s in SEEDS if (f"{f}|{c}", "ind_425", s, -1) not in done]
    log.info("%s: %d CV tasks, %d final tasks", tag, len(cv_tasks), len(fin_tasks))
    prog = ProgressLogger(len(cv_tasks) + len(fin_tasks), tag, log)
    finals: dict[tuple, list] = {}
    labels = {(ts, rg): pd.read_csv(PROC / f"{ts}_regime_{rg.lower()}.csv") for ts, rg in TESTS}
    with ProcessPoolExecutor(max_workers=N_JOBS, mp_context=mp.get_context("spawn")) as ex:
        futs = [ex.submit(cv_task, tk) for tk in cv_tasks] + [ex.submit(final_task, tk) for tk in fin_tasks]
        for fu in as_completed(futs):
            r = fu.result()
            if "probs" in r:
                finals.setdefault((r["feats"], r["clf"], r["phase"]), []).append(r)
            else:
                pd.DataFrame([r])[COLS].to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
            prog.step()
    (V2 / "predictions").mkdir(exist_ok=True)
    for (f, c, ph), rs in finals.items():
        rs.sort(key=lambda r: r["seed"])
        rows = []
        for j, (ts, rg) in enumerate(TESTS):
            df = labels[(ts, rg)]
            y = df["label"].to_numpy()
            plist = [r["probs"][j] for r in rs]
            for r, p in zip(rs, plist):
                rows.append(_row(f"{f}|{c}", ph, f, c, ts, rg, r["seed"], -1, r["ep"], r["secs"], y, p))
            pm = np.mean(plist, axis=0)
            d = {"sequence": df["sequence"], "y_true": y, "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)}
            for r, p in zip(rs, plist):
                d[f"prob_seed{r['seed']}"] = p
            pd.DataFrame(d).to_csv(V2 / "predictions" / f"{f}__{c}_{ts}_{rg}.csv", index=False)
        pd.DataFrame(rows)[COLS].to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
    mark(tag, "complete", t.elapsed(), f"{len(models)} models")


# ---------------------------------------------------------------- phases

POOLINGS = ["mean", "max", "meanmax", "cls", "firstlast"]


def c1() -> None:
    for p in POOLINGS:
        materialise(f"esm650_{p}", esm_builder("esm2_t33_650M", p))
    run_models([(f"esm650_{p}", "mlp", "C1") for p in POOLINGS], "C1_pooling")


def c2() -> None:
    materialise("hand", hand_builder())
    for ck, short in (("esm2_t33_650M", "esm650"), ("esm2_t6_8M", "esm8")):
        materialise(f"{short}_mean", esm_builder(ck, "mean"))
        materialise(f"{short}_fusion", fusion_builder(ck))
    models = [("hand", c, "C2") for c in ("rf", "lgbm", "mlp")]
    for short in ("esm650", "esm8"):
        models += [(f"{short}_mean", c, "C2") for c in ("rf", "lgbm", "mlp")]
        models += [(f"{short}_fusion", c, "C2") for c in ("rf", "lgbm", "mlp")]
    run_models(models, "C2_fusion")


if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    if w in ("c1", "all"):
        c1()
    if w in ("c2", "all"):
        c2()
