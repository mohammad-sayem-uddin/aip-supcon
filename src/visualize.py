"""Publication figures (300 dpi, PDF + PNG, colourblind-safe) into figures/."""
from __future__ import annotations

import argparse
import json
import traceback

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.manifold import TSNE
from sklearn.metrics import (auc, confusion_matrix, davies_bouldin_score, precision_recall_curve, roc_auc_score,
                             roc_curve, silhouette_score)

from src.evaluate import bootstrap_ci
from src.utils import ROOT, append_note, mark_stage, setup_logging, Timer

log = setup_logging("visualize")
FIG = ROOT / "figures"
R = ROOT / "results"
PRED = R / "predictions"

OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442", "#000000"]
plt.rcParams.update({
    "font.size": 11, "axes.titlesize": 11, "axes.labelsize": 11, "legend.fontsize": 9, "xtick.labelsize": 10,
    "ytick.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False, "figure.dpi": 100,
    "savefig.dpi": 300, "axes.prop_cycle": plt.cycler(color=OKABE_ITO), "pdf.fonttype": 42,
})
HEAD = "esm2_t6_8M"
TEST_LABEL = {"ind_425": "Ind_425", "ind_1049": "Ind_1049"}


def _save(fig, name: str) -> list[str]:
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return [f"figures/{name}.pdf", f"figures/{name}.png"]


def selected() -> dict:
    return json.loads((R / "selected_models.json").read_text())


def headline_models() -> dict[str, str]:
    """Display name -> prediction-file model name for the main comparison."""
    sel = selected()
    out = {"AAC + SVM": "AAC_SVM", "AAC + RF": "AAC_RF", "AAC+DPC+CTD + LightGBM": "AAC_DPC_CTD_LGBM",
           "ESM-2 8M + LogReg": f"{HEAD}_LR"}
    for n, d in sel.items():
        if d["checkpoint"] == HEAD and d["role"] == "baseline":
            out["ESM-2 8M + MLP (lambda=0)"] = n
        if d["checkpoint"] == HEAD and d["role"] == "best":
            out[f"ESM-2 8M + SupCon (lambda={d['lambda']:g})"] = n
    return out


def _pred(model: str, ts: str, rg: str) -> pd.DataFrame | None:
    p = PRED / f"{model}_{ts}_{rg}.csv"
    return pd.read_csv(p) if p.exists() else None


def plot_roc_curves(test_set: str, regime: str = "B") -> list[str]:
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    for i, (label, m) in enumerate(headline_models().items()):
        d = _pred(m, test_set, regime)
        if d is None:
            continue
        y, p = d["y_true"].to_numpy(), d["y_prob"].to_numpy()
        fpr, tpr, _ = roc_curve(y, p)
        lo, hi = bootstrap_ci(y, p, lambda a, b: roc_auc_score(a, b), n=500)
        ax.plot(fpr, tpr, lw=1.8, color=OKABE_ITO[i % 8], label=f"{label} ({auc(fpr, tpr):.3f} [{lo:.3f}, {hi:.3f}])")
    ax.plot([0, 1], [0, 1], "--", color="grey", lw=1)
    ax.set(xlabel="False positive rate", ylabel="True positive rate",
           title=f"ROC, {TEST_LABEL[test_set]}, Regime {regime}")
    ax.legend(loc="lower right", frameon=False)
    return _save(fig, f"fig5_1_roc_{test_set}_regime{regime}")


def plot_pr_curves(test_set: str, regime: str = "B") -> list[str]:
    fig, ax = plt.subplots(figsize=(5.2, 5.0))
    base = None
    for i, (label, m) in enumerate(headline_models().items()):
        d = _pred(m, test_set, regime)
        if d is None:
            continue
        y, p = d["y_true"].to_numpy(), d["y_prob"].to_numpy()
        base = y.mean()
        pr, rc, _ = precision_recall_curve(y, p)
        from sklearn.metrics import average_precision_score
        ax.plot(rc, pr, lw=1.8, color=OKABE_ITO[i % 8], label=f"{label} (AP {average_precision_score(y, p):.3f})")
    if base is not None:
        ax.axhline(base, ls="--", color="grey", lw=1, label=f"Positive rate ({base:.2f})")
    ax.set(xlabel="Recall", ylabel="Precision", title=f"Precision-recall, {TEST_LABEL[test_set]}, Regime {regime}")
    ax.legend(loc="upper right", frameon=False)
    return _save(fig, f"fig5_2_pr_{test_set}_regime{regime}")


