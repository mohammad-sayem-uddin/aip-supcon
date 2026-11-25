"""Trainer for Phase B/C residue-level models: same protocol as v1 (make_folds, seeds, AdamW 1e-3, BCE + lambda*SupCon,
cosine schedule, early stopping on validation MCC, patience 20, scaler on training fold only)."""
from __future__ import annotations

import copy
import hashlib
import json
import time
from dataclasses import asdict, dataclass
from functools import lru_cache

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split

from src.evaluate import METRIC_NAMES, compute_metrics, find_optimal_threshold
from src.losses import SupConLoss
from src.train import PROC, make_folds
from src.utils import set_seed, setup_logging
from src.v2.common import V2
from src.v2.embed_res import load_residue_cache
from src.v2.models import MAXLEN, build

log = setup_logging("v2train")
V2_COLUMNS = (["model", "arch", "checkpoint", "lambda_supcon", "temperature", "eval_set", "regime", "seed", "fold", "epoch_stopped",
               "n_epochs_run", "train_seconds", "threshold", "analysis_tier"] + METRIC_NAMES + ["n_eval", "config_key"])


@dataclass
class V2Cfg:
    arch: str = "B2_cnn"
    checkpoint: str = "esm2_t6_8M"
    lambda_supcon: float = 0.0
    temperature: float = 0.07
    lr: float = 1e-3
    weight_decay: float = 1e-4
    batch_size: int = 128
    max_epochs: int = 200
    patience: int = 20
    clip: float = 1.0

    def name(self) -> str:
        return f"{self.arch}_{self.checkpoint}_lam{self.lambda_supcon:g}_tau{self.temperature:g}"

    def key(self) -> str:
        return hashlib.md5(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:10]


@lru_cache(maxsize=4)
def _cache(checkpoint: str):
    idx, res, cls = load_residue_cache(checkpoint)
    lookup = {s: i for i, s in enumerate(idx["sequences"])}
    return idx, np.asarray(res), lookup


def tensors(seqs: list[str], checkpoint: str):
    """Padded (n, MAXLEN, d) float16 array, mask (n, MAXLEN) bool, lengths."""
    idx, res, lookup = _cache(checkpoint)
    d = res.shape[1]
    X = np.zeros((len(seqs), MAXLEN, d), dtype=np.float16)
    M = np.zeros((len(seqs), MAXLEN), dtype=bool)
    for r, s in enumerate(seqs):
        i = lookup[s]
        o, L = idx["offsets"][i], idx["lengths"][i]
        X[r, :L] = res[o : o + L]
        M[r, :L] = True
    return X, M


@lru_cache(maxsize=2)
def benchmark(checkpoint: str):
    df = pd.read_csv(PROC / "benchmark_clean.csv")
    X, M = tensors(df["sequence"].tolist(), checkpoint)
    return X, M, df["label"].to_numpy(), df["sequence"].tolist()


def test_data(checkpoint: str, test_set: str, regime: str):
    df = pd.read_csv(PROC / f"{test_set}_regime_{regime.lower()}.csv")
    X, M = tensors(df["sequence"].tolist(), checkpoint)
    return X, M, df["label"].to_numpy(), df["sequence"].tolist()


def _fit_norm(X, M):
    v = X[M].astype(np.float32)
    return v.mean(0), v.std(0) + 1e-6


def _prep(X, M, mean, std):
    Xn = (X.astype(np.float32) - mean) / std
    Xn[~M] = 0.0
    return torch.as_tensor(Xn), torch.as_tensor(M)


@torch.no_grad()
def predict(model, X: torch.Tensor, M: torch.Tensor, bs: int = 256) -> np.ndarray:
    model.eval()
    out = []
    for i in range(0, len(X), bs):
        Lb = int(M[i : i + bs].sum(1).max())
        out.append(torch.sigmoid(model(X[i : i + bs, :Lb], M[i : i + bs, :Lb])["logit"]))
    return torch.cat(out).numpy()


