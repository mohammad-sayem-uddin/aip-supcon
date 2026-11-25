"""Phase E: all secondary comparisons, Benjamini-Hochberg correction, minimum detectable effects, seed-vs-sample variance.

Reads v1 + v2 prediction files; writes results/v2/comparisons_raw.csv, results/tables/T5.11_corrected_significance.csv,
results/tables/T5.11b_seed_vs_sample_variance.csv and POWER_ANALYSIS.md.   Run: python -m src.v2.phaseE
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.evaluate import _confusion, mcc_from_counts
from src.utils import ROOT, Timer, setup_logging
from src.v2.common import R, TABLES, V2, mark
from src.v2.stats import bh_adjust, cohens_dz, compare_files

log = setup_logging("phaseE")
V1P, V2P = R / "predictions", V2 / "predictions"
TESTS = ("ind_425", "ind_1049")
REGIMES = ("A", "B", "C")


def pp(stem: str, ts: str, rg: str) -> Path | None:
    for d in (V2P, V1P):
        p = d / f"{stem}_{ts}_{rg}.csv"
        if p.exists():
            return p
    return None


def pair(family: str, label: str, a: str, b: str, tier: str, regimes=("B",), note: str = "") -> list[dict]:
    rows = []
    for ts in TESTS:
        for rg in regimes:
            pa, pb = pp(a, ts, rg), pp(b, ts, rg)
            if pa is None or pb is None:
                continue
            r = compare_files(pa, pb)
            r.update({"family": family, "comparison": label, "model_a": a, "model_b": b, "test_set": ts, "regime": rg,
                      "analysis_tier": tier, "note": note})
            rows.append(r)
    return rows


def collect() -> pd.DataFrame:
    rows: list[dict] = []
    # --- H1 (v1 headline, 8M MLP, tau 0.1) -- the preregistered primary test
    rows += pair("H1 primary (v1)", "8M MLP: lambda=2,tau=0.1 vs lambda=0", "esm2_t6_8M_lam2_tau0.1", "esm2_t6_8M_lam0_tau0.07", "primary",
                 note="decided in v1; recomputed here with the v2 comparison code")
    # --- B1 reference at tau=0.07 and other checkpoints (v1 models)
    sel1 = json.loads((R / "selected_models.json").read_text())
    for n, d in sel1.items():
        if d["role"] == "best" and d["checkpoint"] != "esm2_t6_8M":
            base = next(m for m, e in sel1.items() if e["checkpoint"] == d["checkpoint"] and e["role"] == "baseline")
            rows += pair("lambda contrast: checkpoints (v1)", f"{d['checkpoint']} lambda*={d['lambda']:g}", n, base, "exploratory", REGIMES)
    rows += pair("lambda contrast: Phase B", "B1_mlp (v1 MLP, tau 0.07) lambda=2 vs 0", "esm2_t6_8M_lam2_tau0.07", "esm2_t6_8M_lam0_tau0.07", "secondary",
                 ("A", "B", "C"), "B1 reuses v1 final models")
    # --- H2: Phase B architectures
    sel = json.loads((V2 / "selected_v2.json").read_text()) if (V2 / "selected_v2.json").exists() else {}
    for a, d in sel.items():
        lam = d["lambda_star"]
        for rg in REGIMES:
            fam = "H2 architectures (Regime B)" if rg == "B" else "lambda contrast: Phase B other regimes"
            tier = "secondary" if rg == "B" else "exploratory"
            rows += pair(fam, f"{a} lambda*={lam:g} vs 0", f"{a}_esm2_t6_8M_lam{lam:g}_tau0.07", f"{a}_esm2_t6_8M_lam0_tau0.07", tier, (rg,))
    # --- representation comparisons (Regime B)
    ref = "esm650_mean__mlp"
    for p in ("max", "meanmax", "cls", "firstlast"):
        rows += pair("representation: pooling (C1)", f"650M {p} vs mean pooling (MLP)", f"esm650_{p}__mlp", ref, "exploratory")
    rows += pair("representation: pooling (C1)", "650M attention vs mean pooling (MLP)", "esm650_attention__attn_mlp", ref, "exploratory")
    for clf in ("rf", "lgbm", "mlp"):
        for short in ("esm650", "esm8"):
            f, e = f"{short}_fusion__{clf}", f"{short}_mean__{clf}"
            rows += pair("representation: fusion (C2)", f"{short} fusion vs ESM-only ({clf})", f, e, "exploratory")
            rows += pair("representation: fusion (C2)", f"{short} fusion vs hand-crafted only ({clf})", f, f"hand__{clf}", "exploratory")
            rows += pair("representation: fusion (C2)", f"{short} fusion ({clf}) vs AAC+RF (v1 baseline)", f, "AAC_RF", "exploratory")
    rows += pair("representation: fine-tuning (C3)", "ESM-2 8M fine-tuned vs frozen (same head)", "esm2_t6_8M_finetune", "esm2_t6_8M_frozen", "exploratory")
    rows += pair("representation: ESM vs composition", "650M MLP lambda=0 vs AAC+RF", "esm2_t33_650M_lam0_tau0.07", "AAC_RF", "exploratory")
    rows += pair("representation: ESM vs composition", "8M MLP lambda=0 vs AAC+RF", "esm2_t6_8M_lam0_tau0.07", "AAC_RF", "exploratory")
    return pd.DataFrame(rows)


def correct(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["p_delong_bh_family"] = np.nan
    df["p_mcnemar_bh_family"] = np.nan
    for fam, idx in df.groupby("family").groups.items():
        df.loc[idx, "p_delong_bh_family"] = bh_adjust(df.loc[idx, "delong_p"].to_numpy())
        df.loc[idx, "p_mcnemar_bh_family"] = bh_adjust(df.loc[idx, "mcnemar_p"].to_numpy())
    reg_b = df["regime"] == "B"  # only Regime B tests can support claims
    df["p_delong_bh_global_all"] = bh_adjust(df["delong_p"].to_numpy())
    df["p_mcnemar_bh_global_all"] = bh_adjust(df["mcnemar_p"].to_numpy())
    df["p_delong_bh_global_regimeB"] = np.nan
    df.loc[reg_b, "p_delong_bh_global_regimeB"] = bh_adjust(df.loc[reg_b, "delong_p"].to_numpy())
    df["supports_claim_rule"] = (df["p_delong_bh_family"] < 0.05) & (df["mcc_diff_lo"] > 0) & reg_b
    df["significant_raw_delong_0.05"] = df["delong_p"] < 0.05
    df["significant_after_family_BH"] = df["p_delong_bh_family"] < 0.05
    df["significant_after_global_BH"] = df["p_delong_bh_global_all"] < 0.05
    return df


def seed_vs_sample(df: pd.DataFrame) -> pd.DataFrame:
    """Per-seed paired differences vs the bootstrap SE of the ensemble difference, for lambda contrasts with prob_seed columns."""
    rows = []
    for _, r in df[df["comparison"].str.contains("lambda|vs 0", regex=True)].iterrows():
        pa, pb = pp(r["model_a"], r["test_set"], r["regime"]), pp(r["model_b"], r["test_set"], r["regime"])
        a, b = pd.read_csv(pa), pd.read_csv(pb)
        cols = [c for c in a.columns if c.startswith("prob_seed") and c in b.columns]
        if not cols:
            continue
        y = a["y_true"].to_numpy()
        dm = [mcc_from_counts(*_confusion(y, (a[c] >= .5).astype(int))) - mcc_from_counts(*_confusion(y, (b[c] >= .5).astype(int))) for c in cols]
        da = [roc_auc_score(y, a[c]) - roc_auc_score(y, b[c]) for c in cols]
        rows.append({"family": r["family"], "comparison": r["comparison"], "test_set": r["test_set"], "regime": r["regime"],
                     "n_seeds": len(cols), "mean_seed_mcc_diff": np.mean(dm), "sd_across_seeds_mcc_diff": np.std(dm, ddof=1),
                     "n_seeds_mcc_positive": int(np.sum(np.array(dm) > 0)), "mean_seed_auroc_diff": np.mean(da),
                     "sd_across_seeds_auroc_diff": np.std(da, ddof=1), "bootstrap_se_mcc_diff_ensemble": r["mcc_diff_se"],
                     "bootstrap_se_auroc_diff_ensemble": r["auroc_diff_se"], "ensemble_mcc_diff": r["mcc_diff"]})
    return pd.DataFrame(rows)


def cv_effect_sizes() -> pd.DataFrame:
    """Cohen's d_z of the paired (same seed, same fold) CV MCC difference, lambda* vs 0, per architecture (8M)."""
    rows = []
    v1 = pd.read_csv(R / "cv_results.csv")
    v1 = v1[(v1.family == "deep") & (v1.checkpoint == "esm2_t6_8M") & (v1.temperature == 0.07)]
    def add(name, a, b):
        m = a.merge(b, on=["seed", "fold"], suffixes=("_a", "_b"))
        d = (m["mcc_a"] - m["mcc_b"]).to_numpy()
        rows.append({"comparison": name, "n_pairs": len(d), "mean_cv_mcc_diff": d.mean(), "sd": d.std(ddof=1), "cohens_dz": cohens_dz(d),
                     "ci95_lo": d.mean() - 1.96 * d.std(ddof=1) / np.sqrt(len(d)), "ci95_hi": d.mean() + 1.96 * d.std(ddof=1) / np.sqrt(len(d))})
    for lam in (0.1, 0.25, 0.5, 1.0, 2.0):
        add(f"B1_mlp lambda={lam:g} vs 0 (v1 CV, tau 0.07)", v1[v1.lambda_supcon == lam], v1[v1.lambda_supcon == 0.0])
    if (V2 / "cv_results_v2.csv").exists():
        cv = pd.read_csv(V2 / "cv_results_v2.csv")
        for a, g in cv.groupby("arch"):
            base = g[g.lambda_supcon == 0.0]
            for lam in sorted(g.lambda_supcon.unique()):
                if lam > 0:
                    add(f"{a} lambda={lam:g} vs 0 (CV)", g[g.lambda_supcon == lam], base)
    out = pd.DataFrame(rows)
    out["note"] = "CV rows: same seed and fold; the 25 pairs overlap in training data, so the CI is optimistic (correlated folds)"
    return out


