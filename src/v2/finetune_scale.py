"""C3-scale: fine-tune a larger ESM-2 checkpoint (150M or 650M) with exactly the protocol of src/v2/finetune.py (same head, loop, folds, seeds,
learning rates 5e-5 / 1e-3, batch 32, at most 8 epochs, patience 3). Differences: model path and tag come from the environment, the best-epoch
weights are kept on the CPU (GPU memory), results go to their own files. Meant for a Kaggle GPU (BLOCKERS_v2.md).
Environment: AIP_FT_MODEL_PATH, AIP_FT_TAG (e.g. esm2_t30_150M), AIP_FT_TOK_PATH (directory with vocab.txt).
Usage: python -m src.v2.finetune_scale [--smoke] --cv-seeds 0 1 2 --final-seeds 0 1 2 3 4
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split
from transformers import EsmModel, EsmTokenizer

from src.evaluate import METRIC_NAMES, compute_metrics
from src.train import PROC, make_folds
from src.utils import Timer, set_seed, setup_logging
from src.v2.common import V2, mark

log = setup_logging("finetune_scale")
HF = os.environ["AIP_FT_MODEL_PATH"]
TAG = os.environ["AIP_FT_TAG"]
TOK = os.environ.get("AIP_FT_TOK_PATH", HF)
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")
TESTS = [(ts, rg) for ts in ("ind_425", "ind_1049") for rg in ("A", "B", "C")]
OUT = V2 / f"finetune_scale_{TAG}.csv"
COLS = ["model", "mode", "eval_set", "regime", "seed", "fold", "epoch_stopped", "train_seconds", "analysis_tier"] + METRIC_NAMES + ["n_eval"]


class FTNet(nn.Module):
    def __init__(self, freeze: bool):
        super().__init__()
        self.bb = EsmModel.from_pretrained(HF, add_pooling_layer=False)
        self.freeze = freeze
        if freeze:
            for p in self.bb.parameters():
                p.requires_grad_(False)
        d = self.bb.config.hidden_size
        self.head = nn.Sequential(nn.Linear(d, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(0.3))
        self.clf = nn.Linear(256, 1)

    def forward(self, ids, att):
        if self.freeze:
            self.bb.eval()
            with torch.no_grad():
                h = self.bb(input_ids=ids, attention_mask=att).last_hidden_state
        else:
            h = self.bb(input_ids=ids, attention_mask=att).last_hidden_state
        m = att.clone().float()
        m[:, 0] = 0
        m[torch.arange(len(m)), att.sum(1) - 1] = 0
        pooled = (h * m.unsqueeze(-1)).sum(1) / m.sum(1, keepdim=True)
        return self.clf(self.head(pooled)).squeeze(-1)


def tok(seqs, tokenizer):
    e = tokenizer(seqs, return_tensors="pt", padding=True)
    return e["input_ids"], e["attention_mask"]


@torch.no_grad()
def predict(model, ids, att, bs=128):
    model.eval()
    out = []
    for i in range(0, len(ids), bs):
        a = att[i : i + bs]
        L = int(a.sum(1).max())
        out.append(torch.sigmoid(model(ids[i : i + bs, :L].to(DEV), a[:, :L].to(DEV))).cpu())
    return torch.cat(out).numpy()


def fit(model, tr, va, y_tr, y_va, seed, max_epochs=8, patience=3, bs=32, lr_bb=5e-5, lr_head=1e-3):
    set_seed(seed)
    tr = (tr[0].to(DEV), tr[1].to(DEV))
    groups = [{"params": list(model.head.parameters()) + list(model.clf.parameters()), "lr": lr_head}]
    if not model.freeze:
        groups.append({"params": list(model.bb.parameters()), "lr": lr_bb})
    opt = torch.optim.AdamW(groups, weight_decay=1e-4, foreach=False)  # foreach=False avoids a full-size temporary copy (650M OOM on a 15 GB T4)
    pw = torch.tensor(float((y_tr == 0).sum()) / float((y_tr == 1).sum()), device=DEV)
    bce = nn.BCEWithLogitsLoss(pos_weight=pw)
    yt = torch.as_tensor(y_tr, dtype=torch.float32, device=DEV)
    gen = torch.Generator().manual_seed(seed)
    best, state, best_ep, bad = -2.0, None, 0, 0
    for ep in range(1, max_epochs + 1):
        model.train()
        if model.freeze:
            model.bb.eval()
        perm = torch.randperm(len(yt), generator=gen).to(DEV)
        for i in range(0, len(perm), bs):
            b = perm[i : i + bs]
            if len(b) < 2:
                continue
            ids, att = tr[0][b], tr[1][b]
            L = int(att.sum(1).max())
            loss = bce(model(ids[:, :L], att[:, :L]), yt[b])
            opt.zero_grad(set_to_none=True)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
        p = predict(model, *va)
        m = compute_metrics(y_va, (p >= 0.5).astype(int), p)
        log.info("   epoch %d val MCC %.3f", ep, m["mcc"])
        if m["mcc"] > best + 1e-9:
            best, best_ep, bad, state = m["mcc"], ep, 0, {k: v.detach().to("cpu", copy=True) for k, v in model.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    model.load_state_dict(state)
    return model, best_ep


def row(mode, ts, rg, seed, fold, ep, secs, y, p):
    r = {"model": f"{TAG}_{mode}", "mode": mode, "eval_set": ts, "regime": rg, "seed": seed, "fold": fold,
         "epoch_stopped": ep, "train_seconds": round(secs, 1), "analysis_tier": "exploratory"}
    r.update(compute_metrics(y, (p >= 0.5).astype(int), p))
    r["n_eval"] = len(y)
    return r


def run(smoke: bool = False, cv_seeds=(0,), final_seeds=(0, 1, 2)) -> None:
    t = Timer()
    tz = EsmTokenizer.from_pretrained(TOK)
    b = pd.read_csv(PROC / "benchmark_clean.csv")
    seqs, y = b["sequence"].tolist(), b["label"].to_numpy()
    ids, att = tok(seqs, tz)
    rows = []
    done = set()
    if OUT.exists():
        d = pd.read_csv(OUT, usecols=["mode", "eval_set", "seed", "fold"])
        done = set(map(tuple, d.to_numpy()))
    cv_seeds, folds, final_seeds = ((0,), (0,), (0,)) if smoke else (tuple(cv_seeds), range(5), tuple(final_seeds))
    for mode in ("frozen", "finetune"):
        for seed in cv_seeds:
            for f in folds:
                if (mode, "cv", seed, f) in done:
                    continue
                tr, va = make_folds(y, seed)[f]
                model = FTNet(mode == "frozen").to(DEV)
                t0 = time.time()
                model, ep = fit(model, (ids[tr], att[tr]), (ids[va], att[va]), y[tr], y[va], 1000 * seed + f)
                r = row(mode, "cv", "cv", seed, f, ep, time.time() - t0, y[va], predict(model, ids[va], att[va]))
                log.info("%s seed %d fold %d: MCC %.3f AUROC %.3f in %.0fs", mode, seed, f, r["mcc"], r["auroc"], r["train_seconds"])
                rows.append(r)
                del model
                torch.cuda.empty_cache()
                pd.DataFrame([r])[COLS].to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
    if smoke:
        return
    pdir = V2 / "predictions"
    pdir.mkdir(exist_ok=True)
    tests = {}
    for ts, rg in TESTS:
        d = pd.read_csv(PROC / f"{ts}_regime_{rg.lower()}.csv")
        tests[(ts, rg)] = (d, *tok(d["sequence"].tolist(), tz))
    for mode in ("frozen", "finetune"):
        per = {k: [] for k in tests}
        for seed in final_seeds:
            if (mode, "ind_425", seed, -1) in done:
                continue
            tr, ho = train_test_split(np.arange(len(y)), test_size=0.1, stratify=y, random_state=seed)
            model = FTNet(mode == "frozen").to(DEV)
            t0 = time.time()
            model, ep = fit(model, (ids[tr], att[tr]), (ids[ho], att[ho]), y[tr], y[ho], seed)
            secs = time.time() - t0
            for (ts, rg), (d, i2, a2) in tests.items():
                p = predict(model, i2, a2)
                per[(ts, rg)].append(p)
                r = row(mode, ts, rg, seed, -1, ep, secs, d["label"].to_numpy(), p)
                pd.DataFrame([r])[COLS].to_csv(OUT, mode="a", header=not OUT.exists(), index=False)
            log.info("final %s seed %d done in %.0fs", mode, seed, secs)
            del model
            torch.cuda.empty_cache()
        for (ts, rg), plist in per.items():
            if not plist:
                continue
            d = tests[(ts, rg)][0]
            pm = np.mean(plist, axis=0)
            out = {"sequence": d["sequence"], "y_true": d["label"], "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)}
            for s, p in zip(final_seeds, plist):
                out[f"prob_seed{s}"] = p
            pd.DataFrame(out).to_csv(pdir / f"{TAG}_{mode}_{ts}_{rg}.csv", index=False)
    mark(f"C3_scale_{TAG}", "complete", t.elapsed(), f"{TAG} fine-tune vs frozen control")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--cv-seeds", type=int, nargs="*", default=[0])
    ap.add_argument("--final-seeds", type=int, nargs="*", default=[0, 1, 2])
    a = ap.parse_args()
    run(a.smoke, a.cv_seeds, a.final_seeds)
