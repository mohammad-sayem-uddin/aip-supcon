"""Stage orchestration for S7-S10: sweeps, best-hyperparameter selection, final models, statistics.

Usage: python -m src.pipeline s7 | s8 | s9 | s10 | configs
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import numpy as np
import pandas as pd

from src.embed import CHECKPOINTS, EMB_DIR
from src.evaluate import (METRIC_NAMES, bootstrap_ci, compare_models, compute_metrics, find_optimal_threshold,
                          mcc_from_counts, _confusion)
from src.train import (RESULT_COLUMNS, RESULTS, Config, append_results, cross_validate, latents, load_benchmark,
                       load_test, predict_bundle, train_final)
from src.utils import ProgressLogger, Timer, append_note, mark_stage, setup_logging

log = setup_logging("pipeline")

LAMBDAS = [0.0, 0.1, 0.25, 0.5, 1.0, 2.0]
TAUS = [0.05, 0.07, 0.1, 0.5]
SEEDS = (0, 1, 2, 3, 4)
HEADLINE = "esm2_t6_8M"
TEST_SETS = ("ind_425", "ind_1049")
REGIMES = ("A", "B", "C")
N_JOBS = 6


def make_cfg(ckpt: str, lam: float, tau: float = 0.07) -> Config:
    return Config(name=f"{ckpt}_lam{lam:g}_tau{tau:g}", checkpoint=ckpt, lambda_supcon=lam, temperature=tau)


def available_checkpoints() -> list[str]:
    return [c for c in CHECKPOINTS if (EMB_DIR / f"{c}_all.npy").exists()]


def write_configs() -> int:
    d = RESULTS.parent / "configs"
    d.mkdir(exist_ok=True)
    n = 0
    for ck in CHECKPOINTS:
        for lam in LAMBDAS:
            make_cfg(ck, lam).to_yaml(d / f"{ck}_lam{lam:g}_tau0.07.yaml")
            n += 1
        for tau in TAUS:
            if tau != 0.07:
                make_cfg(ck, 0.5, tau).to_yaml(d / f"{ck}_lam0.5_tau{tau:g}.yaml")
                n += 1
    return n


def cv_table() -> pd.DataFrame:
    return pd.read_csv(RESULTS / "cv_results.csv")


def best_lambda(ckpt: str, tau: float = 0.07) -> tuple[float, pd.DataFrame]:
    """Lambda > 0 with the highest mean CV MCC (over seeds x folds) at this checkpoint and temperature."""
    df = cv_table()
    df = df[(df["checkpoint"] == ckpt) & (df["temperature"] == tau) & (df["family"] == "deep")]
    g = df.groupby("lambda_supcon")["mcc"].agg(["mean", "std", "count"])
    pos = g[g.index > 0]
    return float(pos["mean"].idxmax()), g


def best_tau(ckpt: str, lam: float) -> tuple[float, pd.DataFrame]:
    df = cv_table()
    df = df[(df["checkpoint"] == ckpt) & (df["lambda_supcon"] == lam) & (df["family"] == "deep")]
    g = df.groupby("temperature")["mcc"].agg(["mean", "std", "count"])
    return float(g["mean"].idxmax()), g


def run_lambda_sweep(ckpt: str) -> None:
    prog = ProgressLogger(len(LAMBDAS), f"lambda sweep {ckpt}", log)
    for lam in LAMBDAS:
        cross_validate(config=make_cfg(ckpt, lam), seeds=SEEDS, n_jobs=N_JOBS)
        prog.step()


def run_tau_sweep(ckpt: str) -> float:
    lam, _ = best_lambda(ckpt)
    for tau in TAUS:
        cross_validate(config=make_cfg(ckpt, lam, tau), seeds=SEEDS, n_jobs=N_JOBS)
    return lam


def s7() -> int:
    t = Timer()
    write_configs()
    run_lambda_sweep(HEADLINE)
    lam, g = best_lambda(HEADLINE)
    log.info("S7 best lambda at %s = %g\n%s", HEADLINE, lam, g.round(4))
    mark_stage("S7", "complete", t.elapsed(), f"lambda sweep on {HEADLINE}; best lambda>0 = {lam:g} by mean CV MCC")
    return 0


def s8(only: list[str] | None = None) -> int:
    t = Timer()
    failed = []
    for ck in (only or CHECKPOINTS):
        if ck not in available_checkpoints():
            failed.append(ck)
            append_note("BLOCKERS.md", f"S8 {ck}: no embeddings",
                        f"embeddings/{ck}_all.npy is missing, so the lambda/temperature sweeps for {ck} were not run. "
                        f"Run `python -m src.embed --checkpoint {ck} --purge-model` (needs a free-disk margin or a "
                        f"GPU/Kaggle machine) then `python -m src.pipeline s8`.")
            continue
        try:
            run_lambda_sweep(ck)
            lam = run_tau_sweep(ck)
            tau, g = best_tau(ck, lam)
            log.info("S8 %s: best lambda %g, best tau %g\n%s", ck, lam, tau, g.round(4))
        except Exception:
            import traceback
            failed.append(ck)
            append_note("BLOCKERS.md", f"S8 {ck} failed", "```\n" + traceback.format_exc() + "\n```")
            log.exception("S8 %s failed", ck)
    if only is None:
        mark_stage("S8", "partial" if failed else "complete", t.elapsed(),
                   "lambda + temperature sweeps; missing/failed: " + (", ".join(failed) or "none"))
    return 0


# ------------------------------------------------------------------ S9


def final_configs(ckpt: str) -> list[Config]:
    """Models to evaluate on the independent sets for one checkpoint."""
    lam, _ = best_lambda(ckpt)
    tau, _ = best_tau(ckpt, lam)
    cfgs = [make_cfg(ckpt, 0.0), make_cfg(ckpt, lam, tau)]
    if ckpt == HEADLINE:
        cfgs += [make_cfg(ckpt, l) for l in LAMBDAS if l not in (0.0, lam)]
    out, seen = [], set()
    for c in cfgs:
        if c.model_name() not in seen:
            seen.add(c.model_name())
            out.append(c)
    return out


def s9() -> int:
    t = Timer()
    from src.train import _result_row
    rows, rows_tuned, failed = [], [], []
    (RESULTS / "predictions").mkdir(exist_ok=True)
    (RESULTS / "latents").mkdir(exist_ok=True)
    sel_file = RESULTS / "selected_models.json"
    selected = json.loads(sel_file.read_text()) if sel_file.exists() else {}
    done_models = set(pd.read_csv(RESULTS / "final_results.csv", usecols=["model"])["model"]) \
        if (RESULTS / "final_results.csv").exists() else set()
    for ck in available_checkpoints():
        try:
            cfgs = final_configs(ck)
        except Exception:
            import traceback
            failed.append(ck)
            append_note("BLOCKERS.md", f"S9 {ck}: cannot select final configs", "```\n" + traceback.format_exc() + "\n```")
            continue
        X, y, _ = load_benchmark(ck)
        tests = {(ts, rg): load_test(ck, ts, rg) for ts in TEST_SETS for rg in REGIMES}
        for i, cfg in enumerate(cfgs):
            if cfg.model_name() in done_models:
                log.info("S9 skip %s (already in final_results.csv)", cfg.model_name())
                continue
            role = "baseline" if cfg.lambda_supcon == 0 else ("best" if i == 1 else "sweep")
            selected[cfg.model_name()] = {"checkpoint": ck, "lambda": cfg.lambda_supcon, "tau": cfg.temperature,
                                          "role": role}
            ens: dict[tuple, list] = {k: [] for k in tests}
            for seed in SEEDS:
                b = train_final(X, y, cfg, seed=seed)
                for (ts, rg), (Xt, yt, st) in tests.items():
                    p = predict_bundle(b, Xt)
                    ens[(ts, rg)].append(p)
                    rows.append(_result_row(cfg, cfg.model_name(), "deep", ts, rg, seed, -1, b["best_epoch"],
                                            len(b["history"]), b["train_seconds"], 0.5, yt, p))
                    rows_tuned.append(_result_row(cfg, cfg.model_name(), "deep_tuned", ts, rg, seed, -1,
                                                  b["best_epoch"], len(b["history"]), b["train_seconds"],
                                                  b["threshold"], yt, p))
                if seed == 0:
                    for ts in TEST_SETS:
                        Xt, yt, _ = tests[(ts, "B")]
                        lat = latents(b, Xt)
                        np.savez_compressed(RESULTS / "latents" / f"{cfg.model_name()}_seed0_{ts}_B.npz",
                                            y=yt, raw=Xt, **lat)
            for (ts, rg), plist in ens.items():
                Xt, yt, st = tests[(ts, rg)]
                pm = np.mean(plist, axis=0)
                d = {"sequence": st, "y_true": yt, "y_prob": pm, "y_pred": (pm >= 0.5).astype(int)}
                for i, p in enumerate(plist):
                    d[f"prob_seed{SEEDS[i]}"] = p
                pd.DataFrame(d).to_csv(RESULTS / "predictions" / f"{cfg.model_name()}_{ts}_{rg}.csv", index=False)
            log.info("S9 done %s", cfg.model_name())
    if rows:
        append_results(pd.DataFrame(rows)[RESULT_COLUMNS], RESULTS / "final_results.csv")
        append_results(pd.DataFrame(rows_tuned)[RESULT_COLUMNS], RESULTS / "final_results_tuned.csv")
    sel_file.write_text(json.dumps(selected, indent=2))
    missing = [c for c in CHECKPOINTS if c not in {d["checkpoint"] for d in selected.values()}]
    mark_stage("S9", "partial" if (failed or missing) else "complete", t.elapsed(),
               f"final models for {len(selected)} configs; checkpoints without final models: {missing or 'none'}")
    return 0


# ----------------------------------------------------------------- S10


def s10() -> int:
    t = Timer()
    sel = json.loads((RESULTS / "selected_models.json").read_text())
    by_ck: dict[str, list[str]] = {}
    for name, d in sel.items():
        by_ck.setdefault(d["checkpoint"], []).append(name)
    rows, per_seed, cis = [], [], []
    from sklearn.metrics import roc_auc_score
    for ck, names in by_ck.items():
        base = next(n for n in names if sel[n]["lambda"] == 0.0)
        for n in names:
            if n == base:
                continue
            for ts in TEST_SETS:
                for rg in REGIMES:
                    r = compare_models(n, base, ts, rg)
                    r["checkpoint"], r["lambda"], r["tau"] = ck, sel[n]["lambda"], sel[n]["tau"]
                    rows.append(r)
                    # per-seed paired comparison
                    from src.evaluate import delong_test, load_predictions
                    a, b = load_predictions(n, ts, rg), load_predictions(base, ts, rg)
                    for s in SEEDS:
                        pa, pb, y = a[f"prob_seed{s}"].to_numpy(), b[f"prob_seed{s}"].to_numpy(), a["y_true"].to_numpy()
                        z, p = delong_test(y, pa, pb)
                        ma = mcc_from_counts(*_confusion(y, (pa >= .5).astype(int)))
                        mb = mcc_from_counts(*_confusion(y, (pb >= .5).astype(int)))
                        per_seed.append({"checkpoint": ck, "model": n, "baseline": base, "test_set": ts, "regime": rg,
                                         "seed": s, "mcc_diff": ma - mb,
                                         "auroc_diff": roc_auc_score(y, pa) - roc_auc_score(y, pb), "delong_p": p})
        from src.evaluate import load_predictions
        for n in names:
            for ts in TEST_SETS:
                for rg in REGIMES:
                    d = load_predictions(n, ts, rg)
                    y, p = d["y_true"].to_numpy(), d["y_prob"].to_numpy()
                    lo_a, hi_a = bootstrap_ci(y, p, lambda yt, yp: roc_auc_score(yt, yp))
                    lo_m, hi_m = bootstrap_ci(y, p, lambda yt, yp: mcc_from_counts(*_confusion(yt, (yp >= .5).astype(int))))
                    m = compute_metrics(y, (p >= .5).astype(int), p)
                    cis.append({"model": n, "checkpoint": ck, "test_set": ts, "regime": rg, "n": len(y),
                                "auroc": m["auroc"], "auroc_lo": lo_a, "auroc_hi": hi_a,
                                "mcc": m["mcc"], "mcc_lo": lo_m, "mcc_hi": hi_m})
    pd.DataFrame(rows).to_csv(RESULTS / "stats_tests.csv", index=False)
    pd.DataFrame(per_seed).to_csv(RESULTS / "stats_per_seed.csv", index=False)
    pd.DataFrame(cis).to_csv(RESULTS / "bootstrap_cis.csv", index=False)
    mark_stage("S10", "complete", t.elapsed(), "DeLong, McNemar, bootstrap CIs written")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["configs", "s7", "s8", "s9", "s10"])
    ap.add_argument("--only", nargs="+", help="s8 only: run just these checkpoints (does not mark the stage)")
    a = ap.parse_args()
    sys.exit({"configs": lambda: print(write_configs()) or 0, "s7": s7, "s8": lambda: s8(a.only), "s9": s9,
              "s10": s10}[a.stage]())
