"""Completion run, task 2.1: test whether the leakage gap (MCC in Regime A minus MCC in Regime B) differs between model families.

Pre-declared decision rule (written before running): the chapter statement "the gap is largest for flexible non-linear models" is kept
as an inferential claim only if (i) the contrast Flexible - Linear, averaged over the two test sets, has a BH-adjusted bootstrap p < 0.05
with a 95% interval above 0, AND (ii) the model-level Mann-Whitney U test (flexible vs linear, one gap per model and set-average) has
p < 0.05. Otherwise the wording is reduced to a purely descriptive statement.

Method. For every model the ensemble predictions (threshold 0.5) of Regime A are paired with those of Regime B (B is the subset of A without
the overlapping sequences). The peptides of each test set are resampled 2,000 times (stratified by class); in each resample the model's
MCC_A is computed on all drawn peptides and MCC_B on the drawn peptides that belong to Regime B; gap = MCC_A - MCC_B. The same resamples
are used for every model, so contrasts between models are paired. Family gap = mean gap over the base models (lambda = 0 where a lambda grid
exists) of the family. Inference concerns these models and the test peptides; the model-level test is a sensitivity analysis.
Run: PYTHONPATH=. .venv/bin/python -m src.v2.gap_tests
"""
from __future__ import annotations
import json, re
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats as st
from src.v2.stats import bh_adjust
from src.utils import ROOT

R = ROOT / "results"; TABLES = R / "tables"; V2 = R / "v2"
TESTS = ("ind_425", "ind_1049"); NB = 2000

FAMILY = {  # stem -> (display, family)
    **{f"esm2_{c}_LR": (f"ESM-2 {s} + logistic regression", "Linear") for c, s in (("t6_8M", "8M"), ("t12_35M", "35M"), ("t30_150M", "150M"))},
    "AAC_SVM": ("AAC + SVM (RBF)", "Kernel SVM"),
    "AAC_RF": ("AAC + random forest", "Trees"), "AAC_DPC_CTD_LGBM": ("AAC+DPC+CTD + LightGBM", "Trees"),
    "hand__rf": ("Hand-crafted + RF", "Trees"), "hand__lgbm": ("Hand-crafted + LightGBM", "Trees"),
    "esm8_mean__rf": ("8M mean + RF", "Trees"), "esm8_mean__lgbm": ("8M mean + LightGBM", "Trees"),
    "esm650_mean__rf": ("650M mean + RF", "Trees"), "esm650_mean__lgbm": ("650M mean + LightGBM", "Trees"),
    "esm8_fusion__rf": ("8M fusion + RF", "Trees"), "esm8_fusion__lgbm": ("8M fusion + LightGBM", "Trees"),
    "esm650_fusion__rf": ("650M fusion + RF", "Trees"), "esm650_fusion__lgbm": ("650M fusion + LightGBM", "Trees"),
    "esm2_t6_8M_lam0_tau0.07": ("8M MLP", "MLP"), "esm2_t12_35M_lam0_tau0.07": ("35M MLP", "MLP"), "esm2_t30_150M_lam0_tau0.07": ("150M MLP", "MLP"),
    "esm2_t33_650M_lam0_tau0.07": ("650M MLP", "MLP"),
    "hand__mlp": ("Hand-crafted + MLP", "MLP"), "esm8_mean__mlp": ("8M mean + MLP", "MLP"), "esm8_fusion__mlp": ("8M fusion + MLP", "MLP"),
    "esm650_fusion__mlp": ("650M fusion + MLP", "MLP"), "esm2_t6_8M_frozen": ("8M frozen control (fine-tuning head)", "MLP"),
    "esm650_max__mlp": ("650M max-pool MLP", "MLP"), "esm650_meanmax__mlp": ("650M mean||max MLP", "MLP"), "esm650_cls__mlp": ("650M CLS MLP", "MLP"),
    "esm650_firstlast__mlp": ("650M first/last MLP", "MLP"),
    "B2_cnn_esm2_t6_8M_lam0_tau0.07": ("B2 CNN", "Residue-level network"), "B3_bilstm_esm2_t6_8M_lam0_tau0.07": ("B3 BiLSTM", "Residue-level network"),
    "B4_cnn_bilstm_esm2_t6_8M_lam0_tau0.07": ("B4 CNN-BiLSTM", "Residue-level network"), "B5_transformer_esm2_t6_8M_lam0_tau0.07": ("B5 Transformer", "Residue-level network"),
    "B6_attnpool_esm2_t6_8M_lam0_tau0.07": ("B6 attention pooling", "Residue-level network"), "esm650_attention__attn_mlp": ("650M attention-pool MLP", "Residue-level network"),
    "esm2_t6_8M_finetune": ("8M fine-tuned", "Fine-tuned"),
}
LOGP = {"8M MLP": np.log10(8e6), "35M MLP": np.log10(35e6), "150M MLP": np.log10(150e6), "650M MLP": np.log10(650e6)}  # parameter counts of the ESM-2 checkpoints (order of magnitude; used only to order the checkpoints)