def fit(Xtr, Mtr, ytr, Xva, Mva, yva, cfg: V2Cfg, seed: int):
    """Xtr etc. are already-normalised tensors. Returns (model, history, best_epoch)."""
    set_seed(seed)
    model = build(cfg.arch, Xtr.shape[2])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=cfg.max_epochs)
    pw = torch.tensor(float((ytr == 0).sum()) / float((ytr == 1).sum()))
    bce = nn.BCEWithLogitsLoss(pos_weight=pw)
    sc = SupConLoss(cfg.temperature)
    yt = torch.as_tensor(ytr, dtype=torch.float32)
    ytl = torch.as_tensor(ytr, dtype=torch.long)
    gen = torch.Generator().manual_seed(seed)
    best, best_state, best_ep, bad, hist = -2.0, None, 0, 0, []
    n = len(Xtr)
    for ep in range(1, cfg.max_epochs + 1):
        model.train()
        perm = torch.randperm(n, generator=gen)
        s = np.zeros(3)
        nb = 0
        for i in range(0, n, cfg.batch_size):
            b = perm[i : i + cfg.batch_size]
            if len(b) < 2:
                continue
            Lb = int(Mtr[b].sum(1).max())
            out = model(Xtr[b, :Lb], Mtr[b, :Lb])
            lb, ls = bce(out["logit"], yt[b]), sc(out["projection"], ytl[b])
            loss = lb + cfg.lambda_supcon * ls
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), cfg.clip)
            opt.step()
            s += [loss.item(), lb.item(), ls.item()]
            nb += 1
        sched.step()
        p = predict(model, Xva, Mva)
        m = compute_metrics(yva, (p >= 0.5).astype(int), p)
        hist.append({"epoch": ep, "train_bce": s[1] / nb, "train_supcon": s[2] / nb, "val_mcc": m["mcc"]})
        if m["mcc"] > best + 1e-9:
            best, best_ep, bad = m["mcc"], ep, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            bad += 1
            if bad >= cfg.patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    return model, hist, best_ep


def _row(cfg: V2Cfg, eval_set, regime, seed, fold, ep, nep, secs, thr, y, p, tier) -> dict:
    row = {"model": cfg.name(), "arch": cfg.arch, "checkpoint": cfg.checkpoint, "lambda_supcon": cfg.lambda_supcon,
           "temperature": cfg.temperature, "eval_set": eval_set, "regime": regime, "seed": seed, "fold": fold,
           "epoch_stopped": ep, "n_epochs_run": nep, "train_seconds": round(secs, 2), "threshold": thr, "analysis_tier": tier}
    row.update(compute_metrics(y, (p >= thr).astype(int), p))
    row["n_eval"], row["config_key"] = len(y), cfg.key()
    return row


def cv_unit(task: tuple) -> dict:
    cfgd, seed, fold = task
    torch.set_num_threads(1)
    cfg = V2Cfg(**cfgd)
    X, M, y, _ = benchmark(cfg.checkpoint)
    tr, va = make_folds(y, seed)[fold]
    mean, std = _fit_norm(X[tr], M[tr])
    Xtr, Mtr = _prep(X[tr], M[tr], mean, std)
    Xva, Mva = _prep(X[va], M[va], mean, std)
    t0 = time.time()
    model, hist, ep = fit(Xtr, Mtr, y[tr], Xva, Mva, y[va], cfg, seed=1000 * seed + fold)
    return _row(cfg, "cv", "cv", seed, fold, ep, len(hist), time.time() - t0, 0.5, y[va], predict(model, Xva, Mva), "secondary")


def final_unit(task: tuple) -> dict:
    """Train on all of benchmark_clean (10% stratified hold-out for early stopping); predict all test sets/regimes."""
    cfgd, seed, tests = task
    torch.set_num_threads(1)
    cfg = V2Cfg(**cfgd)
    X, M, y, _ = benchmark(cfg.checkpoint)
    tr, ho = train_test_split(np.arange(len(y)), test_size=0.1, stratify=y, random_state=seed)
    mean, std = _fit_norm(X[tr], M[tr])
    Xtr, Mtr = _prep(X[tr], M[tr], mean, std)
    Xho, Mho = _prep(X[ho], M[ho], mean, std)
    t0 = time.time()
    model, hist, ep = fit(Xtr, Mtr, y[tr], Xho, Mho, y[ho], cfg, seed=seed)
    secs = time.time() - t0
    res = {"cfg": cfgd, "seed": seed, "epoch": ep, "n_epochs": len(hist), "secs": secs, "preds": {}}
    for ts, rg in tests:
        Xt, Mt, yt, st = test_data(cfg.checkpoint, ts, rg)
        Xn, Mn = _prep(Xt, Mt, mean, std)
        res["preds"][(ts, rg)] = predict(model, Xn, Mn)
    return res
