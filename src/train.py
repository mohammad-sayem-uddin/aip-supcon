"""Training of AIPNet with L = BCE + lambda * SupCon: fold training, CV, final models, CLI.

lambda_supcon = 0 and lambda_supcon > 0 share one code path; only the multiplier differs.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import yaml
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import StandardScaler

from src.embed import get_embeddings
from src.evaluate import METRIC_NAMES, compute_metrics, find_optimal_threshold
from src.losses import SupConLoss
from src.model import AIPNet
from src.utils import ROOT, ProgressLogger, set_seed, setup_logging

log = setup_logging("train")

PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "results"
MODEL_DIR = RESULTS / "models"

RESULT_COLUMNS = (
    ["model", "family", "checkpoint", "lambda_supcon", "temperature", "eval_set", "regime", "seed", "fold",
     "epoch_stopped", "n_epochs_run", "train_seconds", "threshold"]
    + METRIC_NAMES
    + ["n_eval", "config_key", "config"]
)


@dataclass
class Config:
    name: str = "supcon_8m"
    checkpoint: str = "esm2_t6_8M"
    lambda_supcon: float = 0.5
    temperature: float = 0.07
    hidden_dims: tuple = (512, 256)
    proj_dim: int = 128
    dropout: float = 0.3
    lr: float = 1e-3
    weight_decay: float = 1e-4
    batch_size: int = 128
    max_epochs: int = 200
    patience: int = 20
    n_views: int = 1  # 2 = feature-space augmentation (two stochastic dropout views); exploratory only
    noise_sigma: float = 0.0  # Gaussian noise (std, on standardised features) added to each view when n_views == 2

    def key(self) -> str:
        d = asdict(self)
        d.pop("name")
        if d["n_views"] == 1 and d["noise_sigma"] == 0.0:  # keep keys of the pre-specified grid unchanged
            d.pop("n_views"); d.pop("noise_sigma")
        d["hidden_dims"] = list(d["hidden_dims"])
        return hashlib.md5(json.dumps(d, sort_keys=True).encode()).hexdigest()[:10]

    def model_name(self) -> str:
        base = f"{self.checkpoint}_lam{self.lambda_supcon:g}_tau{self.temperature:g}"
        if self.n_views == 2:
            base += f"_v2n{self.noise_sigma:g}"
        return base

    def family(self) -> str:
        return "deep" if (self.n_views == 1 and self.noise_sigma == 0.0) else "deep_explore"

    @staticmethod
    def from_yaml(path: str | Path) -> "Config":
        d = yaml.safe_load(open(path))
        if "hidden_dims" in d:
            d["hidden_dims"] = tuple(d["hidden_dims"])
        return Config(**d)

    def to_yaml(self, path: str | Path) -> None:
        d = asdict(self)
        d["hidden_dims"] = list(d["hidden_dims"])
        Path(path).write_text(yaml.safe_dump(d, sort_keys=False))


# ------------------------------------------------------------------ data


def load_benchmark(checkpoint: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    df = pd.read_csv(PROC / "benchmark_clean.csv")
    seqs = df["sequence"].tolist()
    return get_embeddings(checkpoint, seqs).astype(np.float32), df["label"].to_numpy(), seqs


def load_test(checkpoint: str, test_set: str, regime: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """test_set in {ind_425, ind_1049}; regime in {A, B, C}."""
    df = pd.read_csv(PROC / f"{test_set}_regime_{regime.lower()}.csv")
    seqs = df["sequence"].tolist()
    return get_embeddings(checkpoint, seqs).astype(np.float32), df["label"].to_numpy(), seqs


def make_folds(y: np.ndarray, seed: int, n_splits: int = 5) -> list[tuple[np.ndarray, np.ndarray]]:
    """The single source of CV splits; baselines import this so models share identical folds."""
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(skf.split(np.zeros(len(y)), y))


# ----------------------------------------------------------------- core


@torch.no_grad()
def _predict(model: AIPNet, X: torch.Tensor) -> np.ndarray:
    model.eval()
    return torch.sigmoid(model(X)["logit"]).cpu().numpy()


def train_fold(X_train, y_train, X_val, y_val, config: Config, seed: int = 0):
    """Train on (already scaled) arrays; early stop on validation MCC; return (model, history)."""
    set_seed(seed)
    Xt = torch.as_tensor(X_train, dtype=torch.float32)
    yt = torch.as_tensor(y_train, dtype=torch.float32)
    yt_long = torch.as_tensor(y_train, dtype=torch.long)
    Xv = torch.as_tensor(X_val, dtype=torch.float32)
    n_pos, n_neg = float((y_train == 1).sum()), float((y_train == 0).sum())
    model = AIPNet(Xt.shape[1], tuple(config.hidden_dims), config.proj_dim, config.dropout)
    opt = torch.optim.AdamW(model.parameters(), lr=config.lr, weight_decay=config.weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=config.max_epochs)
    bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(n_neg / n_pos))
    bce_val = nn.BCEWithLogitsLoss(pos_weight=torch.tensor(n_neg / n_pos))
    supcon = SupConLoss(config.temperature)
    gen = torch.Generator().manual_seed(seed)
    yv_t = torch.as_tensor(y_val, dtype=torch.float32)

    history, best_mcc, best_state, best_epoch, bad = [], -2.0, None, 0, 0
    n = Xt.shape[0]
    for epoch in range(1, config.max_epochs + 1):
        model.train()
        perm = torch.randperm(n, generator=gen)
        sums = np.zeros(3)
        nb = 0
        for i in range(0, n, config.batch_size):
            idx = perm[i : i + config.batch_size]
            if len(idx) < 2:
                continue
            xb = Xt[idx]
            if config.n_views == 2:
                o1 = model(xb + config.noise_sigma * torch.randn_like(xb))
                o2 = model(xb + config.noise_sigma * torch.randn_like(xb))
                logit = torch.cat([o1["logit"], o2["logit"]])
                proj = torch.cat([o1["projection"], o2["projection"]])
                yb, ylb = torch.cat([yt[idx]] * 2), torch.cat([yt_long[idx]] * 2)
            else:
                out = model(xb)
                logit, proj, yb, ylb = out["logit"], out["projection"], yt[idx], yt_long[idx]
            l_bce = bce(logit, yb)
            l_sc = supcon(proj, ylb)
            loss = l_bce + config.lambda_supcon * l_sc
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            sums += [loss.item(), l_bce.item(), l_sc.item()]
            nb += 1
        sched.step()
        model.eval()
        with torch.no_grad():
            vlogit = model(Xv)["logit"]
            vloss = bce_val(vlogit, yv_t).item()
            vprob = torch.sigmoid(vlogit).numpy()
        m = compute_metrics(y_val, (vprob >= 0.5).astype(int), vprob)
        history.append({"epoch": epoch, "train_loss": sums[0] / nb, "train_bce": sums[1] / nb,
                        "train_supcon": sums[2] / nb, "val_loss": vloss, "val_mcc": m["mcc"], "val_auroc": m["auroc"]})
        if m["mcc"] > best_mcc + 1e-9:
            best_mcc, best_epoch, bad = m["mcc"], epoch, 0
            best_state = copy.deepcopy(model.state_dict())
        else:
            bad += 1
            if bad >= config.patience:
                break
    model.load_state_dict(best_state)
    model.eval()
    for h in history:
        h["best_epoch"] = best_epoch
    return model, history


def _fit_scaler(X_train):
    sc = StandardScaler().fit(X_train)
    return sc


def _result_row(cfg: Config, model_name: str, family: str, eval_set: str, regime: str, seed: int, fold: int,
                best_epoch: int, n_epochs: int, secs: float, thr: float, y, prob, n_eval=None) -> dict:
    pred = (prob >= thr).astype(int)
    row = {"model": model_name, "family": family, "checkpoint": cfg.checkpoint,
           "lambda_supcon": cfg.lambda_supcon, "temperature": cfg.temperature, "eval_set": eval_set,
           "regime": regime, "seed": seed, "fold": fold, "epoch_stopped": best_epoch, "n_epochs_run": n_epochs,
           "train_seconds": round(secs, 2), "threshold": thr}
    row.update(compute_metrics(y, pred, prob))
    row["n_eval"] = len(y) if n_eval is None else n_eval
    row["config_key"] = cfg.key()
    row["config"] = json.dumps({**asdict(cfg), "hidden_dims": list(cfg.hidden_dims)}, sort_keys=True)
    return row


@lru_cache(maxsize=8)
def _cached_benchmark(checkpoint: str):
    return load_benchmark(checkpoint)


def run_one_fold(task: tuple) -> dict:
    """One (config, seed, fold) CV unit of work; top-level so it can run in a worker process."""
    cfg_dict, seed, fold = task
    torch.set_num_threads(1)
    cfg_dict = dict(cfg_dict)
    cfg_dict["hidden_dims"] = tuple(cfg_dict["hidden_dims"])
    cfg = Config(**cfg_dict)
    X, y, _ = _cached_benchmark(cfg.checkpoint)
    tr, va = make_folds(y, seed)[fold]
    sc = _fit_scaler(X[tr])
    t0 = time.time()
    model, hist = train_fold(sc.transform(X[tr]), y[tr], sc.transform(X[va]), y[va], cfg, seed=1000 * seed + fold)
    secs = time.time() - t0
    prob = _predict(model, torch.as_tensor(sc.transform(X[va]), dtype=torch.float32))
    return _result_row(cfg, cfg.model_name(), cfg.family(), "cv", "cv", seed, fold, hist[0]["best_epoch"], len(hist),
                       secs, 0.5, y[va], prob)


def cross_validate(X=None, y=None, config: Config | None = None, n_splits: int = 5,
                   seeds: tuple = (0, 1, 2, 3, 4), n_jobs: int = 1, skip_done: bool = True) -> pd.DataFrame:
    """5-fold x seeds CV for one config. Rows are returned and appended to results/cv_results.csv."""
    assert n_splits == 5, "fold layout fixed to 5"
    cfg = config
    out_csv = RESULTS / "cv_results.csv"
    done = set()
    if skip_done and out_csv.exists():
        prev = pd.read_csv(out_csv, usecols=["config_key", "seed", "fold"])
        done = set(map(tuple, prev.loc[prev["config_key"] == cfg.key(), ["seed", "fold"]].to_numpy()))
    cfg_dict = {**asdict(cfg), "hidden_dims": list(cfg.hidden_dims)}
    tasks = [(cfg_dict, s, f) for s in seeds for f in range(n_splits) if (s, f) not in done]
    if not tasks:
        log.info("%s: all CV rows already present, skipping", cfg.model_name())
        return pd.read_csv(out_csv).query("config_key == @cfg.key()")
    t0 = time.time()
    if n_jobs > 1:
        import multiprocessing as mp
        with ProcessPoolExecutor(max_workers=n_jobs, mp_context=mp.get_context("spawn")) as ex:
            rows = list(ex.map(run_one_fold, tasks, chunksize=1))
    else:
        rows = [run_one_fold(t) for t in tasks]
    df = pd.DataFrame(rows)[RESULT_COLUMNS]
    append_results(df, out_csv)
    log.info("%s: %d CV runs in %.1fs | MCC %.4f AUROC %.4f", cfg.model_name(), len(df), time.time() - t0,
             df["mcc"].mean(), df["auroc"].mean())
    return df


def append_results(df: pd.DataFrame, path: Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df[RESULT_COLUMNS]
    df.to_csv(path, mode="a", header=not path.exists(), index=False)


# ------------------------------------------------------------ final models


def train_final(X, y, config: Config, seed: int = 0, save: bool = True) -> dict:
    """Train on all of benchmark_clean with a stratified 10% hold-out for early stopping.

    Returns a bundle: model, scaler stats, threshold tuned on the hold-out (never on test data).
    """
    idx = np.arange(len(y))
    tr, ho = train_test_split(idx, test_size=0.1, stratify=y, random_state=seed)
    sc = _fit_scaler(X[tr])
    t0 = time.time()
    model, hist = train_fold(sc.transform(X[tr]), y[tr], sc.transform(X[ho]), y[ho], config, seed=seed)
    secs = time.time() - t0
    ho_prob = _predict(model, torch.as_tensor(sc.transform(X[ho]), dtype=torch.float32))
    bundle = {"model": model, "mean": sc.mean_.astype(np.float32), "scale": sc.scale_.astype(np.float32),
              "threshold": find_optimal_threshold(y[ho], ho_prob), "seed": seed, "config": config,
              "history": hist, "train_seconds": secs, "best_epoch": hist[0]["best_epoch"]}
    if save:
        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        torch.save({"state_dict": model.state_dict(), "mean": bundle["mean"], "scale": bundle["scale"],
                    "threshold": bundle["threshold"], "config": asdict(config)},
                   MODEL_DIR / f"{config.model_name()}_seed{seed}.pt")
    return bundle


def predict_bundle(bundle: dict, X: np.ndarray) -> np.ndarray:
    Xs = (X - bundle["mean"]) / bundle["scale"]
    return _predict(bundle["model"], torch.as_tensor(Xs, dtype=torch.float32))


@torch.no_grad()
def latents(bundle: dict, X: np.ndarray) -> dict[str, np.ndarray]:
    """Encoder output (256-d) and projection (128-d) for visualisation."""
    Xs = torch.as_tensor((X - bundle["mean"]) / bundle["scale"], dtype=torch.float32)
    bundle["model"].eval()
    out = bundle["model"](Xs)
    return {"embedding": out["embedding"].numpy(), "projection": out["projection"].numpy()}


# --------------------------------------------------------------------- CLI

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--n-jobs", type=int, default=1)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    cfg = Config.from_yaml(a.config)
    log.info("config %s: %s", a.config, cfg)
    df = cross_validate(config=cfg, seeds=tuple(a.seeds), n_jobs=a.n_jobs, skip_done=not a.force)
    print(df[METRIC_NAMES].mean().round(4).to_string())
