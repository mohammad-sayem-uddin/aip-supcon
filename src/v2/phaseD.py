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


def task(args):
    torch.set_num_threads(1)
    tr_name, mkey, seed, tr_df, tests, store = args
    kind, clf, lam, tau = MODELS[mkey]
    Xtr, ytr = feats(kind, tr_df["sequence"].tolist(), store), tr_df["label"].to_numpy()
    Xt = [feats(kind, d["sequence"].tolist(), store) for d in tests.values()]
    probs = fit_predict(kind, clf, lam, tau, Xtr, ytr, Xt, seed)
    return tr_name, mkey, seed, dict(zip(tests, probs))


def run() -> int:
    t0 = Timer()
    S = load_sources()
    trains = {n: clean_train(S[k]) for n, k in TRAINS.items()}
    tests = {n: S[k].drop_duplicates("sequence").reset_index(drop=True) for n, k in TESTS.items()}
    allseqs = sorted({s for d in list(trains.values()) + list(tests.values()) for s in d["sequence"]})
    store = {"esm8": ext_embeddings("esm2_t6_8M", allseqs)}
    try:
        store["esm650"] = ext_embeddings("esm2_t33_650M", allseqs)
        models = list(MODELS)
    except Exception as e:  # e.g. disk or download problem: continue without 650M models and say so
        block("Phase D: 650M embeddings for external sequences failed", f"{type(e).__name__}: {e}. 650M-based models were skipped in Phase D.")
        models = [m for m in MODELS if "650" not in m]
    # regime masks per (train, test)
    masks = {}
    for tn, tdf in trains.items():
        trs = tdf["sequence"].tolist()
        for en, edf in tests.items():
            mx = max_identity_to_train(edf["sequence"].tolist(), trs, floor=0.8)
            exact = edf["sequence"].isin(set(trs)).to_numpy()
            masks[(tn, en)] = {"A": np.ones(len(edf), bool), "B": ~exact, "C": mx < 0.9 - 1e-12}
    done = set()
    if OUT.exists():
        d = pd.read_csv(OUT, usecols=["train_set", "model", "seed"])
        done = set(map(tuple, d.drop_duplicates().to_numpy()))
    jobs = [(tn, m, s, trains[tn], tests, store) for tn in trains for m in models for s in SEEDS if (tn, m, s) not in done]
    log.info("Phase D: %d training jobs", len(jobs))
    rows, ens = [], {}
    with ProcessPoolExecutor(max_workers=6, mp_context=mp.get_context("spawn")) as ex:
        for fu in as_completed([ex.submit(task, j) for j in jobs]):
            tn, mkey, seed, probs = fu.result()
            for en, p in probs.items():
                y = tests[en]["label"].to_numpy()
                ens.setdefault((tn, en, mkey), []).append(p)
                for rg, m in masks[(tn, en)].items():
                    if m.sum() < 20 or len(np.unique(y[m])) < 2:
                        continue
                    r = {"train_set": tn, "test_set": en, "regime": rg, "model": mkey, "seed": seed, "n_train": len(trains[tn]),
                         "n_eval": int(m.sum()), "analysis_tier": "exploratory"}
                    r.update(compute_metrics(y[m], (p[m] >= 0.5).astype(int), p[m]))
                    rows.append(r)
    if rows:
        pd.DataFrame(rows)[COLS].to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
    # ensemble predictions (for paired tests in Phase E)
    pdir = V2 / "predictions_cross"
    pdir.mkdir(exist_ok=True)
    for (tn, en, mkey), plist in ens.items():
        pm = np.mean(plist, axis=0)
        df = pd.DataFrame({"sequence": tests[en]["sequence"], "y_true": tests[en]["label"], "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)})
        for rg, m in masks[(tn, en)].items():
            df[f"in_{rg}"] = m
        df.to_csv(pdir / f"{tn}__{en}__{mkey.replace(' ', '_').replace('+', 'p')}.csv", index=False)
    mark("D_cross", "complete", t0.elapsed(), f"{len(jobs)} jobs")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
