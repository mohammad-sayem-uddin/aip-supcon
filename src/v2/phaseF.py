"""Phase F: why does AAC win? negatives-as-fragments test, motif analysis, error analysis, length-stratified performance.

Run: python -m src.v2.phaseF   -> results/tables/TF*.csv and figures/figF_*.png|pdf  (all exploratory)
"""
from __future__ import annotations

import json
import time
from collections import Counter
from itertools import product

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import matthews_corrcoef, roc_auc_score

from src.data import max_identity_to_train
from src.features import AA
from src.utils import ROOT, setup_logging
from src.v2.common import R, TABLES, V2, mark
from src.v2.stats import bh_adjust

log = setup_logging("phaseF")
FIG = ROOT / "figures"
PROC = ROOT / "data" / "processed"
OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]


def _save(fig, name):
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def bench() -> pd.DataFrame:
    return pd.read_csv(PROC / "benchmark_clean.csv")


# ------------------------------------------------------------- F1 fragments


def kmers(s: str, k: int) -> set[str]:
    return {s[i : i + k] for i in range(len(s) - k + 1)}


def f1_negatives() -> pd.DataFrame:
    b = bench()
    seqs, y = b["sequence"].tolist(), b["label"].to_numpy()
    pos = [s for s, l in zip(seqs, y) if l == 1]
    neg = [s for s, l in zip(seqs, y) if l == 0]
    rows = []

    def maxid(query, ref, exclude_self):
        ref = list(ref)
        mx = np.full(len(query), -1.0)
        # identity to ANY reference (self excluded by dropping identical strings from the reference only when requested)
        if exclude_self:
            out = []
            for i in range(0, len(query), 1):
                r = [x for x in ref if x != query[i]]
                out.append(max_identity_to_train([query[i]], r, floor=0.8)[0])
            return np.array(out)
        return max_identity_to_train(query, ref, floor=0.8)

    t0 = time.time()
    neg_to_pos = max_identity_to_train(neg, pos, floor=0.8)
    pos_to_neg = max_identity_to_train(pos, neg, floor=0.8)
    # same-class baselines via leave-one-out on a random subsample (exact for the sample)
    rng = np.random.default_rng(0)
    sub_neg = list(rng.choice(neg, 800, replace=False))
    sub_pos = list(rng.choice(pos, 800, replace=False))
    neg_to_neg = maxid(sub_neg, neg, True)
    pos_to_pos = maxid(sub_pos, pos, True)
    log.info("F1 identity done in %.0fs", time.time() - t0)
    for name, v in (("negative -> nearest POSITIVE", neg_to_pos), ("positive -> nearest NEGATIVE", pos_to_neg),
                    ("negative -> nearest other NEGATIVE (n=800 sample)", neg_to_neg),
                    ("positive -> nearest other POSITIVE (n=800 sample)", pos_to_pos)):
        rows.append({"comparison": name, "n": len(v), "frac_identity_ge_0.9": float((v >= 0.9 - 1e-12).mean()),
                     "frac_identity_ge_0.8": float((v >= 0.8 - 1e-12).mean())})
    # shared 8-mers between classes (sliding-window / common-parent proxy)
    pk, nk = Counter(), Counter()
    for s in pos:
        pk.update(kmers(s, 8))
    for s in neg:
        nk.update(kmers(s, 8))
    share_pos = np.mean([any(k in nk for k in kmers(s, 8)) for s in pos if len(s) >= 8])
    share_neg = np.mean([any(k in pk for k in kmers(s, 8)) for s in neg if len(s) >= 8])
    same_pos = np.mean([any(pk[k] > 1 for k in kmers(s, 8)) for s in pos if len(s) >= 8])
    same_neg = np.mean([any(nk[k] > 1 for k in kmers(s, 8)) for s in neg if len(s) >= 8])
    rows += [{"comparison": "positives sharing an 8-mer with a NEGATIVE", "n": len(pos), "frac_identity_ge_0.9": float(share_pos)},
             {"comparison": "negatives sharing an 8-mer with a POSITIVE", "n": len(neg), "frac_identity_ge_0.9": float(share_neg)},
             {"comparison": "positives sharing an 8-mer with another POSITIVE", "n": len(pos), "frac_identity_ge_0.9": float(same_pos)},
             {"comparison": "negatives sharing an 8-mer with another NEGATIVE", "n": len(neg), "frac_identity_ge_0.9": float(same_neg)}]
    # cluster co-membership at 0.9
    from src.v2.common import greedy_cluster
    reps, assign = greedy_cluster(seqs, 0.9)
    lab = dict(zip(seqs, y))
    clusters: dict[str, list[int]] = {}
    for s, r in assign.items():
        clusters.setdefault(r, []).append(lab[s])
    multi = [v for v in clusters.values() if len(v) > 1]
    mixed = [v for v in multi if len(set(v)) > 1]
    rows.append({"comparison": f"0.9-identity clusters with >=2 members that contain BOTH labels ({len(mixed)} of {len(multi)})",
                 "n": len(multi), "frac_identity_ge_0.9": len(mixed) / max(len(multi), 1)})
    # length / composition separability
    lens = np.array([len(s) for s in seqs])
    rows.append({"comparison": "AUROC of sequence length alone (benchmark_clean, positive = longer)", "n": len(y),
                 "frac_identity_ge_0.9": float(roc_auc_score(y, lens))})
    df = pd.DataFrame(rows).rename(columns={"frac_identity_ge_0.9": "value_or_fraction_ge_0.9"})
    df.to_csv(TABLES / "TF1_negatives_fragment_test.csv", index=False)
    fig, ax = plt.subplots(figsize=(6, 4))
    for lab_, v, c in (("negative -> nearest positive", neg_to_pos, OKABE[1]), ("negative -> nearest other negative", neg_to_neg, OKABE[0])):
        ax.hist(np.where(v < 0, 0.7, v), bins=np.linspace(0.7, 1.0, 16), alpha=0.6, label=lab_, color=c, density=True)
    ax.set(xlabel="max identity (<0.8 shown at 0.7)", ylabel="density", title="Do negatives resemble positives more than other negatives?")
    ax.legend(frameon=False)
    _save(fig, "figF1_negative_resemblance")
    return df


