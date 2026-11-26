"""The five conceptual diagrams of Chapter 3, drawn in black and white.

The Guidelines ask for computer-drawn line diagrams in black ink and discourage colour,
so nothing here uses colour: categories are distinguished by line style, hatching, shape
and label. Every label is Times New Roman and nothing is smaller than 10 pt at the
printed width (the A4 text block is 5.71 in wide, and each figure is drawn at that width
or less, so figure points equal printed points).

    python3 src/thesis/diagrams.py

Writes figures/figX_Y_*.pdf (vector, for archiving and for manual insertion) and a
400 dpi .png of the same drawing, which is what the .docx embeds.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "figures"
TEXT_W = 5.71          # inches: the A4 text block between the 4.0 cm and 2.5 cm margins

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 10,            # the Guidelines' floor, and the printed size (1:1 in the page)
    "text.color": "black",
    "axes.edgecolor": "black",
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})

D = json.loads((ROOT / "results/v2/chapter3_data.json").read_text())
F = D["F"]


def canvas(h):
    fig, ax = plt.subplots(figsize=(TEXT_W, h))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, *, style="-", hatch=None, fontsize=10.5, lw=1.0, round_=False, bold=False):
    """a labelled rectangle; `style` and `hatch` are how categories are told apart"""
    if round_:
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=2",
                           fill=hatch is not None, facecolor="white", edgecolor="black",
                           linewidth=lw, linestyle=style, hatch=hatch)
    else:
        p = Rectangle((x, y), w, h, fill=hatch is not None, facecolor="white",
                      edgecolor="black", linewidth=lw, linestyle=style, hatch=hatch)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, linespacing=1.35, fontweight="bold" if bold else "normal", zorder=5,
            bbox=dict(fc="white", ec="none", pad=1.6))
    return (x + w / 2, y, x + w / 2, y + h)      # (cx, bottom, cx, top)


def arrow(ax, p0, p1, *, style="-", lw=1.0, text=None, dx=0, fontsize=10):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=9,
                                 linewidth=lw, linestyle=style, color="black",
                                 shrinkA=0, shrinkB=0))
    if text:
        ax.text((p0[0] + p1[0]) / 2 + dx, (p0[1] + p1[1]) / 2, text, ha="center", va="center",
                fontsize=fontsize, bbox=dict(fc="white", ec="none", pad=0.8))


def save(fig, name):
    for ext, kw in ((".pdf", {}), (".png", {"dpi": 400})):
        fig.savefig(FIG / f"{name}{ext}", bbox_inches="tight", pad_inches=0.02, **kw)
    plt.close(fig)
    print("  wrote", name + ".pdf / .png")


# ===================================================================== 3.1 methodology
def fig_methodology():
    fig, ax = canvas(8.4)
    W, X = 62, 19
    steps = [
        (88, 11, "Three distributed FASTA files\nBenchmark_Dataset, Ind_425, Ind_1049", None, "-"),
        (75, 10, "Provenance audit\ntrace each file to its published source", "....", "-"),
        (62.5, 10, "Integrity audit\nduplicates, label conflicts, train-test overlap", "....", "-"),
        (50, 9, "Cleaning\nBenchmark_clean (3,716 sequences)", None, "-"),
        (36, 11, "Three evaluation regimes\nA as distributed | B exact matches removed |\nC near-duplicates removed", "///", "-"),
        (22.5, 10, "Representations\nhand-crafted descriptors | frozen ESM-2 embeddings", None, "--"),
        (9, 10, "Models and objective\nclassical | six neural architectures | fine-tuned\nloss = cross-entropy + lambda x supervised contrastive", None, "--"),
    ]
    prev = None
    for y, h, label, hatch, ls in steps:
        label = label.replace("lambda", "λ")
        c = box(ax, X, y, W, h, label, hatch=hatch, style=ls)
        if prev:
            arrow(ax, (c[0], prev), (c[0], y + h))
        prev = y
    # the evaluation column on the right
    box(ax, 84, 36, 14, 11, "MCC\nAUROC\npaired\ntests", style=":", fontsize=10)
    arrow(ax, (81, 41.5), (84, 41.5), style=":")
    ax.text(50, 3.0, "Output: what changes once the overlap is removed", ha="center",
            va="center", fontsize=10.5, style="italic")
    arrow(ax, (50, 9), (50, 5.2))
    save(fig, "fig3_1_methodology")


# ===================================================================== 3.2 provenance
def fig_lineage():
    fig, ax = canvas(5.9)
    # Each resource keeps its test set on the OUTSIDE and its training set on the INSIDE,
    # so the two training sets sit next to each other and nothing has to cross anything.
    ax.add_patch(Rectangle((2, 56), 46, 40, fill=False, ec="black", lw=1.2, ls="-"))
    ax.text(25, 91.5, "AIPpred resource", ha="center", fontsize=10, fontweight="bold")
    ax.add_patch(Rectangle((52, 56), 46, 40, fill=False, ec="black", lw=1.2, ls="--"))
    ax.text(75, 91.5, "AntiInflam resource", ha="center", fontsize=10, fontweight="bold")

    box(ax, 4, 59, 20, 26, f"Ind_1049\ntest set\n\n{F['ap_ind_pos'] + F['ap_ind_neg']:,}", fontsize=10)
    box(ax, 26, 59, 20, 26, f"AIPpred\nbenchmark\n\n{F['ap_bench_pos'] + F['ap_bench_neg']:,}", hatch="//", fontsize=10)
    box(ax, 54, 59, 20, 26, f"AntiInflam\ntraining\n\n{F['ai_train_pos'] + F['ai_train_neg']:,}", hatch="\\\\", fontsize=10)
    box(ax, 76, 59, 20, 26, f"Ind_425\ntest set\n\n{F['ai_val_pos'] + F['ai_val_neg']}", fontsize=10)

    # A: inside a resource the two sets are disjoint
    for xc in (25, 75):
        ax.annotate("", xy=(xc + 2.2, 72), xytext=(xc - 2.2, 72),
                    arrowprops=dict(arrowstyle="<|-|>", lw=1.0, ls=":", mutation_scale=7, color="black"))
        ax.text(xc, 75.5, "A", ha="center", fontsize=10, fontweight="bold",
                bbox=dict(fc="white", ec="none", pad=0.8))

    # the training file draws on both resources
    box(ax, 16, 24, 68, 19,
        "Benchmark_Dataset\n(the training file)\nAIPpred benchmark + 612 AntiInflam sequences",
        hatch="xx", lw=1.4, fontsize=10)
    arrow(ax, (36, 59), (40, 43), lw=1.2)
    arrow(ax, (64, 59), (60, 43), lw=1.2)

    # B: the crossings, which are where the overlap comes from
    arrow(ax, (14, 59), (23, 43), lw=1.8)
    arrow(ax, (86, 59), (77, 43), lw=1.8)
    ax.text(6, 50, "B\n298 of Ind_1049\nare in the\ntraining file", ha="center", va="center", fontsize=10,
            bbox=dict(fc="white", ec="black", lw=0.9, boxstyle="round,pad=0.3"))
    ax.text(94, 50, "B\n211 of Ind_425\nare in the\ntraining file", ha="center", va="center", fontsize=10,
            bbox=dict(fc="white", ec="black", lw=0.9, boxstyle="round,pad=0.3"))

    ax.text(50, 17.5,
            "A  within a resource: no shared sequence        "
            "B  across resources: 211 and 298 sequences shared",
            ha="center", va="center", fontsize=10, fontweight="bold")
    ax.text(50, 7.0,
            "Each resource keeps its own training and test sets apart (A). The training file draws on\n"
            "both resources, so each resource's test set now meets the other resource's training data (B).\n"
            "That crossing, and nothing else, is where the overlap comes from.",
            ha="center", va="center", fontsize=10, linespacing=1.55)
    save(fig, "fig3_2_lineage")


# ===================================================================== 3.3 architecture
def fig_architecture():
    fig, ax = canvas(5.2)
    seq = box(ax, 30, 88, 40, 9, "Peptide sequence (7-30 residues)")
    esm = box(ax, 30, 73, 40, 10, "Frozen ESM-2 encoder\n(no gradient, weights unchanged)", hatch="...")
    pool = box(ax, 30, 60, 40, 8, "Mean pooling over residue positions")
    enc = box(ax, 24, 42, 52, 13, "Shared encoder\n2 x (linear -> batch norm -> ReLU -> dropout)\noutput: 256 dimensions", lw=1.4)
    for a, b in ((seq, esm), (esm, pool), (pool, enc)):
        arrow(ax, (50, a[1]), (50, b[3]))

    cls = box(ax, 4, 23, 42, 11, "Classifier head\nlinear 256 -> 1, raw logit", style="-")
    prj = box(ax, 54, 23, 42, 11, "Projection head\nlinear 256 -> 128, L2-normalised", style="--")
    arrow(ax, (38, 42), (25, 34))
    arrow(ax, (62, 42), (75, 34))

    l1 = box(ax, 4, 8, 42, 9, "weighted binary\ncross-entropy", style="-", hatch="//")
    l2 = box(ax, 54, 8, 42, 9, "supervised contrastive\nloss (temperature tau)".replace("tau", "τ"),
             style="--", hatch="\\\\")
    arrow(ax, (25, 23), (25, 17))
    arrow(ax, (75, 23), (75, 17), style="--")
    ax.text(50, 1.5, "combined objective:   L  =  L$_{BCE}$  +  λ L$_{SupCon}$",
            ha="center", va="center", fontsize=10.5, fontweight="bold")
    ax.text(50, 37.5, "both gradients update the same encoder", ha="center", va="center",
            fontsize=10, style="italic")
    save(fig, "fig3_3_architecture")


# ===================================================================== 3.4 regimes
def fig_regimes():
    fig, ax = canvas(4.5)
    rows = json.loads(json.dumps(D["T"]["regimes"]))[1:]
    def n(s): return int(s.replace(",", ""))
    sets = [("Ind_425", [r for r in rows if r[0].startswith("Ind_425")]),
            ("Ind_1049", [r for r in rows if r[0].startswith("Ind_1049")])]
    hatches = [None, "//", "xx"]
    labels = ["A  as distributed", "B  exact matches removed", "C  near-duplicates removed"]
    for si, (name, rs) in enumerate(sets):
        y0 = 58 - si * 44
        ax.text(0, y0 + 26, name, fontsize=10, fontweight="bold", va="center")
        full = n(rs[0][1])
        for ri, r in enumerate(rs):
            w = 72 * n(r[1]) / full
            ax.add_patch(Rectangle((22, y0 + 17 - ri * 9), w, 7, fill=ri > 0, facecolor="white",
                                   edgecolor="black", lw=1.0, hatch=hatches[ri]))
            ax.text(22 + w + 1.5, y0 + 20.5 - ri * 9, f"{n(r[1]):,}", fontsize=10, va="center")
            ax.text(21, y0 + 20.5 - ri * 9, labels[ri], fontsize=10, va="center", ha="right")
    ax.text(50, 2, "Each regime removes sequences from the test set only; the training collection never changes.",
            ha="center", fontsize=10, style="italic")
    save(fig, "fig3_4_regimes")


# ===================================================================== 3.5 splitting
def fig_splitting():
    fig, ax = canvas(4.0)
    ax.text(50, 95, "Benchmark_clean (3,716 sequences)", ha="center", fontsize=10, fontweight="bold")
    # five folds, the held-out one hatched
    for k in range(5):
        x = 8 + k * 17.5
        for j in range(5):
            held = (j == k)
            ax.add_patch(Rectangle((x, 62 - j * 5.2), 15, 4.6, fill=held, facecolor="white",
                                   edgecolor="black", lw=0.8, hatch="xx" if held else None))
        ax.text(x + 7.5, 88, f"fold {k + 1}", ha="center", fontsize=10)
        ax.annotate("", xy=(x + 7.5, 69), xytext=(x + 7.5, 85),
                    arrowprops=dict(arrowstyle="-|>", lw=0.8, mutation_scale=8))
    ax.text(2, 57.5, "train", fontsize=10, ha="right", va="center")
    ax.text(2, 41, "validate", fontsize=10, ha="right", va="center")
    ax.add_patch(Rectangle((8, 31), 15, 4.6, fill=True, facecolor="white", edgecolor="black",
                           lw=0.8, hatch="xx"))
    ax.text(25, 33.3, "= the held-out fold of that split", fontsize=10, va="center")
    ax.text(50, 23,
            "The scaler and the positive-class weight are fitted on the training part of each fold only,\n"
            "then applied to the held-out part. Folds are redrawn for each of five seeds (25 runs per model).",
            ha="center", va="center", fontsize=10, linespacing=1.5)
    ax.add_patch(Rectangle((14, 6), 72, 10, fill=False, edgecolor="black", lw=1.2, ls="--"))
    ax.text(50, 11, "Final models: trained on all of Benchmark_clean with a stratified 10% hold-out\n"
                    "for early stopping, five seeds, then scored on the independent sets",
            ha="center", va="center", fontsize=10, linespacing=1.4)
    save(fig, "fig3_5_splitting")


if __name__ == "__main__":
    print("drawing the five Chapter 3 diagrams (black and white):")
    fig_methodology()
    fig_lineage()
    fig_architecture()
    fig_regimes()
    fig_splitting()
