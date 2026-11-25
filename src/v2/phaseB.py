"""Phase B: architectures B2-B6 (B1 = v1 MLP, reused) x lambda, CV + final models on Regimes A/B/C.

Foreground, resumable, time-budgeted slices:
  python -m src.v2.phaseB cv    --archs B4_cnn_bilstm [--budget 420] [--jobs 6]
  python -m src.v2.phaseB final --archs B3_bilstm B4_cnn_bilstm [--budget 420] [--jobs 6]
Every completed CV run appends one flushed line to results/phase_b_progress.log.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import pickle
import sys
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from dataclasses import asdict
from datetime import datetime

import numpy as np
import pandas as pd

from src.utils import Timer, setup_logging
from src.v2.common import R, V2, mark
from src.v2.models import ARCHS
from src.v2.train import V2_COLUMNS, V2Cfg, _row, cv_unit, final_unit

log = setup_logging("phaseB")
LAMS = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]
SEEDS = (0, 1, 2, 3, 4)
CKPT = "esm2_t6_8M"
TESTS = [(ts, rg) for ts in ("ind_425", "ind_1049") for rg in ("A", "B", "C")]
CV_FILE, FINAL_FILE = V2 / "cv_results_v2.csv", V2 / "final_results_v2.csv"
PROGRESS = R / "phase_b_progress.log"
CACHE = V2 / "final_cache"
COST = {"B3_bilstm": 5, "B4_cnn_bilstm": 4, "B5_transformer": 3, "B2_cnn": 2, "B6_attnpool": 1}


def progress(line: str) -> None:
    with open(PROGRESS, "a") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())


def append(df: pd.DataFrame, path) -> None:
    df[V2_COLUMNS].to_csv(path, mode="a", header=not path.exists(), index=False)


def rolling(tasks, fn, on_result, n_jobs: int, budget: float | None) -> int:
    """Run tasks on a process pool in the foreground, never more than n_jobs in flight; stop submitting after `budget`
    seconds. Returns the number of tasks not started."""
    t0 = time.time()
    todo = list(tasks)
    pending: set = set()
    with ProcessPoolExecutor(max_workers=n_jobs, mp_context=mp.get_context("spawn")) as ex:
        while todo or pending:
            while todo and len(pending) < n_jobs and (budget is None or time.time() - t0 < budget):
                pending.add(ex.submit(fn, todo.pop(0)))
            if not pending:
                break
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for fu in done:
                on_result(fu.result())
    return len(todo)


def run_cv(archs=ARCHS, checkpoint: str = CKPT, budget: float | None = None, n_jobs: int = 6, lams=LAMS) -> int:
    done = set()
    if CV_FILE.exists():
        d = pd.read_csv(CV_FILE, usecols=["config_key", "seed", "fold"])[["config_key", "seed", "fold"]]  # usecols keeps file order
        done = {(k, int(s), int(f)) for k, s, f in d.to_numpy()}
    tasks = []
    for a in archs:
        for lam in lams:
            cfg = V2Cfg(arch=a, checkpoint=checkpoint, lambda_supcon=lam)
            for s in SEEDS:
                for f in range(5):
                    if (cfg.key(), s, f) not in done:
                        tasks.append((COST[a], (asdict(cfg), s, f)))
    tasks.sort(key=lambda x: -x[0])
    total_done = len(done)
    log.info("Phase B CV: %d tasks left for %s", len(tasks), list(archs))
    progress(f"# {datetime.now().isoformat(timespec='seconds')} slice start: {len(tasks)} tasks left for {list(archs)}; {total_done} rows already saved")

    def on_result(r: dict) -> None:
        append(pd.DataFrame([r]), CV_FILE)
        progress(f"{datetime.now().isoformat(timespec='seconds')}, {r['arch']}, lambda={r['lambda_supcon']:g}, seed={r['seed']}, "
                 f"fold={r['fold']}, MCC={r['mcc']:.4f}, elapsed={r['train_seconds']:.0f}s")

    left = rolling([tk for _, tk in tasks], cv_unit, on_result, n_jobs, budget)
    progress(f"# slice end: {left} tasks still to start")
    if left == 0 and tasks:
        mark("B_cv", "complete", 0.0, f"CV complete for {list(archs)}")
    return left


def select(archs=None) -> dict:
    cv = pd.read_csv(CV_FILE)
    sel = {}
    for a, g in cv.groupby("arch"):
        if archs and a not in archs:
            continue
        m = g.groupby("lambda_supcon")["mcc"].mean()
        pos = m[m.index > 0]
        best = float(pos.sort_index().idxmax())  # idxmax returns the first max -> smaller lambda on ties
        sel[a] = {"lambda_star": best, "cv_mcc_lambda0": float(m[0.0]), "cv_mcc_star": float(pos[best]), "n_runs": int(len(g)),
                  "cv_table": {str(k): v for k, v in m.round(4).to_dict().items()}}
    old = json.loads((V2 / "selected_v2.json").read_text()) if (V2 / "selected_v2.json").exists() else {}
    old.update(sel)
    (V2 / "selected_v2.json").write_text(json.dumps(old, indent=2))
    return sel


def _final_task(task):
    r = final_unit(task)
    cfg = V2Cfg(**r["cfg"])
    CACHE.mkdir(parents=True, exist_ok=True)
    with open(CACHE / f"{cfg.name()}_seed{r['seed']}.pkl", "wb") as f:
        pickle.dump(r, f)
    return cfg.name(), r["seed"]


def run_final(archs=ARCHS, checkpoint: str = CKPT, budget: float | None = None, n_jobs: int = 6) -> int:
    t = Timer()
    sel = select(set(archs))
    CACHE.mkdir(parents=True, exist_ok=True)
    jobs = []
    for a in archs:
        for lam in (0.0, sel[a]["lambda_star"]):
            cfg = V2Cfg(arch=a, checkpoint=checkpoint, lambda_supcon=lam)
            jobs += [(COST[a], (asdict(cfg), s, TESTS)) for s in SEEDS if not (CACHE / f"{cfg.name()}_seed{s}.pkl").exists()]
    jobs.sort(key=lambda x: -x[0])
    progress(f"# final-model slice start: {len(jobs)} jobs left for {list(archs)}")
    left = rolling([tk for _, tk in jobs], _final_task,
                   lambda r: progress(f"{datetime.now().isoformat(timespec='seconds')}, FINAL {r[0]}, seed={r[1]} cached"), n_jobs, budget)
    progress(f"# final slice end: {left} jobs still to start")
    if left == 0:
        assemble_final(archs, sel, checkpoint)
        mark("B_final", "complete", t.elapsed(), f"final models for {list(archs)}")
    return left


def assemble_final(archs, sel, checkpoint: str = CKPT) -> None:
    PRED = V2 / "predictions"
    PRED.mkdir(parents=True, exist_ok=True)
    have = set(pd.read_csv(FINAL_FILE, usecols=["model"])["model"]) if FINAL_FILE.exists() else set()
    labels = {(ts, rg): pd.read_csv(f"data/processed/{ts}_regime_{rg.lower()}.csv") for ts, rg in TESTS}
    rows = []
    for a in archs:
        for lam in (0.0, sel[a]["lambda_star"]):
            cfg = V2Cfg(arch=a, checkpoint=checkpoint, lambda_supcon=lam)
            if cfg.name() in have:
                continue
            rs = [pickle.load(open(CACHE / f"{cfg.name()}_seed{s}.pkl", "rb")) for s in SEEDS]
            for (ts, rg), df in labels.items():
                y = df["label"].to_numpy()
                plist = [r["preds"][(ts, rg)] for r in rs]
                for r, p in zip(rs, plist):
                    rows.append(_row(cfg, ts, rg, r["seed"], -1, r["epoch"], r["n_epochs"], r["secs"], 0.5, y, p, "secondary"))
                pm = np.mean(plist, axis=0)
                d = {"sequence": df["sequence"], "y_true": y, "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)}
                for r, p in zip(rs, plist):
                    d[f"prob_seed{r['seed']}"] = p
                pd.DataFrame(d).to_csv(PRED / f"{cfg.name()}_{ts}_{rg}.csv", index=False)
    if rows:
        append(pd.DataFrame(rows), FINAL_FILE)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["cv", "final", "select"])
    ap.add_argument("--archs", nargs="+", default=ARCHS)
    ap.add_argument("--budget", type=float, default=None, help="seconds after which no new task is started")
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    if a.what == "cv":
        print("tasks not started:", run_cv(a.archs, budget=a.budget, n_jobs=a.jobs))
    elif a.what == "final":
        print("jobs not started:", run_final(a.archs, budget=a.budget, n_jobs=a.jobs))
    else:
        print(json.dumps(select(set(a.archs)), indent=1))
