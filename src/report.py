"""Regenerate HANDOFF_REPORT.md from stage markers and result files (safe to run at any point)."""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

from src.utils import ROOT

R = ROOT / "results"
STAGES = [
    ("S1", "Data pipeline, audit, regimes A/B + hard gate"),
    ("S2", "Sequence-identity screen, Regime C"),
    ("S3", "ESM-2 embeddings (8M, 35M, 150M, 650M)"),
    ("S4", "AIPNet + SupConLoss + unit tests"),
    ("S5", "Training loop + trial runs (lambda=0, 0.5)"),
    ("S6", "Classical + ESM-LR baselines"),
    ("S7", "Lambda sweep on 8M (6 lambdas x 5 seeds x 5 folds)"),
    ("S8", "Other checkpoints: lambda + temperature sweeps"),
    ("S9", "Final models, all regimes, both test sets"),
    ("S10", "DeLong, McNemar, bootstrap CIs"),
    ("S11", "Tables and figures"),
    ("S12", "Honest interpretation"),
]


def md(df: pd.DataFrame) -> str:
    if df is None or len(df) == 0:
        return "_(none)_\n"
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join("" if (isinstance(v, float) and np.isnan(v)) else str(v) for v in r) + " |")
    return "\n".join(out) + "\n"


def _stage_info(name: str) -> tuple[str, float, str]:
    if name == "S3":
        parts = sorted((R / ".stages").glob("S3_*.json"))
        if not parts:
            return "skipped", 0.0, "not reached"
        infos = [json.loads(p.read_text()) for p in parts]
        done = [i for i in infos if i["status"] == "complete"]
        status = "complete" if len(done) == 4 else ("partial" if done else "failed")
        return status, sum(i["wall_seconds"] for i in infos), "; ".join(f"{i['stage'][3:]}: {i['status']}" for i in infos)
    f = R / ".stages" / f"{name}.json"
    if not f.exists():
        return "skipped", 0.0, "not reached"
    d = json.loads(f.read_text())
    return d["status"], d["wall_seconds"], d.get("notes", "")


def _fmt_secs(s: float) -> str:
    return f"{s:.1f}s" if s < 120 else f"{s / 60:.1f} min"


def section_status() -> str:
    rows = []
    for k, desc in STAGES:
        st, secs, notes = _stage_info(k)
        rows.append({"Stage": k, "What": desc, "Status": st, "Compute wall-clock": _fmt_secs(secs) if secs else "-",
                     "Notes": notes})
    return ("Wall-clock is compute time recorded by the stage runners (it excludes code-writing time).\n\n"
            + md(pd.DataFrame(rows)))


def section_s1() -> str:
    f = R / "s1_verification.csv"
    if not f.exists():
        return "_S1 has not run._\n"
    df = pd.read_csv(f)
    verdict = "**PASSED: all numbers match exactly.**" if df["match"].all() else "**FAILED: see BLOCKERS.md.**"
    return verdict + "\n\n" + md(df)


def _sig_text(p: float) -> str:
    return "statistically significant (p < 0.05)" if p < 0.05 else "NOT statistically significant (p >= 0.05)"


def section_headline() -> str:
    f = R / "stats_tests.csv"
    out = []
    cvf = R / "cv_results.csv"
    if cvf.exists():
        cv = pd.read_csv(cvf)
        cv = cv[(cv["family"] == "deep") & (cv["checkpoint"] == "esm2_t6_8M") & (cv["temperature"] == 0.07)]
        g = cv.groupby("lambda_supcon")[["mcc", "auroc"]].agg(["mean", "std"]).round(4)
        g.columns = ["mcc_mean", "mcc_std", "auroc_mean", "auroc_std"]
        out.append("**5-fold CV, 8M checkpoint, tau=0.07 (mean/std over seeds x folds):**\n\n" + md(g.reset_index()))
    if not f.exists():
        out.append("_Final models / statistical tests (S9-S10) have not run yet._\n")
        return "\n".join(out)
    st = pd.read_csv(f)
    sel = json.loads((R / "selected_models.json").read_text())
    best_names = [n for n, d in sel.items() if d["checkpoint"] == "esm2_t6_8M" and d.get("role") == "best"]
    head = st[(st["model_a"].isin(best_names)) & (st["regime"] == "B")]
    cols = ["test_set", "lambda", "tau", "n", "mcc_a", "mcc_b", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi",
            "auroc_a", "auroc_b", "auroc_diff", "auroc_diff_lo", "auroc_diff_hi", "delong_p", "mcnemar_p"]
    out.append("**Regime B (leakage-free), 8M checkpoint, CV-selected lambda>0 minus lambda=0 (seed-ensemble "
               "predictions; 95% paired stratified bootstrap CIs, 2000 resamples):**\n\n" + md(head[cols].round(4)))
    lines = []
    for _, r in head.iterrows():
        lines.append(f"- {r['test_set']} (lambda={r['lambda']:g}, tau={r['tau']:g}): MCC difference {r['mcc_diff']:+.4f} "
                     f"[{r['mcc_diff_lo']:+.4f}, {r['mcc_diff_hi']:+.4f}], AUROC difference {r['auroc_diff']:+.4f} "
                     f"[{r['auroc_diff_lo']:+.4f}, {r['auroc_diff_hi']:+.4f}]; DeLong p = {r['delong_p']:.4g} "
                     f"({_sig_text(r['delong_p'])}); McNemar p = {r['mcnemar_p']:.4g} ({_sig_text(r['mcnemar_p'])}).")
    out.append("**Verdict (CV-selected lambda>0 model vs lambda=0):**\n\n" + "\n".join(lines) + "\n")
    out.append("The full interpretation, including consistency across checkpoints and regimes, is in "
               "[INTERPRETATION.md](INTERPRETATION.md).\n")
    return "\n".join(out)


