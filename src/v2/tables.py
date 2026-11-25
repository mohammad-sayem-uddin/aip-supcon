"""v2 tables and figures: T5.8 architectures, T5.9 representations, T5.10 cross-benchmark; F5.8-F5.11.

Run: python -m src.v2.tables   (needs Phase B, C, D outputs; skips pieces that do not exist)
"""
from __future__ import annotations

import json
import traceback

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.utils import ROOT
from src.v2.common import R, TABLES, V2, block, mark

FIG = ROOT / "figures"
OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#000000"]
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300, "pdf.fonttype": 42})
TESTS = ("ind_425", "ind_1049")


def ms(x: pd.Series) -> str:
    return f"{x.mean():.4f} ± {x.std(ddof=1):.4f}" if len(x) > 1 else f"{x.mean():.4f}"


def save_fig(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def t58() -> pd.DataFrame:
    cvv2 = pd.read_csv(V2 / "cv_results_v2.csv")
    fin2 = pd.read_csv(V2 / "final_results_v2.csv")
    sel = json.loads((V2 / "selected_v2.json").read_text())
    cv1 = pd.read_csv(R / "cv_results.csv")
    cv1 = cv1[(cv1.family == "deep") & (cv1.checkpoint == "esm2_t6_8M") & (cv1.temperature == 0.07)]
    fin1 = pd.read_csv(R / "final_results.csv")
    comp = pd.read_csv(TABLES / "T5.11_corrected_significance.csv") if (TABLES / "T5.11_corrected_significance.csv").exists() else None
    rows = []
    entries = [("B1_mlp", 2.0, cv1, fin1[fin1.temperature == 0.07], "esm2_t6_8M_lam{l}_tau0.07")]
    for a, d in sel.items():
        entries.append((a, d["lambda_star"], cvv2[cvv2.arch == a], fin2[fin2.arch == a], f"{a}_esm2_t6_8M_lam{{l}}_tau0.07"))
    for a, lam, cv, fin, pat in entries:
        row = {"architecture": a, "lambda_star": lam}
        for tag, l in (("lambda0", 0.0), ("lambda_star", lam)):
            c = cv[cv.lambda_supcon == l]
            row[f"CV_MCC_{tag}"] = ms(c["mcc"])
            row[f"CV_AUROC_{tag}"] = ms(c["auroc"])
            f = fin[(fin.lambda_supcon == l) & (fin.regime == "B")]
            for ts in TESTS:
                g = f[f.eval_set == ts]
                row[f"RegB_MCC_{ts}_{tag}"] = ms(g["mcc"])
                row[f"RegB_AUROC_{ts}_{tag}"] = ms(g["auroc"])
        rows.append(row)
    t = pd.DataFrame(rows)
    # attach paired statistics (Regime B, ensemble predictions)
    if comp is not None:
        for ts in TESTS:
            for key, col in (("mcc_diff", "dMCC"), ("auroc_diff", "dAUROC")):
                vals, lo, hi = [], [], []
                for a, lam in zip(t.architecture, t.lambda_star):
                    lab = "B1_mlp (v1 MLP, tau 0.07) lambda=2 vs 0" if a == "B1_mlp" else f"{a} lambda*={lam:g} vs 0"
                    r = comp[(comp.comparison == lab) & (comp.test_set == ts) & (comp.regime == "B")]
                    vals.append(r[key].iloc[0] if len(r) else np.nan)
                    lo.append(r[key + "_lo"].iloc[0] if len(r) else np.nan)
                    hi.append(r[key + "_hi"].iloc[0] if len(r) else np.nan)
                t[f"{col}_{ts}_RegB"] = [f"{v:+.4f} [{l:+.4f}, {h:+.4f}]" if not np.isnan(v) else "" for v, l, h in zip(vals, lo, hi)]
            ps, pa, ma = [], [], []
            for a, lam in zip(t.architecture, t.lambda_star):
                lab = "B1_mlp (v1 MLP, tau 0.07) lambda=2 vs 0" if a == "B1_mlp" else f"{a} lambda*={lam:g} vs 0"
                r = comp[(comp.comparison == lab) & (comp.test_set == ts) & (comp.regime == "B")]
                ps.append(r["delong_p"].iloc[0] if len(r) else np.nan)
                pa.append(r["p_delong_bh_family"].iloc[0] if len(r) else np.nan)
                ma.append(r["auroc_mde80"].iloc[0] if len(r) else np.nan)
            t[f"DeLong_p_raw_{ts}"], t[f"DeLong_p_BH_{ts}"], t[f"MDE80_AUROC_{ts}"] = ps, pa, ma
    t["analysis_tier"] = ["secondary (B1 reference reuses v1 models; tau=0.07)"] + ["secondary (H2)"] * (len(t) - 1)
    t.round(4).to_csv(TABLES / "T5.8_architecture_comparison.csv", index=False)
    # long table with all regimes
    f = pd.concat([fin2.assign(arch=fin2.arch), fin1[(fin1.model.isin(["esm2_t6_8M_lam0_tau0.07", "esm2_t6_8M_lam2_tau0.07"]))].assign(arch="B1_mlp")])
    f["lambda_label"] = np.where(f.lambda_supcon == 0, "lambda=0", "lambda*")
    long = f.groupby(["arch", "lambda_label", "eval_set", "regime"]).agg(
        mcc=("mcc", ms), auroc=("auroc", ms), auprc=("auprc", ms), n_seeds=("seed", "nunique"), n_eval=("n_eval", "first")).reset_index()
    long["analysis_tier"] = np.where(long.regime == "B", "secondary", "exploratory")
    long.to_csv(TABLES / "T5.8b_architecture_all_regimes.csv", index=False)
    # F5.8
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    archs = list(t.architecture)
    for ax, ts in zip(axes, TESTS):
        for k, (tag, lbl) in enumerate((("lambda0", "lambda = 0"), ("lambda_star", "lambda = CV-best"))):
            m, s = [], []
            for a, lam in zip(archs, t.lambda_star):
                src = fin1[fin1.model == f"esm2_t6_8M_lam{lam:g}_tau0.07"] if a == "B1_mlp" and tag == "lambda_star" else \
                    fin1[fin1.model == "esm2_t6_8M_lam0_tau0.07"] if a == "B1_mlp" else fin2[(fin2.arch == a) & (fin2.lambda_supcon == (0.0 if tag == "lambda0" else lam))]
                g = src[(src.eval_set == ts) & (src.regime == "B")]["mcc"]
                m.append(g.mean()); s.append(g.std(ddof=1))
            ax.bar(np.arange(len(archs)) + (k - 0.5) * 0.38, m, 0.38, yerr=s, capsize=3, label=lbl, color=OKABE[k])
        ax.set_xticks(range(len(archs)), [a.split("_", 1)[0] + "\n" + a.split("_", 1)[1].replace("cnn_bilstm", "cnn-\nbilstm").replace("transformer", "trans-\nformer") for a in archs], fontsize=9)
        ax.set(title=f"{ts.replace('ind_', 'Ind_')}, Regime B", ylabel="MCC (mean ± SD over 5 seeds)" if ts == TESTS[0] else "")
    axes[0].legend(frameon=False)
    fig.suptitle("Does the contrastive objective help across architectures? (8M residue embeddings)")
    save_fig(fig, "fig5_8_architecture_lambda")
    return t


def t59() -> pd.DataFrame:
    f = V2 / "repr_results_v2.csv"
    frames = [pd.read_csv(f)] if f.exists() else []
    ft = V2 / "finetune_results_v2.csv"
    if ft.exists():
        d = pd.read_csv(ft)
        d["phase"], d["features"], d["classifier"] = "C3", d["mode"], "head"
        frames.append(d)
    base = pd.read_csv(R / "baseline_results.csv")
    base = base[base.model.isin(["AAC_RF", "AAC_DPC_CTD_LGBM", "esm2_t6_8M_LR", "esm2_t33_650M_LR"]) if "esm2_t33_650M_LR" in set(base.model) else base.model.isin(["AAC_RF", "AAC_DPC_CTD_LGBM", "esm2_t6_8M_LR"])].copy()
    base["phase"], base["features"], base["classifier"] = "v1 baseline", base["model"], ""
    frames.append(base)
    fin1 = pd.read_csv(R / "final_results.csv")
    m650 = fin1[fin1.model == "esm2_t33_650M_lam0_tau0.07"].copy()
    m650["phase"], m650["features"], m650["classifier"] = "v1 deep", "esm650_mean", "mlp (v1 protocol)"
    frames.append(m650)
    allr = pd.concat(frames, ignore_index=True)
    allr["analysis_tier"] = "exploratory"
    rows = []
    for (ph, model), g in allr.groupby(["phase", "model"], sort=False):
        r = {"phase": ph, "model": model}
        cv = g[g.eval_set == "cv"]
        r["CV_MCC"], r["CV_AUROC"] = (ms(cv["mcc"]), ms(cv["auroc"])) if len(cv) else ("", "")
        for ts in TESTS:
            for rg in ("A", "B", "C"):
                x = g[(g.eval_set == ts) & (g.regime == rg)]
                r[f"{ts}_{rg}_MCC"] = ms(x["mcc"]) if len(x) else ""
                r[f"{ts}_{rg}_AUROC"] = ms(x["auroc"]) if len(x) else ""
        r["analysis_tier"] = "exploratory"
        rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(TABLES / "T5.9_representation_comparison.csv", index=False)
    # F5.9: pooling ablation + fusion, Regime B MCC / AUROC
    sel = allr[(allr.regime == "B") & allr.eval_set.isin(TESTS)]
    pool = sel[sel.phase == "C1"].groupby(["model", "eval_set"])["mcc"].agg(["mean", "std"]).reset_index()
    ref = sel[sel.model == "AAC_RF"].groupby("eval_set")["mcc"].mean()
    if len(pool):
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
        names = list(dict.fromkeys(pool.model))
        for ax, ts in zip(axes, TESTS):
            p = pool[pool.eval_set == ts].set_index("model").reindex(names)
            ax.bar(range(len(names)), p["mean"], yerr=p["std"], capsize=3, color=OKABE[0])
            if ts in ref.index:
                ax.axhline(ref[ts], color=OKABE[1], ls="--", label="AAC+RF (v1 baseline)")
            ax.set_xticks(range(len(names)), [n.split("|")[0].replace("esm650_", "") for n in names], rotation=30, ha="right")
            ax.set(title=f"{ts.replace('ind_', 'Ind_')}, Regime B", ylabel="MCC" if ts == TESTS[0] else "")
        axes[0].legend(frameon=False)
        fig.suptitle("Pooling ablation on frozen ESM-2 650M (MLP, lambda = 0)")
        save_fig(fig, "fig5_9_pooling_ablation")
    fus = sel[sel.phase.isin(["C2", "C3", "v1 baseline"])].groupby(["model", "eval_set"])["mcc"].mean().unstack("eval_set")
    if len(fus):
        fig, ax = plt.subplots(figsize=(9, 5.5))
        fus = fus.sort_values(TESTS[1])
        y = np.arange(len(fus))
        for k, ts in enumerate(TESTS):
            ax.barh(y + (k - 0.5) * 0.4, fus[ts], 0.4, label=ts.replace("ind_", "Ind_"), color=OKABE[k])
        ax.set_yticks(y, fus.index, fontsize=7)
        ax.set(xlabel="MCC (Regime B, mean over seeds)", title="Feature fusion, fine-tuning and baselines")
        ax.legend(frameon=False)
        save_fig(fig, "fig5_9b_fusion_finetune")
    return t


def t510() -> pd.DataFrame | None:
    f = V2 / "cross_benchmark_results_v2.csv"
    if not f.exists():
        return None
    d = pd.read_csv(f)
    g = d.groupby(["train_set", "test_set", "regime", "model"]).agg(n_train=("n_train", "first"), n_eval=("n_eval", "first"),
                                                                    MCC=("mcc", ms), AUROC=("auroc", ms), mcc_mean=("mcc", "mean")).reset_index()
    g["analysis_tier"] = "exploratory"
    g.drop(columns="mcc_mean").to_csv(TABLES / "T5.10_cross_benchmark.csv", index=False)
    models = ["AAC+RF", "ESM2-650M MLP lam0", "ESM2-8M MLP lam0"]
    fig, axes = plt.subplots(len(models), 3, figsize=(12, 3.2 * len(models)))
    for i, m in enumerate(models):
        for j, rg in enumerate(("A", "B", "C")):
            sub = g[(g.model == m) & (g.regime == rg)].pivot(index="train_set", columns="test_set", values="mcc_mean")
            ax = axes[i, j]
            im = ax.imshow(sub.values, vmin=0, vmax=0.7, cmap="viridis")
            ax.set_xticks(range(sub.shape[1]), [c.replace("_", "\n") for c in sub.columns], fontsize=7)
            ax.set_yticks(range(sub.shape[0]), [c.replace("_", " ") for c in sub.index], fontsize=7)
            for (a, b), v in np.ndenumerate(sub.values):
                ax.text(b, a, f"{v:.2f}", ha="center", va="center", color="white" if v < 0.4 else "black", fontsize=9)
            ax.set_title(f"{m}, Regime {rg}", fontsize=9)
    fig.suptitle("Cross-benchmark generalisation: MCC by training set (rows) and independent set (columns)")
    fig.tight_layout()
    save_fig(fig, "fig5_10_cross_benchmark_heatmap")
    return g


def run() -> None:
    for name, fn in (("T5.8/F5.8", t58), ("T5.9/F5.9", t59), ("T5.10/F5.10", t510)):
        try:
            fn()
        except Exception:
            block(f"v2 table/figure {name} failed", "```\n" + traceback.format_exc() + "\n```")
    mark("V2_tables", "complete", 0.0, "T5.8, T5.9, T5.10 and figures")


if __name__ == "__main__":
    run()