# ------------------------------------------------------------- F2 motifs


def f2_motifs() -> pd.DataFrame:
    b = bench()
    seqs, y = b["sequence"].tolist(), b["label"].to_numpy()
    comp = np.array([[s.count(a) / len(s) for a in AA] for s in seqs])
    rows = []
    for j, a in enumerate(AA):
        x1, x0 = comp[y == 1, j], comp[y == 0, j]
        u = stats.mannwhitneyu(x1, x0, alternative="two-sided")
        rows.append({"feature": a, "kind": "residue", "mean_AIP": x1.mean(), "mean_nonAIP": x0.mean(),
                     "log2_ratio": float(np.log2((x1.mean() + 1e-9) / (x0.mean() + 1e-9))), "p_raw": u.pvalue})
    di = {a + b: [] for a, b in product(AA, AA)}
    for s in seqs:
        present = {s[i : i + 2] for i in range(len(s) - 1)}
        for d in di:
            di[d].append(d in present)
    for d, v in di.items():
        v = np.array(v)
        a1, a0 = int(v[y == 1].sum()), int(v[y == 0].sum())
        tab = [[a1, int((y == 1).sum()) - a1], [a0, int((y == 0).sum()) - a0]]
        _, p = stats.fisher_exact(tab)
        f1, f0 = a1 / (y == 1).sum(), a0 / (y == 0).sum()
        rows.append({"feature": d, "kind": "dipeptide(presence)", "mean_AIP": f1, "mean_nonAIP": f0,
                     "log2_ratio": float(np.log2((f1 + 1e-9) / (f0 + 1e-9))), "p_raw": p})
    df = pd.DataFrame(rows)
    df["p_bh"] = bh_adjust(df["p_raw"].to_numpy())
    # RF importance on AAC+length (same features as the best baseline)
    from sklearn.ensemble import RandomForestClassifier
    from src.features import combine
    X = combine(seqs, ("aac", "len"))
    rf = RandomForestClassifier(500, random_state=0, n_jobs=2, class_weight="balanced").fit(X, y)
    imp = dict(zip(list(AA) + ["length"], rf.feature_importances_))
    df["rf_importance"] = df["feature"].map(imp)
    res = df[df["kind"] == "residue"]
    rho, p = stats.spearmanr(res["log2_ratio"].abs(), res["rf_importance"])
    df.attrs["spearman"] = (rho, p)
    out = pd.concat([res.sort_values("p_raw"), df[df["kind"] != "residue"].sort_values("p_raw").head(25)])
    out["spearman_abs_log2ratio_vs_rf_importance"] = rho
    out.to_csv(TABLES / "TF2_motif_enrichment.csv", index=False)
    log.info("F2: spearman(|log2 ratio|, RF importance) over 20 residues = %.3f (p %.3g); length importance %.3f",
             rho, p, imp["length"])
    fig, ax = plt.subplots(figsize=(7, 3.8))
    r = res.sort_values("log2_ratio")
    ax.bar(r["feature"], r["log2_ratio"], color=[OKABE[1] if v > 0 else OKABE[0] for v in r["log2_ratio"]])
    ax.set(xlabel="residue", ylabel="log2(mean freq AIP / non-AIP)", title="Residue enrichment in AIPs")
    _save(fig, "figF2_residue_enrichment")
    return out


