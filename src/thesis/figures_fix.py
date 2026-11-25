"""Readable versions of Figures 5.9b, F1 and F5 (labels >= 10 pt after scaling to the page, legends outside the axes).
Reads only result files; does not change any number. Run: PYTHONPATH=. .venv/bin/python src/thesis/figures_fix.py"""
import json, re
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]; FIG = ROOT / "figures"; TAB = ROOT / "results" / "tables"
OK = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]
plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.labelsize": 11, "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10, "axes.spines.top": False, "axes.spines.right": False})

def save(fig, name):
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight"); fig.savefig(FIG / f"{name}.png", dpi=250, bbox_inches="tight"); plt.close(fig)

# ---- Figure 5.9b: fusion, fine-tuning and baselines (display names from ch5_data.json)
T = json.loads((ROOT / "results/thesis/ch5_data.json").read_text())["T"]
rows = {}
for r in T["fusion"][0:] + T["finetune"][0:]:
    if r[0] == "Model": continue
    rows[r[0]] = (float(r[3]), float(r[4]))   # Regime B MCC Ind_425, Ind_1049
df = pd.DataFrame(rows, index=["Ind_425", "Ind_1049"]).T.sort_values("Ind_1049")
fig, ax = plt.subplots(figsize=(8.2, 0.34 * len(df) + 1.6))
y = np.arange(len(df))
ax.barh(y + 0.2, df["Ind_425"], 0.4, color=OK[0], label="Ind_425 (n = 214)")
ax.barh(y - 0.2, df["Ind_1049"], 0.4, color=OK[1], label="Ind_1049 (n = 751)")
ax.set_yticks(y, df.index); ax.set_xlabel("MCC, Regime B (mean over five final models)")
ax.set_title("Fusion, fine-tuning and baselines")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2, frameon=False)
save(fig, "fig5_9b_fusion_finetune")

# ---- Figure F1: sequence sharing within and between classes (8-mers), replaces the degenerate identity histogram
tf = pd.read_csv(TAB / "TF1_negatives_fragment_test.csv"); v = dict(zip(tf.comparison, tf["value_or_fraction_ge_0.9"]))
cats = ["Positive peptides\n(n = 1,414)", "Negative peptides\n(n = 2,302)"]
same = [v["positives sharing an 8-mer with another POSITIVE"], v["negatives sharing an 8-mer with another NEGATIVE"]]
other = [v["positives sharing an 8-mer with a NEGATIVE"], v["negatives sharing an 8-mer with a POSITIVE"]]
fig, ax = plt.subplots(figsize=(6.6, 4.4)); x = np.arange(2)
b1 = ax.bar(x - 0.19, [100 * a for a in same], 0.36, color=OK[0], label="shares an 8-mer with another peptide of the same class")
b2 = ax.bar(x + 0.19, [100 * a for a in other], 0.36, color=OK[1], label="shares an 8-mer with a peptide of the other class")
for b in list(b1) + list(b2): ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{b.get_height():.1f}%", ha="center", fontsize=10)
ax.set_xticks(x, cats); ax.set_ylabel("share of peptides (%)"); ax.set_ylim(0, 85)
ax.set_title("Do negatives resemble other negatives more than positives?")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.17), frameon=False, ncol=1)
save(fig, "figF1_negative_resemblance")

# ---- Figure F5: AUROC by peptide length group, heat map (models x length groups)
d = pd.read_csv(TAB / "TF5_length_stratified.csv"); d = d[d.length_bin != "all"]
order = ["7-12", "13-16", "17-20", "21-30"]
nn = d[d.model == "AAC+RF"].set_index("length_bin")["n"]
piv = d.pivot(index="model", columns="length_bin", values="auroc")[order]
piv = piv.loc[piv["13-16"].sort_values(ascending=False).index]
tidy = lambda s: s.replace("lam*=", "λ*=").replace("(lam0)", "(λ=0)").replace("lam2", "λ=2").replace("lam0", "λ=0").replace("_", " ")
fig, ax = plt.subplots(figsize=(7.6, 0.34 * len(piv) + 1.8))
im = ax.imshow(piv.values, cmap="RdYlBu", vmin=0.2, vmax=0.8, aspect="auto")
ax.set_xticks(range(4), [f"{c} residues\n(n = {nn[c]})" for c in order]); ax.set_yticks(range(len(piv)), [tidy(m) for m in piv.index])
for i in range(piv.shape[0]):
    for j in range(4):
        val = piv.values[i, j]; ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=10, color="black")
ax.set_title("AUROC by peptide length (Regime B, both test sets pooled)")
cb = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.14, fraction=0.04); cb.set_label("AUROC (0.5 = chance)")
for s in ax.spines.values(): s.set_visible(False)
save(fig, "figF5_length_stratified")
print("figures written")
