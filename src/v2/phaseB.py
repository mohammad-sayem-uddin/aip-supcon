"""Phase B: architectures B2-B6 (B1 = v1 MLP, reused) x lambda, CV + final models on Regimes A/B/C.

Run: python -m src.v2.phaseB [cv|select|final|tables|all]  (resumable; results in results/v2/)
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict

import numpy as np
import pandas as pd

from src.evaluate import compute_metrics
from src.utils import ProgressLogger, Timer, setup_logging
from src.v2.common import R, V2, mark
from src.v2.models import ARCHS
from src.v2.stats import compare_arrays
from src.v2.train import V2_COLUMNS, V2Cfg, _row, cv_unit, final_unit

log = setup_logging("phaseB")
LAMS = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]
SEEDS = (0, 1, 2, 3, 4)
CKPT = "esm2_t6_8M"
N_JOBS = 6
TESTS = [(ts, rg) for ts in ("ind_425", "ind_1049") for rg in ("A", "B", "C")]
CV_FILE, FINAL_FILE = V2 / "cv_results_v2.csv", V2 / "final_results_v2.csv"
COST = {"B3_bilstm": 5, "B4_cnn_bilstm": 4, "B5_transformer": 3, "B2_cnn": 2, "B6_attnpool": 1}


def append(df: pd.DataFrame, path) -> None:
    df[V2_COLUMNS].to_csv(path, mode="a", header=not path.exists(), index=False)


def run_cv(archs=ARCHS, checkpoint: str = CKPT) -> None:
    t = Timer()
    done = set()
    if CV_FILE.exists():
        d = pd.read_csv(CV_FILE, usecols=["config_key", "seed", "fold"])
        done = set(map(tuple, d.to_numpy()))
    tasks = []
    for a in archs:
        for lam in LAMS:
            cfg = V2Cfg(arch=a, checkpoint=checkpoint, lambda_supcon=lam)
            for s in SEEDS:
                for f in range(5):
                    if (cfg.key(), s, f) not in done:
                        tasks.append((COST[a], (asdict(cfg), s, f)))
    tasks.sort(key=lambda x: -x[0])
    log.info("Phase B CV: %d tasks to run", len(tasks))
    if not tasks:
        return
    prog = ProgressLogger(len(tasks), "phaseB CV", log, every=300)
    with ProcessPoolExecutor(max_workers=N_JOBS, mp_context=mp.get_context("spawn")) as ex:
        futs = [ex.submit(cv_unit, tk) for _, tk in tasks]
        for fu in as_completed(futs):
            append(pd.DataFrame([fu.result()]), CV_FILE)
            prog.step()
    mark("B_cv", "complete", t.elapsed(), f"{len(tasks)} CV runs")


def select() -> dict:
    cv = pd.read_csv(CV_FILE)
    sel = {}
    for a, g in cv.groupby("arch"):
        m = g.groupby("lambda_supcon")["mcc"].mean()
        pos = m[m.index > 0]
        best = float(pos.sort_index().idxmax())  # idxmax returns first max -> smaller lambda on ties
        sel[a] = {"lambda_star": best, "cv_mcc_lambda0": float(m[0.0]), "cv_mcc_star": float(pos[best]), "cv_table": m.round(4).to_dict()}
    (V2 / "selected_v2.json").write_text(json.dumps(sel, indent=2))
    return sel


def run_final(archs=ARCHS, checkpoint: str = CKPT) -> None:
    t = Timer()
    sel = select()
    PRED = V2 / "predictions"
    PRED.mkdir(parents=True, exist_ok=True)
    have = set(pd.read_csv(FINAL_FILE, usecols=["model"])["model"]) if FINAL_FILE.exists() else set()
    jobs = []
    for a in archs:
        for lam in (0.0, sel[a]["lambda_star"]):
            cfg = V2Cfg(arch=a, checkpoint=checkpoint, lambda_supcon=lam)
            if cfg.name() not in have:
                jobs += [(COST[a], (asdict(cfg), s, TESTS)) for s in SEEDS]
    jobs.sort(key=lambda x: -x[0])
    log.info("Phase B final: %d training jobs", len(jobs))
    results: dict[str, list] = {}
    with ProcessPoolExecutor(max_workers=N_JOBS, mp_context=mp.get_context("spawn")) as ex:
        futs = [ex.submit(final_unit, tk) for _, tk in jobs]
        for fu in as_completed(futs):
            r = fu.result()
            results.setdefault(V2Cfg(**r["cfg"]).name(), []).append(r)
    labels = {(ts, rg): pd.read_csv(f"data/processed/{ts}_regime_{rg.lower()}.csv") for ts, rg in TESTS}
    rows = []
    for name, rs in results.items():
        cfg = V2Cfg(**rs[0]["cfg"])
        rs.sort(key=lambda r: r["seed"])
        for (ts, rg), df in labels.items():
            y = df["label"].to_numpy()
            plist = [r["preds"][(ts, rg)] for r in rs]
            for r, p in zip(rs, plist):
                rows.append(_row(cfg, ts, rg, r["seed"], -1, r["epoch"], r["n_epochs"], r["secs"], 0.5, y, p, "secondary"))
            pm = np.mean(plist, axis=0)
            d = {"sequence": df["sequence"], "y_true": y, "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)}
            for r, p in zip(rs, plist):
                d[f"prob_seed{r['seed']}"] = p
            pd.DataFrame(d).to_csv(PRED / f"{name}_{ts}_{rg}.csv", index=False)
    if rows:
        append(pd.DataFrame(rows), FINAL_FILE)
    mark("B_final", "complete", t.elapsed(), f"{len(results)} models x {len(SEEDS)} seeds")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("cv", "all"):
        run_cv()
    if what in ("select", "all"):
        print(json.dumps(select(), indent=1))
    if what in ("final", "all"):
        run_final()