def plot_tsne_panels(test_set: str = "ind_1049") -> list[str]:
    sel = selected()
    base = next(n for n, d in sel.items() if d["checkpoint"] == HEAD and d["role"] == "baseline")
    best = next(n for n, d in sel.items() if d["checkpoint"] == HEAD and d["role"] == "best")
    z0 = np.load(R / "latents" / f"{base}_seed0_{test_set}_B.npz")
    z1 = np.load(R / "latents" / f"{best}_seed0_{test_set}_B.npz")
    y = z0["y"]
    panels = [("(a) Raw frozen ESM-2 (8M)", z0["raw"]), ("(b) Encoder output, lambda = 0", z0["embedding"]),
              (f"(c) Encoder output, lambda = {sel[best]['lambda']:g}", z1["embedding"])]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    rows = []
    for ax, (title, Z) in zip(axes, panels):
        sil, db = silhouette_score(Z, y), davies_bouldin_score(Z, y)
        rows.append({"panel": title, "test_set": test_set, "silhouette": sil, "davies_bouldin": db})
        E = TSNE(n_components=2, perplexity=30, random_state=42, init="pca").fit_transform(Z)
        for lab, col, name in ((0, OKABE_ITO[0], "Non-AIP"), (1, OKABE_ITO[1], "AIP")):
            ax.scatter(E[y == lab, 0], E[y == lab, 1], s=9, alpha=0.65, color=col, label=name, linewidths=0)
        ax.set_title(f"{title}\nsilhouette {sil:.3f}, Davies-Bouldin {db:.3f}")
        ax.set_xticks([]); ax.set_yticks([])
    axes[0].legend(frameon=False, markerscale=2)
    pd.DataFrame(rows).to_csv(R / "tables" / f"cluster_metrics_{test_set}.csv", index=False)
    return _save(fig, f"fig5_3_tsne_{test_set}")


def plot_lambda_sweep() -> list[str]:
    cv = pd.read_csv(R / "cv_results.csv")
    cv = cv[(cv["family"] == "deep") & (cv["temperature"] == 0.07)]
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    for i, (ck, g) in enumerate(cv.groupby("checkpoint")):
        s = g.groupby("lambda_supcon")["mcc"].agg(["mean", "std"]).reset_index()
        x = np.arange(len(s))
        ax.errorbar(x + 0.05 * i, s["mean"], yerr=s["std"], marker="o", capsize=3, lw=1.6, color=OKABE_ITO[i % 8],
                    label=ck.replace("esm2_", "ESM-2 "))
        ax.set_xticks(x, [f"{v:g}" for v in s["lambda_supcon"]])
    ax.axvline(0, color="grey", ls=":", lw=1)
    ax.text(0.02, 0.02, "lambda = 0: BCE-only baseline", transform=ax.transAxes, fontsize=9, color="grey")
    ax.set(xlabel="SupCon weight lambda", ylabel="CV MCC (mean ± std over seeds × folds)",
           title="Lambda sweep, 5-fold CV on cleaned Benchmark")
    ax.legend(frameon=False)
    return _save(fig, "fig5_4_lambda_sweep")


def plot_leakage_gap() -> list[str]:
    frames = [pd.read_csv(R / f) for f in ("baseline_results.csv", "final_results.csv") if (R / f).exists()]
    df = pd.concat(frames)
    df = df[df["eval_set"].isin(["ind_425", "ind_1049"])]
    sel = selected()
    keep = set(headline_models().values())
    df = df[df["model"].isin(keep)]
    label = {v: k for k, v in headline_models().items()}
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)
    for ax, ts in zip(axes, ("ind_425", "ind_1049")):
        g = df[df["eval_set"] == ts].groupby(["model", "regime"])["mcc"].mean().unstack("regime")
        g = g.loc[[m for m in label if m in g.index]]
        x = np.arange(len(g))
        for j, rg in enumerate(["A", "B", "C"]):
            if rg in g:
                ax.bar(x + (j - 1) * 0.27, g[rg], 0.27, label=f"Regime {rg}", color=OKABE_ITO[[4, 0, 1][j]])
        ax.set_xticks(x, [label[m] for m in g.index], rotation=35, ha="right")
        ax.set(title=TEST_LABEL[ts], ylabel="MCC" if ts == "ind_425" else "")
    axes[0].legend(frameon=False)
    fig.suptitle("Performance removed by leakage control (A: as published, B: exact-match removed, C: <90% identity)")
    return _save(fig, "fig5_5_leakage_gap")


