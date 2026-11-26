"""Re-export the results figures that Chapter 4 still uses so that each one is legible
in black and white, as the Guidelines ask ("unless necessary, the use of color in graphs
and figures is discouraged").

Series are told apart by line style and marker, not colour; heat maps use a sequential
grey ramp so that shading agrees with the printed value instead of contradicting it; and
figure subparts are labelled A, B, C rather than (a), (b), (c).

    PYTHONPATH=. .venv/bin/python src/thesis/figures_grey.py

Reads only result files and changes no number.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.metrics import davies_bouldin_score, silhouette_score

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "results"
FIG = ROOT / "figures"

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Liberation Serif", "DejaVu Serif"],
    "font.size": 11, "axes.titlesize": 11.5, "axes.labelsize": 11,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10,
    "axes.spines.top": False, "axes.spines.right": False,
    "savefig.facecolor": "white", "figure.facecolor": "white",
})

# one grey per series, each with its own dash pattern and marker
GREYS = ["0.0", "0.35", "0.0", "0.55"]
DASHES = [(None, None), (5, 2), (1.2, 1.6), (6, 2, 1.5, 2)]
MARKERS = ["o", "s", "^", "D"]


def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=320, bbox_inches="tight")
    plt.close(fig)
    print("  wrote", name)


# ------------------------------------------------------------------ lambda sweep
def lambda_sweep():
    cv = pd.read_csv(R / "cv_results.csv")
    cv = cv[(cv["family"] == "deep") & (cv["temperature"] == 0.07)]
    # order the checkpoints by size, not alphabetically
    size = {"esm2_t6_8M": 0, "esm2_t12_35M": 1, "esm2_t30_150M": 2, "esm2_t33_650M": 3}
    cks = sorted(cv["checkpoint"].unique(), key=lambda c: size.get(c, 9))
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    for i, ck in enumerate(cks):
        g = cv[cv["checkpoint"] == ck]
        s = g.groupby("lambda_supcon")["mcc"].agg(["mean", "std"]).reset_index()
        x = np.arange(len(s))
        ax.errorbar(x + 0.06 * (i - 1.5), s["mean"], yerr=s["std"],
                    color=GREYS[i], dashes=DASHES[i], marker=MARKERS[i], markersize=5,
                    markerfacecolor="white", markeredgewidth=1.2, capsize=2.5, lw=1.4,
                    label=ck.replace("esm2_", "ESM-2 "))
        ax.set_xticks(x, [f"{v:g}" for v in s["lambda_supcon"]])
    ax.axvline(0, color="0.5", ls=":", lw=1)
    ax.text(0.015, 0.02, "λ = 0: cross-entropy only", transform=ax.transAxes,
            fontsize=9.5, color="0.3")
    ax.set(xlabel="supervised contrastive weight λ",
           ylabel="cross-validated MCC (mean ± s.d.)")
    ax.legend(frameon=False, handlelength=3.2)
    save(fig, "fig5_4_lambda_sweep")


# ------------------------------------------------------------------ t-SNE panels
def tsne_panels(test_set="ind_1049"):
    import json
    sel = json.loads((R / "selected_models.json").read_text())
    head = "esm2_t6_8M"
    base = next(n for n, d in sel.items() if d["checkpoint"] == head and d["role"] == "baseline")
    best = next(n for n, d in sel.items() if d["checkpoint"] == head and d["role"] == "best")
    z0 = np.load(R / "latents" / f"{base}_seed0_{test_set}_B.npz")
    z1 = np.load(R / "latents" / f"{best}_seed0_{test_set}_B.npz")
    y = z0["y"]
    panels = [("A  raw frozen ESM-2 (8M)", z0["raw"]),
              ("B  encoder output, λ = 0", z0["embedding"]),
              (f"C  encoder output, λ = {sel[best]['lambda']:g}", z1["embedding"])]
    fig, axes = plt.subplots(1, 3, figsize=(10.8, 3.9))
    for ax, (title, Z) in zip(axes, panels):
        sil, db = silhouette_score(Z, y), davies_bouldin_score(Z, y)
        E = TSNE(n_components=2, perplexity=30, random_state=42, init="pca").fit_transform(Z)
        # class is carried by marker shape and fill, so the panels survive greyscale
        ax.scatter(E[y == 0, 0], E[y == 0, 1], s=11, marker="o", facecolors="none",
                   edgecolors="0.45", linewidths=0.6, label="non-AIP")
        ax.scatter(E[y == 1, 0], E[y == 1, 1], s=13, marker="^", facecolors="black",
                   edgecolors="black", linewidths=0, alpha=0.75, label="AIP")
        ax.set_title(f"{title}\nsilhouette {sil:.3f}, Davies-Bouldin {db:.3f}", fontsize=10.5)
        ax.set_xticks([]); ax.set_yticks([])
        for s_ in ax.spines.values():
            s_.set_visible(True); s_.set_color("0.6")
    axes[0].legend(frameon=False, markerscale=1.8, loc="upper right", fontsize=9.5)
    save(fig, f"fig5_3_tsne_{test_set}")


# ------------------------------------------------------------------ length-stratified heat map
def length_heatmap():
    d = pd.read_csv(R / "tables" / "TF5_length_stratified.csv")
    d = d[d.length_bin != "all"]
    order = ["7-12", "13-16", "17-20", "21-30"]
    nn = d[d.model == "AAC+RF"].set_index("length_bin")["n"]
    piv = d.pivot(index="model", columns="length_bin", values="auroc")[order]
    piv = piv.loc[piv["13-16"].sort_values(ascending=False).index]
    tidy = lambda s: (s.replace("lam*=", "λ*=").replace("(lam0)", "(λ=0)")
                      .replace("lam2", "λ=2").replace("lam0", "λ=0").replace("_", " "))
    fig, ax = plt.subplots(figsize=(7.2, 0.33 * len(piv) + 1.8))
    # sequential grey: darker always means higher, so shading and number agree
    im = ax.imshow(piv.values, cmap="Greys", vmin=0.2, vmax=0.8, aspect="auto")
    ax.set_xticks(range(4), [f"{c} residues\n(n = {nn[c]})" for c in order])
    ax.set_yticks(range(len(piv)), [tidy(m) for m in piv.index])
    for i in range(piv.shape[0]):
        for j in range(4):
            v = piv.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=9.5,
                    color="white" if v > 0.62 else "black")
    ax.set_title("AUROC by peptide length (Regime B, both test sets pooled)")
    cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.14, fraction=0.04)
    cb.set_label("AUROC (0.5 = chance)")
    for s_ in ax.spines.values():
        s_.set_visible(False)
    save(fig, "figF5_length_stratified")


# ------------------------------------------------------------------ cross-benchmark heat map
def cross_benchmark():
    g = pd.read_csv(R / "tables" / "T5.10_cross_benchmark.csv")
    val = "MCC" if "MCC" in g.columns else "mcc"
    g["v"] = g[val].astype(str).str.split(" ").str[0].astype(float)
    models = ["AAC+RF", "ESM2-650M MLP lam0", "ESM2-8M MLP lam0"]
    fig, axes = plt.subplots(len(models), 3, figsize=(7.1, 2.05 * len(models)))
    for i, m in enumerate(models):
        for j, rg in enumerate(("A", "B", "C")):
            sub = g[(g.model == m) & (g.regime == rg)].pivot(index="train_set", columns="test_set", values="v")
            ax = axes[i, j]
            im = ax.imshow(sub.values, vmin=0, vmax=0.7, cmap="Greys")
            ax.set_xticks(range(sub.shape[1]), [c.replace("_", "\n") for c in sub.columns], fontsize=7)
            ax.set_yticks(range(sub.shape[0]), [c.replace("_", " ") for c in sub.index], fontsize=7)
            for (a, b), v in np.ndenumerate(sub.values):
                ax.text(b, a, f"{v:.2f}", ha="center", va="center",
                        color="white" if v > 0.42 else "black", fontsize=8.5)
            nice = m.replace("lam0", "\u03bb = 0")
            ax.set_title(f"{nice}, Regime {rg}", fontsize=8.5)
            for s_ in ax.spines.values():
                s_.set_visible(False)
    fig.suptitle("Cross-benchmark generalisation: MCC by training set (rows) and independent set (columns)",
                 fontsize=10)
    fig.tight_layout()
    save(fig, "fig5_10_cross_benchmark_heatmap")


if __name__ == "__main__":
    print("re-exporting the results figures in black and white:")
    lambda_sweep()
    tsne_panels("ind_1049")
    length_heatmap()
    cross_benchmark()
