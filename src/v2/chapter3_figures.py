"""Figure 3.1 (dataset lineage and the two cross-lineage overlaps) and Figure 3.2 (AIPNet); numbers read from results/."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from src.utils import ROOT
from src.v2.common import R, TABLES

FIG = ROOT / "figures"
BLUE, ORANGE, GREEN, GREY = "#0072B2", "#D55E00", "#009E73", "#444444"
plt.rcParams.update({"font.size": 10, "pdf.fonttype": 42})


def box(ax, x, y, w, h, text, fc, ec="#222222", fs=10, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.03", fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight=weight)


def arrow(ax, p, q, color, both=True, lw=2.0, style="<->"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style if both else "->", mutation_scale=14, color=color, lw=lw))


def save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def fig31():
    t = pd.read_csv(TABLES / "T3.5_cross_benchmark_leakage.csv")
    a = pd.read_csv(R / "data_audit.csv")
    ds = a[a.section == "dataset"].pivot(index="subject", columns="metric", values="value")
    g = lambda tr, te: t[(t.training_set.str.startswith(tr)) & (t.independent_set.str.startswith(te))].iloc[0]
    ap_v = g("AIPpred_benchmark", "AntiInflam_validation")
    ai_i = g("AntiInflam_training", "AIPpred_independent")
    ap_ap = g("AIPpred_benchmark", "AIPpred_independent")
    ai_ai = g("AntiInflam_training", "AntiInflam_validation")
    prov = pd.read_csv(R / "provenance.csv")
    import json
    facts = json.loads((R / "v2" / "phaseA_summary.json").read_text())["provenance_facts"]
    n = lambda x: f"{int(x):,}"
    fig, ax = plt.subplots(figsize=(9.2, 5.6))
    ax.set_xlim(0, 10); ax.set_ylim(-0.1, 6.6); ax.axis("off")
    ax.text(5.0, 6.35, "Each row is one training set paired with the independent set of the other lineage",
            ha="center", fontsize=10.5, weight="bold")
    BLUE_F, GREEN_F = "#DCEBF7", "#DDF2EA"
    # row 1: AIPpred benchmark (blue) vs AntiInflam validation (green)
    box(ax, 0.3, 4.1, 3.5, 1.5, f"AIPpred benchmark\n{n(ap_ap.n_train)} sequences", BLUE_F)
    box(ax, 6.2, 4.1, 3.5, 1.5, f"AntiInflam validation set\n= Ind_425, {n(ai_ai.n_test)} sequences", GREEN_F)
    arrow(ax, (3.9, 4.85), (6.1, 4.85), ORANGE, lw=3.0)
    ax.text(5.0, 5.35, f"{int(ap_v.exact_overlap)} shared sequences", color=ORANGE, fontsize=8.8, weight="bold", ha="center")
    ax.text(5.0, 4.35, f"{int(ap_v.exact_same_label)} same label,\n{int(ap_v.exact_conflicting_label)} opposite label", color=ORANGE, fontsize=9, ha="center", va="center")
    # row 2: AntiInflam training (green) vs AIPpred independent (blue)
    box(ax, 0.3, 1.9, 3.5, 1.5, f"AntiInflam training set\n{n(ai_ai.n_train)} sequences", GREEN_F)
    box(ax, 6.2, 1.9, 3.5, 1.5, f"AIPpred independent set\n= Ind_1049, {n(ap_ap.n_test)} sequences", BLUE_F)
    arrow(ax, (3.9, 2.65), (6.1, 2.65), ORANGE, lw=3.0)
    ax.text(5.0, 3.15, f"{int(ai_i.exact_overlap)} shared sequences", color=ORANGE, fontsize=8.8, weight="bold", ha="center")
    ax.text(5.0, 2.15, f"{int(ai_i.exact_same_label)} same label,\n{int(ai_i.exact_conflicting_label)} opposite label", color=ORANGE, fontsize=9, ha="center", va="center")
    ax.text(5.0, 1.35, f"Within each lineage the training and independent sets share {int(ap_ap.exact_overlap)} sequences "
            f"(AIPpred) and {int(ai_ai.exact_overlap)} sequences (AntiInflam).", ha="center", fontsize=9, color=GREEN, weight="bold")
    box(ax, 1.2, 0.0, 7.6, 0.95, "Distributed Benchmark_Dataset.fasta = AIPpred benchmark\n+ " f"{facts['n_extras_not_in_aippred_bench']} AntiInflam training sequences "
        f"({n(facts['local_benchmark_unique'])} unique sequences)", "#F5F5F5", fs=9)
    save(fig, "fig3_1_dataset_lineage")


def fig32():
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.set_xlim(0, 12.6); ax.set_ylim(0, 6); ax.axis("off")
    box(ax, 0.1, 2.3, 1.9, 1.4, "Mean-pooled\nESM-2 vector\n(d = 320 for 8M)", "#F0F0F0", fs=9)
    box(ax, 2.5, 2.3, 2.1, 1.4, "Linear d to 512\nBatchNorm, ReLU\nDropout 0.3", "#DCEBF7", fs=9)
    box(ax, 5.1, 2.3, 2.1, 1.4, "Linear 512 to 256\nBatchNorm, ReLU\nDropout 0.3", "#DCEBF7", fs=9)
    ax.text(6.15, 3.95, "shared encoder", ha="center", fontsize=9, color=BLUE)
    box(ax, 8.2, 3.8, 2.2, 1.3, "Projection head\nLinear 256 to 128\nL2 normalisation", "#FBE3D2", fs=9)
    box(ax, 8.2, 0.9, 2.2, 1.3, "Classifier head\nLinear 256 to 1\n(raw logit)", "#DDF2EA", fs=9)
    box(ax, 10.8, 3.8, 1.6, 1.3, "SupCon\nloss", "#FBE3D2", fs=9, weight="bold")
    box(ax, 10.8, 0.9, 1.6, 1.3, "BCE loss\n(pos_weight)", "#DDF2EA", fs=8.5, weight="bold")
    for p, q in (((2.0, 3.0), (2.45, 3.0)), ((4.6, 3.0), (5.05, 3.0)), ((7.2, 3.2), (8.15, 4.2)), ((7.2, 2.8), (8.15, 1.9)),
                 ((10.4, 4.45), (10.75, 4.45)), ((10.4, 1.55), (10.75, 1.55))):
        arrow(ax, p, q, "#222222", both=False, lw=1.6)
    ax.text(6.0, 0.2, "L = L_BCE + lambda * L_SupCon   (lambda = 0 gives the BCE-only baseline; both losses update the same encoder)",
            ha="center", fontsize=9.5, style="italic")
    save(fig, "fig3_2_aipnet_architecture")


if __name__ == "__main__":
    fig31()
    fig32()
    print("figures written")