# ------------------------------------------------------- F3/F5 predictions

V1P = R / "predictions"
V2P = V2 / "predictions"


def pred_path(model: str, ts: str, rg: str):
    for d in (V2P, V1P):
        p = d / f"{model}_{ts}_{rg}.csv"
        if p.exists():
            return p
    return None


def model_list() -> dict[str, str]:
    """display name -> model file stem; models present on disk only."""
    cand = {"AAC+RF": "AAC_RF", "AAC+DPC+CTD+LGBM": "AAC_DPC_CTD_LGBM", "ESM2-650M LR": "esm2_t33_650M_LR",
            "ESM2-650M MLP (lam0)": "esm2_t33_650M_lam0_tau0.07", "ESM2-8M MLP (lam0)": "esm2_t6_8M_lam0_tau0.07",
            "ESM2-8M MLP (SupCon lam2)": "esm2_t6_8M_lam2_tau0.1", "fusion650 RF": "esm650_fusion__rf",
            "fusion650 LGBM": "esm650_fusion__lgbm", "attn-pool 650M MLP": "esm650_mean__mlp"}
    sel = V2 / "selected_v2.json"
    if sel.exists():
        for a, d in json.loads(sel.read_text()).items():
            cand[f"{a} (lam0)"] = f"{a}_esm2_t6_8M_lam0_tau0.07"
            cand[f"{a} (lam*={d['lambda_star']:g})"] = f"{a}_esm2_t6_8M_lam{d['lambda_star']:g}_tau0.07"
    return {k: v for k, v in cand.items() if pred_path(v, "ind_425", "B") is not None}


def load_regime_b() -> dict[str, pd.DataFrame]:
    out = {}
    for name, stem in model_list().items():
        frames = []
        for ts in ("ind_425", "ind_1049"):
            d = pd.read_csv(pred_path(stem, ts, "B"))
            d["test_set"] = ts
            frames.append(d)
        out[name] = pd.concat(frames, ignore_index=True)
    return out


def f3_errors(P: dict[str, pd.DataFrame]) -> pd.DataFrame:
    names = list(P)
    base = P[names[0]][["sequence", "y_true", "test_set"]].copy()
    wrong = np.stack([(P[n]["y_pred"].to_numpy() != P[n]["y_true"].to_numpy()) for n in names])
    base["n_models_wrong"] = wrong.sum(0)
    base["length"] = base["sequence"].str.len()
    train = bench()
    pos, neg = train[train.label == 1]["sequence"].tolist(), train[train.label == 0]["sequence"].tolist()
    seqs = base["sequence"].tolist()
    base["max_id_to_train_pos"] = max_identity_to_train(seqs, pos, floor=0.8)
    base["max_id_to_train_neg"] = max_identity_to_train(seqs, neg, floor=0.8)
    nn_lab = np.where(base["max_id_to_train_pos"] > base["max_id_to_train_neg"], 1, 0)
    base["nearest_train_label_agrees"] = nn_lab == base["y_true"]
    allwrong, allright = base["n_models_wrong"] == len(names), base["n_models_wrong"] == 0
    comp = pd.DataFrame([[s.count(a) / len(s) for a in AA] for s in seqs], columns=list(AA))
    rows = []
    for label, m in (("all models wrong", allwrong), ("all models right", allright), ("all sequences", np.ones(len(base), bool))):
        m = np.asarray(m)
        sub = base[m]
        r = {"group": label, "n": int(m.sum()), "mean_length": sub["length"].mean(),
             "frac_true_AIP": sub["y_true"].mean(), "mean_n_models_wrong": sub["n_models_wrong"].mean()}
        r.update({f"freq_{a}": comp[m][a].mean() for a in AA})
        rows.append(r)
    out = pd.DataFrame(rows)
    out["n_models"] = len(names)
    out.to_csv(TABLES / "TF3_error_analysis.csv", index=False)
    base[np.asarray(allwrong)].sort_values("length").to_csv(V2 / "hardest_sequences.csv", index=False)
    # which classes are the all-wrong sequences?
    summary = base.groupby("n_models_wrong").agg(n=("sequence", "size"), frac_AIP=("y_true", "mean"), mean_len=("length", "mean"),
                                                 nn_agree=("nearest_train_label_agrees", "mean")).reset_index()
    summary.to_csv(TABLES / "TF3b_errors_by_number_of_models_wrong.csv", index=False)
    return out