def power_md(df: pd.DataFrame) -> str:
    sub = df[df["comparison"].str.contains("vs 0|lambda=2,tau")].copy()
    g = sub.groupby(["test_set", "regime"]).agg(n=("n", "first"), mde_mcc_median=("mcc_mde80", "median"), mde_mcc_min=("mcc_mde80", "min"),
                                              mde_mcc_max=("mcc_mde80", "max"), mde_auroc_median=("auroc_mde80", "median"),
                                              n_comparisons=("n", "size")).reset_index()
    lines = ["# POWER ANALYSIS", "",
             "Minimum detectable effect (MDE) at 80% power, two-sided alpha = 0.05, for the paired lambda>0 vs lambda=0 comparisons "
             "actually run. MDE = (1.96 + 0.84) x SE, where SE is the standard deviation of the paired stratified bootstrap "
             "distribution (2,000 resamples) of the difference. It applies to *paired* comparisons of two models scored on the same "
             "sequences, which is what every test here is; an unpaired comparison would need a larger difference.", "",
             "| test set | regime | n | comparisons | MDE MCC (median [min, max]) | MDE AUROC (median) |", "|---|---|---|---|---|---|"]
    for _, r in g.iterrows():
        lines.append(f"| {r.test_set} | {r.regime} | {int(r.n)} | {int(r.n_comparisons)} | {r.mde_mcc_median:.3f} [{r.mde_mcc_min:.3f}, {r.mde_mcc_max:.3f}] | {r.mde_auroc_median:.3f} |")
    b = g[g.regime == "B"]
    lines += ["", "## How to read a non-significant result", "",
              "A non-significant paired difference means: *no effect larger than the MDE in the table was detectable at this sample size*. "
              "It is not evidence that the two models are equivalent. "]
    for _, r in b.iterrows():
        lines.append(f"- {r.test_set} (Regime B, n = {int(r.n)}): effects below about {r.mde_mcc_median:.2f} MCC / {r.mde_auroc_median:.3f} AUROC cannot be ruled out.")
    lines += ["", "Differences of the size seen between lambda settings in cross-validation (0.005-0.01 MCC) are an order of magnitude below these "
              "MDEs, so the independent test sets cannot confirm or refute effects of that size; the 5 x 5 cross-validation (25 paired runs on "
              "3,716 sequences) is the better-powered, but optimistic, view (see T5.11c)."]
    return "\n".join(lines) + "\n"