def section_leakage() -> str:
    frames = []
    for f in ("baseline_results.csv", "final_results.csv"):
        p = R / f
        if p.exists():
            frames.append(pd.read_csv(p))
    if not frames:
        return "_No independent-set results yet._\n"
    df = pd.concat(frames)
    df = df[df["eval_set"].isin(["ind_425", "ind_1049"])]
    if df.empty:
        return "_No independent-set results yet._\n"
    g = df.groupby(["model", "eval_set", "regime"])[["mcc", "auroc"]].mean().unstack("regime")
    g.columns = [f"{m}_{r}" for m, r in g.columns]
    g = g.reset_index()
    for m in ("mcc", "auroc"):
        if f"{m}_A" in g and f"{m}_B" in g:
            g[f"{m}_gap_A-B"] = g[f"{m}_A"] - g[f"{m}_B"]
    return ("Mean over 5 seeds of each model's per-seed metrics (threshold 0.5). Gap = Regime A minus Regime B.\n\n"
            + md(g.round(4)))


FILE_DESC = {
    "data_audit.csv": "Tidy dataset audit and cross-set overlap table (Table 3.1/3.2)",
    "s1_verification.csv": "S1 hard-gate expected vs actual",
    "identity_screen.csv": "Sequences removed per identity threshold (0.8/0.9/0.95/1.0 and exact)",
    "embedding_timings.csv": "ESM-2 embedding wall-clock, device, peak memory per checkpoint",
    "cv_results.csv": "Deep model CV rows: one row per (config, seed, fold), all 8 metrics",
    "baseline_results.csv": "Baselines 1-4: CV rows and independent-set rows (Regimes A/B/C)",
    "final_results.csv": "Deep final models, per seed, independent sets x regimes, threshold 0.5",
    "final_results_tuned.csv": "Same, threshold tuned on a 10% hold-out of the training data",
    "selected_models.json": "Which (lambda, tau) was selected per checkpoint by CV",
    "stats_tests.csv": "DeLong, McNemar and paired-bootstrap CIs, lambda>0 vs lambda=0",
    "stats_per_seed.csv": "Per-seed paired differences and DeLong p-values",
    "bootstrap_cis.csv": "95% bootstrap CIs for AUROC and MCC of every final model",
}


def section_files() -> str:
    rows = []
    for f, d in FILE_DESC.items():
        p = R / f
        if p.exists():
            n = len(pd.read_csv(p)) if f.endswith(".csv") else "-"
            rows.append({"File": f"results/{f}", "Rows": n, "Contents": d})
    for sub, d in (("tables", "Thesis tables as CSV + LaTeX"), ("predictions", "Per-sample predictions"),
                   ("latents", "Latent vectors for t-SNE"), ("models", "Final model weights + scalers")):
        p = R / sub
        if p.exists():
            rows.append({"File": f"results/{sub}/", "Rows": len(list(p.glob('*'))), "Contents": d})
    return md(pd.DataFrame(rows))


def section_figures() -> str:
    fig = ROOT / "figures"
    files = sorted(p.name for p in fig.glob("*") if p.suffix in (".pdf", ".png")) if fig.exists() else []
    status = R / "figure_status.json"
    s = json.loads(status.read_text()) if status.exists() else {}
    out = ""
    if s:
        out += md(pd.DataFrame([{"Figure": k, "Status": v} for k, v in s.items()])) + "\n"
    out += "Files in figures/: " + (", ".join(files) if files else "none yet") + "\n"
    return out


def section_notes(name: str, fallback: str) -> str:
    p = R / "report_notes" / name
    return p.read_text() if p.exists() else fallback


def build() -> str:
    parts = [
        f"# HANDOFF REPORT\n\n_Generated {datetime.now().isoformat(timespec='seconds')} by `python -m src.report`; "
        "rebuilt after every stage._\n",
        "## 1. STATUS\n\n" + section_status(),
        "## 2. S1 VERIFICATION\n\n" + section_s1(),
        "## 3. HEADLINE RESULT\n\n" + section_headline(),
        "## 4. LEAKAGE IMPACT\n\n" + section_leakage(),
        "## 5. FULL RESULTS\n\n" + section_files(),
        "## 6. FIGURES\n\n" + section_figures(),
        "## 7. BLOCKERS\n\n" + ((ROOT / "BLOCKERS.md").read_text().split("\n", 1)[1] if (ROOT / "BLOCKERS.md").exists() else "_none_"),
        "## 8. DECISIONS\n\n" + ((ROOT / "DECISIONS.md").read_text().split("\n", 1)[1] if (ROOT / "DECISIONS.md").exists() else "_none_"),
        "## 9. NEXT ACTIONS\n\n" + section_notes("next_actions.md", "_To be written at the end of the run._\n"),
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    (ROOT / "HANDOFF_REPORT.md").write_text(build())
    print("wrote HANDOFF_REPORT.md")
