"""Completion run 2.2: scale axis of fine-tuning (ESM-2 8M, 150M, 650M), merged from the Kaggle outputs.

Inputs (copied from the Kaggle kernel outputs into results/v2/scale/): finetune_scale_<tag>*.csv (CV rows and final-model rows) and
predictions/<tag>_<mode>_<test>_<regime>.csv. The 8M rows come from the earlier run (results/v2/finetune_results_v2.csv, same protocol).
Outputs: results/tables/T5.13a_finetune_scale_cv.csv, T5.13b_finetune_scale_independent.csv, T5.13c_finetune_scale_tests.csv,
T5.11d_global_BH_with_scale.csv (global BH recomputed over the 126 earlier comparisons plus the new ones; T5.11 itself is NOT changed),
figures/fig5_11_finetune_scale.png.   Run: PYTHONPATH=. .venv/bin/python -m src.v2.phase_scale
"""
from __future__ import annotations
import glob, json
from pathlib import Path
import numpy as np, pandas as pd
from src.v2.stats import bh_adjust, compare_files
from src.utils import ROOT

R = ROOT / "results"; V2 = R / "v2"; TAB = R / "tables"; SC = V2 / "scale"
TESTS = ("ind_425", "ind_1049")
TAGS = {"esm2_t6_8M": "8M", "esm2_t30_150M": "150M", "esm2_t33_650M": "650M"}

def load_csv(tag):
    if tag == "esm2_t6_8M": files = [V2 / "finetune_results_v2.csv"]
    else: files = sorted(Path(p) for p in glob.glob(str(SC / f"finetune_scale_{tag}*.csv")))
    if not files: return None
    d = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    d["tag"] = tag; return d.drop_duplicates(subset=["mode", "eval_set", "regime", "seed", "fold"])

def pred_path(tag, mode, ts, rg):
    for d in ([V2 / "predictions"] if tag == "esm2_t6_8M" else [SC / "predictions", V2 / "predictions"]):
        p = d / f"{tag}_{mode}_{ts}_{rg}.csv"
        if p.exists(): return p
    return None

