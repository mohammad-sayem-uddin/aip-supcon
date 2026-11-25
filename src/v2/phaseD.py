"""Phase D: cross-benchmark generalisation over every obtainable AIP dataset.

Training sets: AIPpred benchmark (1258/1887), AntiInflam training (690/1009), local composite Benchmark_clean (3716).
Independent sets: AIPpred independent (= local Ind_1049), AntiInflam validation (= local Ind_425).
For each (train, test) pair, Regime A = test set as distributed, B = exact matches to that training set removed,
C = additionally identity >= 0.9 removed. All results are exploratory (analysis_tier column).
AIPStack independent sets were not obtainable (BLOCKERS_v2.md); D3 (AMP/ACP transfer) was not attempted (see report).
Run: python -m src.v2.phaseD
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import time
import warnings
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd
import torch

from src.data import max_identity_to_train
from src.embed import embed_sequences
from src.evaluate import METRIC_NAMES, compute_metrics
from src.features import combine
from src.train import Config, _fit_scaler, _predict, train_fold
from src.utils import ROOT, Timer, setup_logging
from src.v2.common import R, V2, block, mark
from src.v2.phaseA import load_sources

warnings.filterwarnings("ignore")
log = setup_logging("phaseD")
EXT = ROOT / "embeddings" / "v2"
SEEDS = (0, 1, 2, 3, 4)
OUT = V2 / "cross_benchmark_results_v2.csv"
TRAINS = {"AIPpred_benchmark": "AIPpred_benchmark", "AntiInflam_training": "AntiInflam_training", "local_Benchmark_clean": "local_Benchmark"}
TESTS = {"AIPpred_independent": "AIPpred_independent", "AntiInflam_validation": "AntiInflam_validation"}
MODELS = {  # key -> (features, classifier, lambda, tau)
    "AAC+RF": ("hand_aac", "rf", 0.0, 0.07),
    "AAC+DPC+CTD+LGBM": ("hand_all", "lgbm", 0.0, 0.07),
    "ESM2-8M MLP lam0": ("esm8", "mlp", 0.0, 0.07),
    "ESM2-8M SupCon lam2": ("esm8", "mlp", 2.0, 0.1),
    "ESM2-650M MLP lam0": ("esm650", "mlp", 0.0, 0.07),
    "ESM2-650M SupCon lam1": ("esm650", "mlp", 1.0, 0.05),
    "fusion650 RF": ("fusion650", "rf", 0.0, 0.07),
}
COLS = (["train_set", "test_set", "regime", "model", "seed", "n_train", "n_eval", "analysis_tier"] + METRIC_NAMES)


def clean_train(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("sequence")["label"].nunique()
    d = df[~df["sequence"].isin(set(g[g > 1].index))]
    return d.drop_duplicates("sequence").reset_index(drop=True)


def ext_embeddings(ckpt: str, seqs: list[str]) -> dict[str, np.ndarray]:
    """Pooled embeddings for any sequence: v1 cache when present, otherwise computed once and cached here."""
    from src.embed import load_cached
    c = load_cached(ckpt, "all")
    have = {s: i for i, s in enumerate(c[1])}
    out = {s: c[0][have[s]] for s in seqs if s in have}
    miss = sorted(set(seqs) - set(out))
    if miss:
        EXT.mkdir(parents=True, exist_ok=True)
        f = EXT / f"ext_{ckpt}"
        cached = {}
        if (f.with_suffix(".json")).exists():
            names = json.loads(f.with_suffix(".json").read_text())
            arr = np.load(f.with_suffix(".npy"))
            cached = dict(zip(names, arr))
        todo = [s for s in miss if s not in cached]
        if todo:
            log.info("embedding %d new sequences with %s", len(todo), ckpt)
            from src.utils import get_device
            arr = embed_sequences(todo, ckpt, "cpu", 32)
            cached.update(dict(zip(todo, arr)))
            f.with_suffix(".json").write_text(json.dumps(list(cached)))
            np.save(f.with_suffix(".npy"), np.stack(list(cached.values())))
        out.update({s: cached[s] for s in miss})
    return out


def feats(kind: str, seqs: list[str], store: dict) -> np.ndarray:
    if kind == "hand_aac":
        return combine(seqs, ("aac", "len"))
    if kind == "hand_all":
        return combine(seqs, ("aac", "dpc", "ctd", "len"))
    if kind in ("esm8", "esm650"):
        return np.stack([store[kind][s] for s in seqs]).astype(np.float32)
    if kind == "fusion650":
        return np.hstack([feats("esm650", seqs, store), combine(seqs, ("aac", "dpc", "ctd", "len"))])
    raise ValueError(kind)


def fit_predict(kind: str, clf: str, lam: float, tau: float, Xtr, ytr, Xtests, seed: int):
    from sklearn.model_selection import train_test_split
    sc = _fit_scaler(Xtr)
    Xs, tests = sc.transform(Xtr), [sc.transform(x) for x in Xtests]
    if clf == "rf":
        from sklearn.ensemble import RandomForestClassifier
        m = RandomForestClassifier(500, random_state=seed, n_jobs=1, class_weight="balanced").fit(Xs, ytr)
        return [m.predict_proba(t)[:, 1] for t in tests]
    if clf == "lgbm":
        import lightgbm as lgb
        a, b = train_test_split(np.arange(len(ytr)), test_size=0.1, stratify=ytr, random_state=seed)
        m = lgb.LGBMClassifier(n_estimators=2000, learning_rate=0.05, num_leaves=15, subsample=0.8, subsample_freq=1,
                               colsample_bytree=0.5, is_unbalance=True, random_state=seed, n_jobs=1, verbose=-1)
        m.fit(Xs[a], ytr[a], eval_set=[(Xs[b], ytr[b])], eval_metric="auc", callbacks=[lgb.early_stopping(50, verbose=False)])
        return [m.predict_proba(t)[:, 1] for t in tests]
    a, b = train_test_split(np.arange(len(ytr)), test_size=0.1, stratify=ytr, random_state=seed)
    model, _ = train_fold(Xs[a], ytr[a], Xs[b], ytr[b], Config(name="d", checkpoint="x", lambda_supcon=lam, temperature=tau), seed=seed)
    return [_predict(model, torch.as_tensor(t, dtype=torch.float32)) for t in tests]


CACHE_D = V2 / "cross_cache"
FEAT_D = V2 / "cross_feats"
PROG_D = R / "phase_d_progress.log"


def _prog(line: str) -> None:
    with open(PROG_D, "a") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def task(args):
    """One (train set, model, seed) job: features come from npy files written once by the parent."""
    import pickle
    torch.set_num_threads(1)
    tr_name, mkey, seed, test_names = args
    kind, clf, lam, tau = MODELS[mkey]
    Xtr = np.load(FEAT_D / f"{tr_name}__{kind}__train.npy")
    ytr = np.load(FEAT_D / f"{tr_name}__ytrain.npy")
    Xt = [np.load(FEAT_D / f"{en}__{kind}__test.npy") for en in test_names]
    probs = fit_predict(kind, clf, lam, tau, Xtr, ytr, Xt, seed)
    CACHE_D.mkdir(parents=True, exist_ok=True)
    with open(CACHE_D / f"{tr_name}__{mkey.replace(' ', '_').replace('+', 'p')}__s{seed}.pkl", "wb") as fh:
        pickle.dump(dict(zip(test_names, probs)), fh)
    return tr_name, mkey, seed


def run(budget: float | None = None, n_jobs: int = 6) -> int:
    import pickle
    from datetime import datetime
    from src.v2.phaseB import rolling
    t0 = Timer()
    S = load_sources()
    trains = {n: clean_train(S[k]) for n, k in TRAINS.items()}
    tests = {n: S[k].drop_duplicates("sequence").reset_index(drop=True) for n, k in TESTS.items()}
    models = list(MODELS)
    FEAT_D.mkdir(parents=True, exist_ok=True)
    if not (FEAT_D / "done").exists():
        allseqs = sorted({s for d in list(trains.values()) + list(tests.values()) for s in d["sequence"]})
        store = {"esm8": ext_embeddings("esm2_t6_8M", allseqs)}
        try:
            import shutil
            from pathlib import Path
            hub = Path.home() / ".cache" / "huggingface" / "hub" / "models--facebook--esm2_t33_650M_UR50D"
            pre = hub.exists()
            c650 = V2.parent.parent / "embeddings" / "v2" / "ext_esm2_t33_650M.json"
            if not c650.exists() and shutil.disk_usage(V2).free / 1e9 < 3.6 and not pre:
                raise RuntimeError("less than 3.6 GB free; not downloading the 2.6 GB 650M checkpoint")
            store["esm650"] = ext_embeddings("esm2_t33_650M", allseqs)
            if not pre and hub.exists():
                shutil.rmtree(hub)  # purge the checkpoint this step downloaded
        except Exception as e:
            block("Phase D: 650M embeddings for external sequences failed", f"{type(e).__name__}: {e}. 650M-based models were skipped in Phase D.")
            models = [m for m in models if "650" not in m]
        kinds = sorted({MODELS[m][0] for m in models})
        for kind in kinds:
            for tn, tdf in trains.items():
                np.save(FEAT_D / f"{tn}__{kind}__train.npy", feats(kind, tdf["sequence"].tolist(), store).astype(np.float32))
            for en, edf in tests.items():
                np.save(FEAT_D / f"{en}__{kind}__test.npy", feats(kind, edf["sequence"].tolist(), store).astype(np.float32))
        for tn, tdf in trains.items():
            np.save(FEAT_D / f"{tn}__ytrain.npy", tdf["label"].to_numpy())
        (FEAT_D / "done").write_text(json.dumps(models))
    models = json.loads((FEAT_D / "done").read_text())
    jobs = [(tn, m, s, list(tests)) for tn in trains for m in models for s in SEEDS
            if not (CACHE_D / f"{tn}__{m.replace(' ', '_').replace('+', 'p')}__s{s}.pkl").exists()]
    _prog(f"# {datetime.now().isoformat(timespec='seconds')} Phase D: {len(jobs)} jobs left")
    left = rolling(jobs, task, lambda r: _prog(f"{datetime.now().isoformat(timespec='seconds')}, {r[0]}, {r[1]}, seed={r[2]} cached"), n_jobs, budget)
    _prog(f"# slice end: {left} jobs not started")
    if left:
        return left
    # ---- assemble: regime masks, per-seed metrics, ensemble predictions
    masks = {}
    for tn, tdf in trains.items():
        trs = tdf["sequence"].tolist()
        for en, edf in tests.items():
            mx = max_identity_to_train(edf["sequence"].tolist(), trs, floor=0.8)
            exact = edf["sequence"].isin(set(trs)).to_numpy()
            masks[(tn, en)] = {"A": np.ones(len(edf), bool), "B": ~exact, "C": mx < 0.9 - 1e-12}
    rows, ens = [], {}
    for tn in trains:
        for m in models:
            for s in SEEDS:
                probs = pickle.load(open(CACHE_D / f"{tn}__{m.replace(' ', '_').replace('+', 'p')}__s{s}.pkl", "rb"))
                for en, p in probs.items():
                    y = tests[en]["label"].to_numpy()
                    ens.setdefault((tn, en, m), []).append(p)
                    for rg, mk in masks[(tn, en)].items():
                        if mk.sum() < 20 or len(np.unique(y[mk])) < 2:
                            continue
                        r = {"train_set": tn, "test_set": en, "regime": rg, "model": m, "seed": s, "n_train": len(trains[tn]),
                             "n_eval": int(mk.sum()), "analysis_tier": "exploratory"}
                        r.update(compute_metrics(y[mk], (p[mk] >= 0.5).astype(int), p[mk]))
                        rows.append(r)
    pd.DataFrame(rows)[COLS].to_csv(OUT, index=False)
    pdir = V2 / "predictions_cross"
    pdir.mkdir(exist_ok=True)
    for (tn, en, m), plist in ens.items():
        pm = np.mean(plist, axis=0)
        df = pd.DataFrame({"sequence": tests[en]["sequence"], "y_true": tests[en]["label"], "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)})
        for rg, mk in masks[(tn, en)].items():
            df[f"in_{rg}"] = mk
        df.to_csv(pdir / f"{tn}__{en}__{m.replace(' ', '_').replace('+', 'p')}.csv", index=False)
    mark("D_cross", "complete", t0.elapsed(), f"{len(jobs)} jobs this run; {len(rows)} metric rows")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=float, default=None)
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    print("jobs not started:", run(a.budget, a.jobs))