def plot_confusion_matrices() -> list[str]:
    frames = [pd.read_csv(R / f) for f in ("baseline_results.csv", "final_results.csv") if (R / f).exists()]
    df = pd.concat(frames)
    df = df[(df["regime"] == "B") & df["eval_set"].isin(["ind_425", "ind_1049"])]
    best = df.groupby("model")["mcc"].mean().idxmax()
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
    for ax, ts in zip(axes, ("ind_425", "ind_1049")):
        d = _pred(best, ts, "B")
        cm = confusion_matrix(d["y_true"], d["y_pred"])
        pct = cm / cm.sum(axis=1, keepdims=True)
        ax.imshow(pct, cmap="Blues", vmin=0, vmax=1)
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]}\n({100 * pct[i, j]:.1f}%)", ha="center", va="center",
                        color="white" if pct[i, j] > 0.5 else "black")
        ax.set_xticks([0, 1], ["Non-AIP", "AIP"]); ax.set_yticks([0, 1], ["Non-AIP", "AIP"])
        ax.set(xlabel="Predicted", ylabel="True", title=f"{TEST_LABEL[ts]}, Regime B")
    fig.suptitle(f"Best model by mean Regime-B MCC: {best}")
    return _save(fig, "fig5_6_confusion_matrices")


def plot_training_curves() -> list[str]:
    from src.pipeline import make_cfg
    from src.train import load_benchmark, train_final
    sel = selected()
    best = next(d for d in sel.values() if d["checkpoint"] == HEAD and d["role"] == "best")
    X, y, _ = load_benchmark(HEAD)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.0))
    for ax, lam in zip(axes, (0.0, best["lambda"])):
        h = pd.DataFrame(train_final(X, y, make_cfg(HEAD, lam, best["tau"]), seed=0, save=False)["history"])
        ax.plot(h["epoch"], h["train_bce"], color=OKABE_ITO[0], label="train BCE")
        ax.plot(h["epoch"], h["train_supcon"], color=OKABE_ITO[1], label="train SupCon")
        ax.set(xlabel="Epoch", ylabel="Loss", title=f"lambda = {lam:g}")
        ax2 = ax.twinx()
        ax2.plot(h["epoch"], h["val_mcc"], color=OKABE_ITO[2], label="val MCC")
        ax2.set_ylabel("Validation MCC")
        ax2.spines["right"].set_visible(True)
        l1, n1 = ax.get_legend_handles_labels(); l2, n2 = ax2.get_legend_handles_labels()
        ax.legend(l1 + l2, n1 + n2, frameon=False, loc="upper right")
    return _save(fig, "figA_training_curves")


def run_all() -> int:
    t = Timer()
    (R / "tables").mkdir(exist_ok=True)
    jobs = {
        "F5.1 ROC Ind_425 B": lambda: plot_roc_curves("ind_425", "B"),
        "F5.1 ROC Ind_1049 B": lambda: plot_roc_curves("ind_1049", "B"),
        "F5.1 ROC Ind_425 A": lambda: plot_roc_curves("ind_425", "A"),
        "F5.1 ROC Ind_1049 A": lambda: plot_roc_curves("ind_1049", "A"),
        "F5.2 PR Ind_425 B": lambda: plot_pr_curves("ind_425", "B"),
        "F5.2 PR Ind_1049 B": lambda: plot_pr_curves("ind_1049", "B"),
        "F5.3 t-SNE Ind_1049": lambda: plot_tsne_panels("ind_1049"),
        "F5.3 t-SNE Ind_425": lambda: plot_tsne_panels("ind_425"),
        "F5.4 lambda sweep": plot_lambda_sweep,
        "F5.5 leakage gap": plot_leakage_gap,
        "F5.6 confusion matrices": plot_confusion_matrices,
        "FA training curves": plot_training_curves,
    }
    status = {}
    for name, fn in jobs.items():
        try:
            status[name] = "ok: " + ", ".join(fn())
            log.info("figure %s done", name)
        except Exception:
            status[name] = "FAILED"
            append_note("BLOCKERS.md", f"S11 figure failed: {name}", "```\n" + traceback.format_exc() + "\n```")
            log.exception("figure %s failed", name)
    (R / "figure_status.json").write_text(json.dumps(status, indent=2))
    failed = [k for k, v in status.items() if v == "FAILED"]
    mark_stage("S11_figures", "partial" if failed else "complete", t.elapsed(), f"failed: {failed}" if failed else "all figures")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.parse_args()
    raise SystemExit(run_all())