def path(stem, ts, rg):
    for d in (R / "v2" / "predictions", R / "predictions"):
        p = d / f"{stem}_{ts}_{rg}.csv"
        if p.exists(): return p
    raise FileNotFoundError(f"{stem}_{ts}_{rg}")

def mcc_w(W, y, P):
    """Weighted MCC for every resample (rows of W) and model (columns of P). P: 0/1 predictions (n x M)."""
    tp = W @ (y[:, None] * P); fp = W @ ((1 - y)[:, None] * P); fn = W @ (y[:, None] * (1 - P)); tn = W @ ((1 - y)[:, None] * (1 - P))
    den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)); return np.where(den > 0, (tp * tn - fp * fn) / np.where(den > 0, den, 1), 0.0)

def main():
    stems = list(FAMILY); rng = np.random.default_rng(20261126)
    gaps_boot, gaps_obs, ns, mcc_obs = {}, {}, {}, {}
    for ts in TESTS:
        PA, PB, y, inB = [], [], None, None
        for s in stems:
            a = pd.read_csv(path(s, ts, "A")); b = pd.read_csv(path(s, ts, "B"))
            if y is None:
                y = a["y_true"].to_numpy().astype(float); seqs = a["sequence"].tolist(); inB = a["sequence"].isin(set(b["sequence"])).to_numpy()
                assert inB.sum() == len(b), "Regime B is not a subset of Regime A"
            assert a["sequence"].tolist() == seqs and set(b["sequence"]) <= set(seqs)
            PA.append(((a["y_prob"].to_numpy() >= 0.5)).astype(float)); PB.append(a["sequence"].map(dict(zip(b["sequence"], (b["y_prob"] >= 0.5).astype(float)))).fillna(0).to_numpy())
        PA, PB = np.array(PA).T, np.array(PB).T; n = len(y); ns[ts] = (n, int(inB.sum()))
        # stratified bootstrap weights
        W = np.zeros((NB, n)); 
        for cls in (0.0, 1.0):
            idx = np.where(y == cls)[0]
            for r in range(NB): W[r] += np.bincount(rng.choice(idx, len(idx)), minlength=n)
        WB = W * inB[None, :]
        obs = mcc_w(np.ones((1, n)), y, PA)[0] - mcc_w(inB.astype(float)[None, :], y, PB)[0]
        boot = mcc_w(W, y, PA) - mcc_w(WB, y, PB)
        gaps_obs[ts], gaps_boot[ts] = obs, boot
        mcc_obs[ts] = (mcc_w(np.ones((1, n)), y, PA)[0], mcc_w(inB.astype(float)[None, :], y, PB)[0])
        print(ts, "n", n, "n_B", int(inB.sum()), "gap range", obs.min().round(3), obs.max().round(3), flush=True)
    names = [FAMILY[s][0] for s in stems]; fam = np.array([FAMILY[s][1] for s in stems])
    rows = []
    for ts in TESTS:
        for j, s in enumerate(stems):
            b = gaps_boot[ts][:, j]
            rows.append({"model": names[j], "family": fam[j], "test_set": ts, "n_A": ns[ts][0], "n_B": ns[ts][1], "mcc_A": mcc_obs[ts][0][j], "mcc_B": mcc_obs[ts][1][j], "gap_mcc": gaps_obs[ts][j],
                         "gap_lo": np.quantile(b, .025), "gap_hi": np.quantile(b, .975), "p_gap_le_0": float((b <= 0).mean() * 2 if (b <= 0).mean() < .5 else 1.0)})
    per = pd.DataFrame(rows); per["p_gap_le_0_BH"] = bh_adjust(per["p_gap_le_0"].to_numpy())
    per.to_csv(TABLES / "T5.12_leakage_gap_per_model.csv", index=False)
    # ---- family contrasts
    flex = fam != "Linear"
    def famgap(M, mask): return M[:, mask].mean(axis=1)
    def ctr(a, b):
        out = {}
        for ts in TESTS: out[ts] = famgap(gaps_boot[ts], a) - famgap(gaps_boot[ts], b)
        out["both"] = (out["ind_425"] + out["ind_1049"]) / 2
        return out
    def obs_ctr(a, b):
        o = {ts: gaps_obs[ts][a].mean() - gaps_obs[ts][b].mean() for ts in TESTS}; o["both"] = (o["ind_425"] + o["ind_1049"]) / 2; return o
    C = {"Flexible non-linear (all) - Linear": (flex & (fam != "Fine-tuned"), fam == "Linear"), "Trees - Linear": (fam == "Trees", fam == "Linear"), "Kernel SVM - Linear": (fam == "Kernel SVM", fam == "Linear"),
         "MLP - Linear": (fam == "MLP", fam == "Linear"), "Residue-level network - Linear": (fam == "Residue-level network", fam == "Linear"), "Fine-tuned - Linear": (fam == "Fine-tuned", fam == "Linear"),
         "Trees - MLP": (fam == "Trees", fam == "MLP"), "Trees - Residue-level network": (fam == "Trees", fam == "Residue-level network"), "MLP - Residue-level network": (fam == "MLP", fam == "Residue-level network"),
         "Fine-tuned - MLP (frozen vectors)": (fam == "Fine-tuned", fam == "MLP"),
         "LightGBM (6) - Linear": ((fam == "Trees") & np.array(["LightGBM" in n for n in names]), fam == "Linear"),
         "Random forest (6) - Linear": ((fam == "Trees") & np.array([("RF" in n or "random forest" in n) for n in names]), fam == "Linear"),
         "LightGBM (6) - Random forest (6)": ((fam == "Trees") & np.array(["LightGBM" in n for n in names]), (fam == "Trees") & np.array([("RF" in n or "random forest" in n) for n in names]))}
    crow = []
    for name, (a, b) in C.items():
        bs, ob = ctr(a, b), obs_ctr(a, b)
        for key in ("ind_425", "ind_1049", "both"):
            d = bs[key]; p = 2 * min((d <= 0).mean(), (d >= 0).mean()); p = max(p, 1 / (NB + 1))
            # model-level Mann-Whitney on set-averaged gaps
            ga = (gaps_obs["ind_425"] + gaps_obs["ind_1049"]) / 2
            mw = st.mannwhitneyu(ga[a], ga[b], alternative="two-sided").pvalue if key == "both" and a.sum() >= 2 and b.sum() >= 2 else np.nan
            crow.append({"contrast": name, "scope": key, "n_models_a": int(a.sum()), "n_models_b": int(b.sum()), "mean_gap_a": float(gaps_obs["ind_425"][a].mean() if key == "ind_425" else gaps_obs["ind_1049"][a].mean() if key == "ind_1049" else (gaps_obs["ind_425"][a].mean() + gaps_obs["ind_1049"][a].mean()) / 2),
                         "mean_gap_b": float(gaps_obs["ind_425"][b].mean() if key == "ind_425" else gaps_obs["ind_1049"][b].mean() if key == "ind_1049" else (gaps_obs["ind_425"][b].mean() + gaps_obs["ind_1049"][b].mean()) / 2),
                         "diff": ob[key], "lo": float(np.quantile(d, .025)), "hi": float(np.quantile(d, .975)), "p_boot": p, "p_mannwhitney_models": mw})
    # capacity: slope of the gap on log10(parameters) within the MLP checkpoints
    mlp = [i for i, s in enumerate(stems) if FAMILY[s][0] in LOGP]; x = np.array([LOGP[names[i]] for i in mlp]); x = x - x.mean()
    def slope(M): return (M[:, mlp] * x).sum(axis=1) / (x ** 2).sum()
    sb = {ts: slope(gaps_boot[ts]) for ts in TESTS}; sb["both"] = (sb["ind_425"] + sb["ind_1049"]) / 2
    so = {ts: float((gaps_obs[ts][mlp] * x).sum() / (x ** 2).sum()) for ts in TESTS}; so["both"] = (so["ind_425"] + so["ind_1049"]) / 2
    for key in ("ind_425", "ind_1049", "both"):
        d = sb[key]; p = max(2 * min((d <= 0).mean(), (d >= 0).mean()), 1 / (NB + 1))
        crow.append({"contrast": "Capacity: slope of gap per decade of parameters (8M, 35M, 150M, 650M MLP)", "scope": key, "n_models_a": 4, "n_models_b": 0, "mean_gap_a": np.nan, "mean_gap_b": np.nan,
                     "diff": so[key], "lo": float(np.quantile(d, .025)), "hi": float(np.quantile(d, .975)), "p_boot": p, "p_mannwhitney_models": np.nan})
    cdf = pd.DataFrame(crow)
    for sc in ("ind_425", "ind_1049", "both"):
        m = cdf.scope == sc; cdf.loc[m, "p_BH_within_scope"] = bh_adjust(cdf.loc[m, "p_boot"].to_numpy())
    cdf["p_BH_all"] = bh_adjust(cdf["p_boot"].to_numpy())
    cdf.to_csv(TABLES / "T5.12b_leakage_gap_family_contrasts.csv", index=False)
    pd.DataFrame({"model": names, "stem": stems, "family": fam}).to_csv(V2 / "gap_family_assignment.csv", index=False)
    fam_tab = per.groupby(["family", "test_set"]).agg(n_models=("gap_mcc", "size"), mean_gap=("gap_mcc", "mean"), min_gap=("gap_mcc", "min"), max_gap=("gap_mcc", "max")).reset_index()
    fam_tab.to_csv(TABLES / "T5.12c_leakage_gap_family_summary.csv", index=False)
    print(fam_tab.round(3).to_string()); print(cdf.round(4).to_string())
    main_row = cdf[(cdf.contrast.str.startswith("Flexible")) & (cdf.scope == "both")].iloc[0]
    rule = bool(main_row.p_BH_within_scope < 0.05 and main_row.lo > 0 and main_row.p_mannwhitney_models < 0.05)
    json.dump({"rule_met": rule, "flex_minus_linear_both": main_row.to_dict()}, open(V2 / "gap_decision.json", "w"), indent=1, default=float)
    print("DECISION: inferential claim", "SUPPORTED" if rule else "NOT supported -> descriptive wording")
main()