def f5_length(P: dict[str, pd.DataFrame]) -> pd.DataFrame:
    bins = [(7, 12), (13, 16), (17, 20), (21, 30)]
    rows = []
    for name, d in P.items():
        L = d["sequence"].str.len().to_numpy()
        for lo, hi in bins:
            m = (L >= lo) & (L <= hi)
            y, p, yp = d["y_true"].to_numpy()[m], d["y_prob"].to_numpy()[m], d["y_pred"].to_numpy()[m]
            ok = len(np.unique(y)) == 2 and m.sum() >= 30
            rows.append({"model": name, "length_bin": f"{lo}-{hi}", "n": int(m.sum()), "frac_AIP": float(y.mean()) if m.sum() else np.nan,
                         "auroc": float(roc_auc_score(y, p)) if ok else np.nan, "mcc": float(matthews_corrcoef(y, yp)) if ok else np.nan})
    # length-only baseline: logistic regression on length (+ squared) fit on benchmark, scored on Regime B
    from sklearn.linear_model import LogisticRegression
    b = bench()
    f = lambda s: np.c_[s.str.len(), s.str.len() ** 2]
    lr = LogisticRegression(max_iter=1000).fit(f(b["sequence"]), b["label"])
    ref = next(iter(P.values()))
    pl = lr.predict_proba(f(ref["sequence"]))[:, 1]
    L = ref["sequence"].str.len().to_numpy()
    for lo, hi in bins:
        m = (L >= lo) & (L <= hi)
        y = ref["y_true"].to_numpy()[m]
        ok = len(np.unique(y)) == 2 and m.sum() >= 30
        rows.append({"model": "length-only logistic baseline", "length_bin": f"{lo}-{hi}", "n": int(m.sum()), "frac_AIP": float(y.mean()),
                     "auroc": float(roc_auc_score(y, pl[m])) if ok else np.nan, "mcc": np.nan})
    rows.append({"model": "length-only logistic baseline", "length_bin": "all", "n": len(ref), "frac_AIP": float(ref["y_true"].mean()),
                 "auroc": float(roc_auc_score(ref["y_true"], pl)), "mcc": np.nan})
    df = pd.DataFrame(rows)
    df.to_csv(TABLES / "TF5_length_stratified.csv", index=False)
    piv = df[df.model != "length-only logistic baseline"].pivot(index="model", columns="length_bin", values="auroc")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    w = 0.8 / max(len(piv), 1)
    for i, (m_, r) in enumerate(piv.iterrows()):
        ax.bar(np.arange(len(r)) + i * w, r.values, w, label=m_)
    ax.axhline(0.5, color="grey", ls=":")
    ax.set_xticks(np.arange(len(piv.columns)) + 0.4, piv.columns)
    ax.set(xlabel="peptide length", ylabel="AUROC (Regime B, both test sets pooled)", title="Performance by peptide length")
    ax.legend(frameon=False, fontsize=6, ncol=2)
    _save(fig, "figF5_length_stratified")
    return df


def run() -> int:
    t0 = time.time()
    TABLES.mkdir(exist_ok=True)
    f1_negatives()
    f2_motifs()
    P = load_regime_b()
    log.info("F3/F5 models available: %s", list(P))
    f3_errors(P)
    f5_length(P)
    mark("F_analysis", "complete", time.time() - t0, f"{len(P)} models")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