def main():
    SC.mkdir(parents=True, exist_ok=True)
    D = {t: load_csv(t) for t in TAGS}; D = {t: d for t, d in D.items() if d is not None}
    cv_rows, ind_rows = [], []
    for t, d in D.items():
        for mode in ("frozen", "finetune"):
            c = d[(d["mode"] == mode) & (d.eval_set == "cv")]
            if len(c): cv_rows.append({"checkpoint": TAGS[t], "mode": mode, "runs": len(c), "mcc_mean": c.mcc.mean(), "mcc_sd": c.mcc.std(ddof=1), "auroc_mean": c.auroc.mean(), "auroc_sd": c.auroc.std(ddof=1),
                                       "epochs_mean": c.epoch_stopped.mean(), "seconds_per_run_mean": c.train_seconds.mean()})
            for ts in TESTS:
                for rg in "ABC":
                    f = d[(d["mode"] == mode) & (d.eval_set == ts) & (d.regime == rg)]
                    if len(f): ind_rows.append({"checkpoint": TAGS[t], "mode": mode, "test_set": ts, "regime": rg, "seeds": len(f), "mcc_mean": f.mcc.mean(), "mcc_sd": f.mcc.std(ddof=1) if len(f) > 1 else np.nan,
                                                "auroc_mean": f.auroc.mean(), "auroc_sd": f.auroc.std(ddof=1) if len(f) > 1 else np.nan})
    pd.DataFrame(cv_rows).to_csv(TAB / "T5.13a_finetune_scale_cv.csv", index=False); pd.DataFrame(ind_rows).to_csv(TAB / "T5.13b_finetune_scale_independent.csv", index=False)
    print(pd.DataFrame(cv_rows).round(4).to_string())
    # paired comparisons on Regime B (and A, C) ensemble predictions
    ext = {"frozen650_mlp": V2.parent / "predictions" / "esm2_t33_650M_lam0_tau0.07", "mlp150": V2.parent / "predictions" / "esm2_t30_150M_lam0_tau0.07", "aac_rf": V2.parent / "predictions" / "AAC_RF"}
    def P(name, ts, rg):
        if name in ext: p = Path(f"{ext[name]}_{ts}_{rg}.csv"); return p if p.exists() else None
        tag, mode = name.split(":"); return pred_path(tag, mode, ts, rg)
    pairs = [("esm2_t30_150M:finetune", "esm2_t30_150M:frozen", "FT 150M vs frozen control 150M (same head)"), ("esm2_t33_650M:finetune", "esm2_t33_650M:frozen", "FT 650M vs frozen control 650M (same head)"),
             ("esm2_t30_150M:finetune", "esm2_t6_8M:finetune", "FT 150M vs FT 8M"), ("esm2_t33_650M:finetune", "esm2_t6_8M:finetune", "FT 650M vs FT 8M"), ("esm2_t33_650M:finetune", "esm2_t30_150M:finetune", "FT 650M vs FT 150M"),
             ("esm2_t30_150M:finetune", "mlp150", "FT 150M vs frozen 150M MLP (lambda=0)"), ("esm2_t33_650M:finetune", "frozen650_mlp", "FT 650M vs frozen 650M MLP (lambda=0)"),
             ("esm2_t30_150M:finetune", "aac_rf", "FT 150M vs AAC+RF"), ("esm2_t33_650M:finetune", "aac_rf", "FT 650M vs AAC+RF")]
    rows = []
    for a, b, lab in pairs:
        for ts in TESTS:
            for rg in "BAC":
                pa, pb = P(a, ts, rg), P(b, ts, rg)
                if pa is None or pb is None: continue
                r = compare_files(pa, pb); r.update({"comparison": lab, "test_set": ts, "regime": rg, "family": "representation: fine-tuning scale (C3b)", "analysis_tier": "exploratory", "model_a": a, "model_b": b}); rows.append(r)
    if rows:
        T = pd.DataFrame(rows); T["p_delong_bh_family"] = np.nan
        T["p_delong_bh_family"] = bh_adjust(T["delong_p"].to_numpy())  # one family across all regimes and sets of this table
        T.to_csv(TAB / "T5.13c_finetune_scale_tests.csv", index=False)
        old = pd.read_csv(TAB / "T5.11_corrected_significance.csv")
        allp = np.r_[old["delong_p"].to_numpy(), T["delong_p"].to_numpy()]; adj = bh_adjust(allp)
        T["p_delong_bh_global_with_scale"] = adj[len(old):]
        pd.DataFrame({"source": ["T5.11"] * len(old) + ["T5.13c"] * len(T), "delong_p": allp, "p_BH_global_recomputed": adj,
                      "p_BH_global_original": np.r_[old["p_delong_bh_global_all"].to_numpy(), np.full(len(T), np.nan)]}).to_csv(TAB / "T5.11d_global_BH_with_scale.csv", index=False)
        print(T[T.regime == "B"][["comparison", "test_set", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi", "auroc_diff", "delong_p", "p_delong_bh_family"]].round(4).to_string())
    # figure: scale axis
    cv = pd.DataFrame(cv_rows)
    if len(cv):
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
        fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
        order = ["8M", "150M", "650M"]
        mlp = {"8M": json.load(open(ROOT / "results/thesis/ch5_data.json"))["F"]["ft_cv"]["esm2_t6_8M_lam0_tau0.07"]["mcc"], "650M": json.load(open(ROOT / "results/thesis/ch5_data.json"))["F"]["ft_cv"]["esm2_t33_650M_lam0_tau0.07"]["mcc"]}
        ax = axes[0]
        for mode, col in (("finetune", "#D55E00"), ("frozen", "#0072B2")):
            s = cv[cv["mode"] == mode].set_index("checkpoint").reindex(order).dropna(subset=["mcc_mean"])
            ax.errorbar(range(len(s)), s.mcc_mean, yerr=s.mcc_sd, marker="o", color=col, label={"finetune": "fine-tuned", "frozen": "frozen backbone, same head"}[mode], capsize=3)
            ax.set_xticks(range(len(order)), order)
        ax.axhline(0.429, color="grey", ls="--", label="AAC + RF"); ax.set(title="Cross-validation", ylabel="MCC", xlabel="ESM-2 checkpoint"); ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.22))
        ind = pd.DataFrame(ind_rows)
        for ax, ts, tt in zip(axes[1:], TESTS, ("Ind_425, Regime B", "Ind_1049, Regime B")):
            for mode, col in (("finetune", "#D55E00"), ("frozen", "#0072B2")):
                s = ind[(ind["mode"] == mode) & (ind.test_set == ts) & (ind.regime == "B")].set_index("checkpoint").reindex(order).dropna(subset=["mcc_mean"])
                ax.errorbar(range(len(s)), s.mcc_mean, yerr=s.mcc_sd, marker="o", color=col, capsize=3); ax.set_xticks(range(len(order)), order)
            ax.set(title=tt, xlabel="ESM-2 checkpoint")
        fig.tight_layout(); fig.savefig(ROOT / "figures/fig5_11_finetune_scale.png", dpi=250, bbox_inches="tight"); fig.savefig(ROOT / "figures/fig5_11_finetune_scale.pdf", bbox_inches="tight"); plt.close(fig)
    print("done")
main()