def run() -> int:
    t = Timer()
    df = collect()
    df.to_csv(V2 / "comparisons_raw.csv", index=False)
    out = correct(df)
    cols = ["family", "comparison", "analysis_tier", "test_set", "regime", "n", "mcc_a", "mcc_b", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi",
            "mcc_mde80", "auroc_a", "auroc_b", "auroc_diff", "auroc_diff_lo", "auroc_diff_hi", "auroc_mde80", "delong_p", "p_delong_bh_family",
            "p_delong_bh_global_all", "mcnemar_p", "p_mcnemar_bh_family", "p_mcnemar_bh_global_all", "significant_raw_delong_0.05",
            "significant_after_family_BH", "significant_after_global_BH", "supports_claim_rule", "model_a", "model_b", "note"]
    out[cols].round(5).to_csv(TABLES / "T5.11_corrected_significance.csv", index=False)
    seed_vs_sample(out).round(5).to_csv(TABLES / "T5.11b_seed_vs_sample_variance.csv", index=False)
    cv_effect_sizes().round(5).to_csv(TABLES / "T5.11c_cv_effect_sizes.csv", index=False)
    (ROOT / "POWER_ANALYSIS.md").write_text(power_md(out))
    log.info("Phase E: %d comparisons; raw sig %d; family-BH sig %d; global-BH sig %d", len(out), int(out["significant_raw_delong_0.05"].sum()),
             int(out["significant_after_family_BH"].sum()), int(out["significant_after_global_BH"].sum()))
    mark("E_stats", "complete", t.elapsed(), f"{len(out)} comparisons")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
