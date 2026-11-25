"""Build results/thesis/ch5_data.json: every number and table quoted in Chapters 4-6, computed from results/ (no hand-typed values)."""
from __future__ import annotations

import json
import re

import numpy as np
import pandas as pd

from src.utils import ROOT

R = ROOT / "results"
V2 = R / "v2"
TB = R / "tables"
MET = ["accuracy", "sensitivity", "specificity", "precision", "f1", "mcc", "auroc", "auprc"]
n0 = lambda x: f"{int(round(float(x))):,}"
f3 = lambda x: f"{float(x):.3f}"
f4 = lambda x: f"{float(x):.4f}"


def ms(g, k=4):
    return f"{g.mean():.{k}f} ± {g.std(ddof=1):.{k}f}" if len(g) > 1 else f"{g.mean():.{k}f}"


def unified() -> pd.DataFrame:
    sel1 = json.loads((R / "selected_models.json").read_text())
    sel2 = json.loads((V2 / "selected_v2.json").read_text())
    frames = []

    def add(df, mid, disp, group):
        d = df.copy()
        d["mid"], d["disp"], d["group"] = mid, disp, group
        frames.append(d[["mid", "disp", "group", "eval_set", "regime", "seed", "fold"] + MET])

    base = pd.read_csv(R / "baseline_results.csv")
    for m, disp, grp in (("AAC_SVM", "AAC + SVM", "Composition-based classical"), ("AAC_RF", "AAC + random forest", "Composition-based classical"),
                         ("AAC_DPC_CTD_LGBM", "AAC+DPC+CTD + LightGBM", "Composition-based classical"),
                         ("esm2_t6_8M_LR", "ESM-2 8M + logistic regression", "Frozen ESM-2, linear"), ("esm2_t12_35M_LR", "ESM-2 35M + logistic regression", "Frozen ESM-2, linear"),
                         ("esm2_t30_150M_LR", "ESM-2 150M + logistic regression", "Frozen ESM-2, linear")):
        add(base[base.model == m], m, disp, grp)
    cv1 = pd.read_csv(R / "cv_results.csv")
    cv1 = cv1[cv1.family == "deep"]
    fin1 = pd.read_csv(R / "final_results.csv")
    size = {"esm2_t6_8M": "8M", "esm2_t12_35M": "35M", "esm2_t30_150M": "150M", "esm2_t33_650M": "650M"}
    for name, d in sel1.items():
        ck, lam, tau, role = d["checkpoint"], d["lambda"], d["tau"], d["role"]
        if role == "sweep":
            continue
        disp = f"ESM-2 {size[ck]} MLP, λ=0" if role == "baseline" else f"ESM-2 {size[ck]} MLP + SupCon (λ={lam:g}, τ={tau:g})"
        add(pd.concat([cv1[cv1.model == name], fin1[fin1.model == name]]), name, disp, "Frozen ESM-2, MLP (mean-pooled)")
    # B1 at tau 0.07 (the architecture-comparison reference)
    for name, disp in (("esm2_t6_8M_lam0_tau0.07", "B1 MLP, λ=0"), ("esm2_t6_8M_lam2_tau0.07", "B1 MLP, λ=2")):
        add(pd.concat([cv1[cv1.model == name], fin1[fin1.model == name]]), name + "#B1", disp, "Phase B architectures (frozen 8M residues)")
    cv2 = pd.read_csv(V2 / "cv_results_v2.csv")
    fin2 = pd.read_csv(V2 / "final_results_v2.csv")
    an = {"B2_cnn": "B2 CNN", "B3_bilstm": "B3 BiLSTM", "B4_cnn_bilstm": "B4 CNN-BiLSTM", "B5_transformer": "B5 Transformer", "B6_attnpool": "B6 attention pooling"}
    for a, d in sel2.items():
        for lam in (0.0, d["lambda_star"]):
            sub = lambda x: x[(x.arch == a) & (x.lambda_supcon == lam)]
            add(pd.concat([sub(cv2), sub(fin2)]), f"{a}_lam{lam:g}", f"{an[a]}, λ={lam:g}", "Phase B architectures (frozen 8M residues)")
    rep = pd.read_csv(V2 / "repr_results_v2.csv")
    nm = {"esm650_mean|mlp": ("650M mean pooling + MLP", "Pooling variants (frozen 650M, MLP)"), "esm650_max|mlp": ("650M max pooling + MLP", "Pooling variants (frozen 650M, MLP)"),
          "esm650_meanmax|mlp": ("650M mean||max pooling + MLP", "Pooling variants (frozen 650M, MLP)"), "esm650_cls|mlp": ("650M CLS token + MLP", "Pooling variants (frozen 650M, MLP)"),
          "esm650_firstlast|mlp": ("650M first/last-3 + MLP", "Pooling variants (frozen 650M, MLP)"), "esm650_attention|attn_mlp": ("650M attention pooling + MLP", "Pooling variants (frozen 650M, MLP)")}
    for c in ("rf", "lgbm", "mlp"):
        cn = {"rf": "random forest", "lgbm": "LightGBM", "mlp": "MLP"}[c]
        nm[f"hand|{c}"] = (f"Hand-crafted + {cn}", "Fusion study (hand-crafted, ESM-2, fusion)")
        for sh, lab in (("esm8", "8M"), ("esm650", "650M")):
            nm[f"{sh}_mean|{c}"] = (f"ESM-2 {lab} mean-pooled + {cn}", "Fusion study (hand-crafted, ESM-2, fusion)")
            nm[f"{sh}_fusion|{c}"] = (f"Fusion {lab} + {cn}", "Fusion study (hand-crafted, ESM-2, fusion)")
    nm["esm650_mean|mlp"] = (nm["esm650_mean|mlp"][0], "Pooling variants (frozen 650M, MLP)")  # shared by C1 and C2; listed once, under pooling
    for m, (disp, grp) in nm.items():
        add(rep[rep.model == m], m, disp, grp)
    ft = pd.read_csv(V2 / "finetune_results_v2.csv")
    add(ft[ft["mode"] == "finetune"], "esm2_t6_8M_finetune", "ESM-2 8M fine-tuned", "Fine-tuning (8M)")
    add(ft[ft["mode"] == "frozen"], "esm2_t6_8M_frozen", "ESM-2 8M frozen (same head)", "Fine-tuning (8M)")
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    U = unified()
    F: dict = {}
    T: dict = {}
    order = list(dict.fromkeys(U.mid))
    disp = dict(zip(U.mid, U.disp))
    group = dict(zip(U.mid, U.group))

    # ---- 5.1 CV
    cv = U[U.eval_set == "cv"]
    rows = [["Model", "Runs", "Accuracy", "MCC", "AUROC", "AUPRC", "F1"]]
    shade = []
    last = None
    for m in order:
        g = cv[cv.mid == m]
        if not len(g) or m.endswith("#B1") and False:
            continue
        if group[m] != last:
            rows.append([f"<b>{group[m]}</b>", "", "", "", "", "", ""])
            shade.append(len(rows) - 1)
            last = group[m]
        rows.append([disp[m], str(len(g)), ms(g.accuracy, 3), ms(g.mcc, 3), ms(g.auroc, 3), ms(g.auprc, 3), ms(g.f1, 3)])
    T["cv"] = rows
    T["cv_shade"] = shade
    F["cv_mean"] = {m: {"mcc": float(cv[cv.mid == m].mcc.mean()), "auroc": float(cv[cv.mid == m].auroc.mean()), "n": int(len(cv[cv.mid == m]))} for m in order if len(cv[cv.mid == m])}

    # ---- 5.2/5.3 independent sets
    ind = U[U.eval_set.isin(["ind_425", "ind_1049"])]
    mean = ind.groupby(["mid", "eval_set", "regime"])[["mcc", "auroc", "accuracy", "f1"]].mean()
    sd = ind.groupby(["mid", "eval_set", "regime"])[["mcc", "auroc"]].std()
    F["ind"] = {}
    for ts in ("ind_425", "ind_1049"):
        rows = [["Model", "MCC A", "MCC B", "MCC C", "AUROC A", "AUROC B", "AUROC C"]]
        shade, last = [], None
        for m in order:
            if (m, ts, "A") not in mean.index:
                continue
            if group[m] != last:
                rows.append([f"<b>{group[m]}</b>", "", "", "", "", "", ""])
                shade.append(len(rows) - 1)
                last = group[m]
            r = [disp[m]]
            for k in ("mcc", "auroc"):
                for rg in ("A", "B", "C"):
                    r.append(f"{mean.loc[(m, ts, rg), k]:.3f}")
            rows.append(r)
            F["ind"].setdefault(m, {})[ts] = {rg: {"mcc": float(mean.loc[(m, ts, rg), "mcc"]), "auroc": float(mean.loc[(m, ts, rg), "auroc"]),
                                                   "mcc_sd": float(sd.loc[(m, ts, rg), "mcc"]), "auroc_sd": float(sd.loc[(m, ts, rg), "auroc"])} for rg in ("A", "B", "C")}
        T[f"ind_{ts}"] = rows
        T[f"ind_{ts}_shade"] = shade

    # ---- 5.4 leakage gaps
    gap_rows = [["Model", "Ind_425 MCC A−B", "Ind_425 AUROC A−B", "Ind_1049 MCC A−B", "Ind_1049 AUROC A−B", "Ind_425 MCC A−C", "Ind_1049 MCC A−C"]]
    gaps = {}
    for m in order:
        if m not in F["ind"] or "ind_425" not in F["ind"][m]:
            continue
        a, b = F["ind"][m]["ind_425"], F["ind"][m]["ind_1049"]
        g = {"m425": a["A"]["mcc"] - a["B"]["mcc"], "a425": a["A"]["auroc"] - a["B"]["auroc"], "m1049": b["A"]["mcc"] - b["B"]["mcc"], "a1049": b["A"]["auroc"] - b["B"]["auroc"],
             "mC425": a["A"]["mcc"] - a["C"]["mcc"], "mC1049": b["A"]["mcc"] - b["C"]["mcc"]}
        gaps[m] = g
    F["gaps"] = gaps
    keyg = ["AAC_RF", "AAC_SVM", "AAC_DPC_CTD_LGBM", "esm2_t6_8M_LR", "esm2_t30_150M_LR", "esm2_t6_8M_lam0_tau0.07", "esm2_t33_650M_lam0_tau0.07", "esm2_t6_8M_finetune", "esm2_t6_8M_frozen",
            "B2_cnn_lam0", "B3_bilstm_lam0", "B4_cnn_bilstm_lam0", "B5_transformer_lam0", "B6_attnpool_lam0", "hand|rf", "esm650_fusion|rf"]
    for m in keyg:
        if m in gaps:
            g = gaps[m]
            gap_rows.append([disp[m], f3(g["m425"]), f3(g["a425"]), f3(g["m1049"]), f3(g["a1049"]), f3(g["mC425"]), f3(g["mC1049"])])
    T["gaps"] = gap_rows
    gg = pd.DataFrame(gaps).T
    gg["group"] = [group[m] for m in gg.index]
    F["gap_by_group"] = {k: {c: float(v[c].mean()) for c in ("m425", "m1049", "a425", "a1049")} | {"n": int(len(v))} for k, v in gg.groupby("group")}
    F["gap_range_mcc"] = {"min": float(gg[["m425", "m1049"]].min().min()), "max": float(gg[["m425", "m1049"]].max().max())}

    # cross-benchmark matrix
    xb = pd.read_csv(V2 / "cross_benchmark_results_v2.csv")
    g = xb.groupby(["train_set", "test_set", "regime", "model"]).agg(n_eval=("n_eval", "first"), mcc=("mcc", "mean"), auroc=("auroc", "mean")).reset_index()
    F["xb"] = {}
    rows = [["Training set", "Independent set", "n (A)", "n (B)", "AAC+RF MCC A", "AAC+RF MCC B", "ESM-2 650M MLP MCC A", "ESM-2 650M MLP MCC B"]]
    for tr in ("AIPpred_benchmark", "AntiInflam_training", "local_Benchmark_clean"):
        for te in ("AIPpred_independent", "AntiInflam_validation"):
            q = lambda m, rg, c="mcc": float(g[(g.train_set == tr) & (g.test_set == te) & (g.model == m) & (g.regime == rg)][c].iloc[0])
            nA = int(g[(g.train_set == tr) & (g.test_set == te) & (g.model == "AAC+RF") & (g.regime == "A")].n_eval.iloc[0])
            nB = int(g[(g.train_set == tr) & (g.test_set == te) & (g.model == "AAC+RF") & (g.regime == "B")].n_eval.iloc[0])
            rows.append([tr.replace("_", " "), te.replace("_", " "), n0(nA), n0(nB), f3(q("AAC+RF", "A")), f3(q("AAC+RF", "B")), f3(q("ESM2-650M MLP lam0", "A")), f3(q("ESM2-650M MLP lam0", "B"))])
            F["xb"][f"{tr}|{te}"] = {"nA": nA, "nB": nB, "rf_A": q("AAC+RF", "A"), "rf_B": q("AAC+RF", "B"), "esm_A": q("ESM2-650M MLP lam0", "A"), "esm_B": q("ESM2-650M MLP lam0", "B")}
    T["xb"] = rows

    # ---- 5.5 lambda sweep
    cv1 = pd.read_csv(R / "cv_results.csv")
    cv1 = cv1[(cv1.family == "deep") & (cv1.checkpoint == "esm2_t6_8M") & (cv1.temperature == 0.07)]
    fin1 = pd.read_csv(R / "final_results.csv")
    fin1 = fin1[(fin1.checkpoint == "esm2_t6_8M") & (fin1.temperature == 0.07) & (fin1.regime == "B")]
    rows = [["λ", "CV MCC", "CV AUROC", "Ind_425 MCC (Regime B)", "Ind_1049 MCC (Regime B)"]]
    F["lam"] = {}
    for lam, g in cv1.groupby("lambda_supcon"):
        f = fin1[fin1.lambda_supcon == lam]
        a, b = f[f.eval_set == "ind_425"].mcc.mean(), f[f.eval_set == "ind_1049"].mcc.mean()
        rows.append([f"{lam:g}", ms(g.mcc, 4), ms(g.auroc, 4), f"{a:.3f}", f"{b:.3f}"])
        F["lam"][f"{lam:g}"] = {"cv_mcc": float(g.mcc.mean()), "cv_sd": float(g.mcc.std()), "cv_auroc": float(g.auroc.mean()), "b425": float(a), "b1049": float(b)}
    T["lambda"] = rows
    t55 = pd.read_csv(TB / "T5_5_checkpoint_ablation.csv")
    rows = [["Checkpoint", "Best λ", "CV MCC, λ=0", "CV MCC, best λ", "Difference", "Regime B MCC Ind_425: λ=0 / best", "Regime B MCC Ind_1049: λ=0 / best"]]
    for r in t55.itertuples():
        rows.append([r.checkpoint.replace("esm2_", "ESM-2 "), f"{r.best_lambda:g}", r.CV_MCC_lambda0, r.CV_MCC_best, f"{r.CV_MCC_diff:+.4f}",
                     f"{r.RegimeB_MCC_ind_425_baseline:.3f} / {r.RegimeB_MCC_ind_425_best:.3f}", f"{r.RegimeB_MCC_ind_1049_baseline:.3f} / {r.RegimeB_MCC_ind_1049_best:.3f}"])
    T["checkpoints"] = rows
    t55b = pd.read_csv(TB / "T5_5b_temperature_sweep.csv")
    rows = [["Checkpoint", "λ", "τ", "CV MCC", "CV AUROC"]]
    for r in t55b.itertuples():
        rows.append([r.checkpoint.replace("esm2_", "ESM-2 "), f"{r.lambda_supcon:g}", f"{r.temperature:g}", r.mcc, r.auroc])
    T["tau"] = rows

    # architectures
    t58 = pd.read_csv(TB / "T5.8_architecture_comparison.csv")
    comp = pd.read_csv(TB / "T5.11_corrected_significance.csv")
    rows = [["Architecture", "λ*", "CV MCC, λ=0", "CV MCC, λ*", "Ind_425 ΔMCC [95% CI]", "Ind_425 raw p", "Ind_425 BH p", "Ind_1049 ΔMCC [95% CI]", "Ind_1049 raw p", "Ind_1049 BH p"]]
    h2 = comp[(comp.regime == "B") & comp.family.isin(["H2 architectures (Regime B)", "lambda contrast: Phase B"]) & comp.comparison.str.contains("lambda")]
    an = {"B1_mlp": "B1 MLP", "B2_cnn": "B2 CNN", "B3_bilstm": "B3 BiLSTM", "B4_cnn_bilstm": "B4 CNN-BiLSTM", "B5_transformer": "B5 Transformer", "B6_attnpool": "B6 attention pooling"}
    F["h2"] = {}
    for r in t58.itertuples():
        out = [an[r.architecture], f"{r.lambda_star:g}", r.CV_MCC_lambda0.split(" ±")[0], r.CV_MCC_lambda_star.split(" ±")[0]]
        for ts in ("ind_425", "ind_1049"):
            lab = "B1_mlp (v1 MLP, tau 0.07) lambda=2 vs 0" if r.architecture == "B1_mlp" else f"{r.architecture} lambda*={r.lambda_star:g} vs 0"
            q = h2[(h2.comparison == lab) & (h2.test_set == ts)].iloc[0]
            out += [f"{q.mcc_diff:+.3f} [{q.mcc_diff_lo:+.3f}, {q.mcc_diff_hi:+.3f}]", f"{q.delong_p:.3f}", f"{q.p_delong_bh_family:.3f}"]
            F["h2"][f"{r.architecture}|{ts}"] = {"dmcc": float(q.mcc_diff), "lo": float(q.mcc_diff_lo), "hi": float(q.mcc_diff_hi), "p": float(q.delong_p), "bh": float(q.p_delong_bh_family),
                                                 "dauroc": float(q.auroc_diff), "mde_mcc": float(q.mcc_mde80), "mde_auc": float(q.auroc_mde80), "support": bool(q.supports_claim_rule)}
        rows.append(out)
    T["arch"] = rows
    fam = comp.groupby("family").agg(n=("n", "size"), raw=("significant_raw_delong_0.05", "sum"), fam=("significant_after_family_BH", "sum"), glob=("significant_after_global_BH", "sum")).reset_index()
    T["families"] = [["Family of comparisons", "Tests", "Raw p < 0.05", "Significant after BH (within family)", "Significant after BH (all tests)"]] + \
        [[r.family, str(r.n), str(r.raw), str(r.fam), str(r.glob)] for r in fam.itertuples()]
    F["fam"] = {r.family: {"n": int(r.n), "raw": int(r.raw), "fam": int(r.fam), "glob": int(r.glob)} for r in fam.itertuples()}
    F["n_tests"] = int(len(comp))
    lam_fams = ["H1 primary (v1)", "H2 architectures (Regime B)", "lambda contrast: Phase B", "lambda contrast: Phase B other regimes", "lambda contrast: checkpoints (v1)"]
    lc = comp[comp.family.isin(lam_fams)]
    F["lamtests"] = {"n": int(len(lc)), "raw": int(lc["significant_raw_delong_0.05"].sum()), "fam": int(lc.significant_after_family_BH.sum()), "glob": int(lc.significant_after_global_BH.sum())}
    sur = lc[lc.significant_after_family_BH | lc.significant_after_global_BH]
    F["lam_survivors"] = [{"comparison": r.comparison, "test_set": r.test_set, "regime": r.regime, "dauroc": float(r.auroc_diff), "dmcc": float(r.mcc_diff), "bh_fam": float(r.p_delong_bh_family), "bh_glob": float(r.p_delong_bh_global_all)} for r in sur.itertuples()]
    xbc = comp[comp.family.str.contains("cross-benchmark")]
    F["xb_tests"] = {"n": int(len(xbc)), "raw": int(xbc["significant_raw_delong_0.05"].sum()), "fam": int(xbc.significant_after_family_BH.sum()), "pos": int((xbc.mcc_diff > 0).sum()),
                     "min": float(xbc.mcc_diff.min()), "max": float(xbc.mcc_diff.max())}
    h1 = comp[comp.family == "H1 primary (v1)"]
    F["h1"] = {r.test_set: {"dmcc": float(r.mcc_diff), "lo": float(r.mcc_diff_lo), "hi": float(r.mcc_diff_hi), "dauroc": float(r.auroc_diff), "alo": float(r.auroc_diff_lo), "ahi": float(r.auroc_diff_hi),
                            "p": float(r.delong_p), "pm": float(r.mcnemar_p), "n": int(r.n), "mde": float(r.mcc_mde80), "mde_auc": float(r.auroc_mde80)} for r in h1.itertuples()}
    # per-seed variation
    ps = pd.read_csv(TB / "T5.11b_seed_vs_sample_variance.csv")
    F["seed_sd_range"] = [float(ps.sd_across_seeds_mcc_diff.min()), float(ps.sd_across_seeds_mcc_diff.max())]
    # nested CV
    nc = pd.read_csv(V2 / "nested_cv_8M.csv")
    d = nc.outer_mcc_selected - nc.outer_mcc_lambda0
    F["nested"] = {"n": int(len(nc)), "lam0": float(nc.outer_mcc_lambda0.mean()), "sel": float(nc.outer_mcc_selected.mean()), "diff": float(d.mean()), "sd": float(d.std()),
                   "lo": float(d.mean() - 1.96 * d.std() / np.sqrt(len(d))), "hi": float(d.mean() + 1.96 * d.std() / np.sqrt(len(d))), "dz": float(d.mean() / d.std()),
                   "sel_counts": {f"{k:g}": int(v) for k, v in nc.selected_lambda.value_counts().sort_index().items()}}
    cvs = pd.read_csv(TB / "T5.11c_cv_effect_sizes.csv")
    F["cv_effect"] = {r.comparison: {"diff": float(r.mean_cv_mcc_diff), "dz": float(r.cohens_dz)} for r in cvs.itertuples()}
    F["cv_lam2_positive"] = int((cvs[cvs.comparison.str.contains("lambda=2 vs 0")].mean_cv_mcc_diff > 0).sum())
    F["cv_lam2_total"] = int(cvs.comparison.str.contains("lambda=2 vs 0").sum())

    # ---- 5.6 representation
    def rowfor(mids, title_cols=True):
        rows = [["Model", "CV MCC", "CV AUROC", "Ind_425 MCC B", "Ind_1049 MCC B", "Ind_425 AUROC B", "Ind_1049 AUROC B"]]
        for m in mids:
            c = cv[cv.mid == m]
            r = [disp[m], ms(c.mcc, 3).split(" ±")[0], ms(c.auroc, 3).split(" ±")[0]]
            for k in ("mcc", "auroc"):
                for ts in ("ind_425", "ind_1049"):
                    r.append(f"{F['ind'][m][ts]['B'][k]:.3f}" if m in F["ind"] else "")
            rows.append(r)
        return rows
    pool_m = ["esm2_t33_650M_lam0_tau0.07"] + ["esm650_mean|mlp", "esm650_max|mlp", "esm650_meanmax|mlp", "esm650_cls|mlp", "esm650_firstlast|mlp", "esm650_attention|attn_mlp"]
    T["pooling"] = rowfor(pool_m[1:] + ["AAC_RF"])
    fus_m = ["AAC_RF"] + [f"hand|{c}" for c in ("rf", "lgbm", "mlp")] + [f"{s}_mean|{c}" for s in ("esm8", "esm650") for c in ("rf", "lgbm", "mlp")] + [f"{s}_fusion|{c}" for s in ("esm8", "esm650") for c in ("rf", "lgbm", "mlp")]
    T["fusion"] = rowfor(fus_m)
    ft_m = ["esm2_t6_8M_frozen", "esm2_t6_8M_finetune", "esm2_t6_8M_lam0_tau0.07", "esm2_t33_650M_lam0_tau0.07", "B5_transformer_lam0", "AAC_RF"]
    T["finetune"] = rowfor(ft_m)
    F["ft_cv"] = {m: {"mcc": float(cv[cv.mid == m].mcc.mean()), "auroc": float(cv[cv.mid == m].auroc.mean()), "n": int(len(cv[cv.mid == m]))} for m in ft_m}
    F["pool_cv"] = {m: float(cv[cv.mid == m].mcc.mean()) for m in pool_m[1:] + ["AAC_RF"]}
    F["fus_cv"] = {m: {"mcc": float(cv[cv.mid == m].mcc.mean()), "auroc": float(cv[cv.mid == m].auroc.mean())} for m in fus_m}
    reps = comp[comp.family.str.startswith("representation") & (comp.regime == "B")]
    F["rep"] = {f"{r.comparison}|{r.test_set}": {"dmcc": float(r.mcc_diff), "lo": float(r.mcc_diff_lo), "hi": float(r.mcc_diff_hi), "dauroc": float(r.auroc_diff), "p": float(r.delong_p),
                                                 "bh": float(r.p_delong_bh_family), "bhg": float(r.p_delong_bh_global_all)} for r in reps.itertuples()}
    rr = [["Comparison", "Test set", "ΔMCC [95% CI]", "ΔAUROC", "Raw p", "BH p (family)"]]
    sel_c = reps[reps.comparison.str.contains("fine-tuned|vs mean pooling|fusion vs hand|ESM vs|650M MLP lambda=0 vs AAC|8M MLP lambda=0 vs AAC")]
    for r in sel_c.itertuples():
        rr.append([r.comparison, r.test_set.replace("ind_", "Ind_"), f"{r.mcc_diff:+.3f} [{r.mcc_diff_lo:+.3f}, {r.mcc_diff_hi:+.3f}]", f"{r.auroc_diff:+.3f}", f"{r.delong_p:.4f}", f"{r.p_delong_bh_family:.4f}"])
    T["rep_tests"] = rr

    # ---- Phase F facts
    tf1 = pd.read_csv(TB / "TF1_negatives_fragment_test.csv")
    F["tf1"] = {r.comparison: float(r.value_or_fraction_ge_0_9) if hasattr(r, "value_or_fraction_ge_0_9") else None for r in tf1.itertuples()} if False else \
        {row["comparison"]: float(row["value_or_fraction_ge_0.9"]) for _, row in tf1.iterrows()}
    tf5 = pd.read_csv(TB / "TF5_length_stratified.csv")
    F["len_only_auroc"] = float(tf5[(tf5.model == "length-only logistic baseline") & (tf5.length_bin == "all")].auroc.iloc[0])
    pv = tf5[tf5.model == "AAC+RF"].set_index("length_bin")
    F["len_rf"] = {k: {"n": int(pv.loc[k, "n"]), "auroc": float(pv.loc[k, "auroc"])} for k in pv.index}
    tf3 = pd.read_csv(TB / "TF3b_errors_by_number_of_models_wrong.csv")
    F["all_wrong"] = {"n": int(tf3.iloc[-1].n), "frac_aip": float(tf3.iloc[-1].frac_AIP), "none_wrong": int(tf3.iloc[0].n), "total": int(tf3.n.sum()), "n_models": int(tf3.n_models_wrong.max())}
    mot = pd.read_csv(TB / "TF2_motif_enrichment.csv")
    res = mot[mot.kind == "residue"].sort_values("p_raw")
    F["motif"] = {"top": [{"aa": r.feature, "log2": float(r.log2_ratio), "bh": float(r.p_bh)} for r in res.head(6).itertuples()],
                  "spearman": float(mot.spearman_abs_log2ratio_vs_rf_importance.iloc[0]), "n_residue_sig": int((res.p_bh < 0.05).sum())}

    # ---- MDE table
    mde = pd.read_csv(V2 / "mde_summary.csv")
    T["mde"] = [["Test set", "Regime", "Sequences", "MDE of MCC: median [min, max]", "MDE of AUROC: median"]] + \
        [[r.test_set.replace("ind_", "Ind_"), r.regime, n0(r.n), f"{r.mde_mcc_median:.3f} [{r.mde_mcc_min:.3f}, {r.mde_mcc_max:.3f}]", f"{r.mde_auroc_median:.3f}"] for r in mde.itertuples()]
    F["mde"] = {f"{r.test_set}|{r.regime}": {"n": int(r.n), "mcc": float(r.mde_mcc_median), "auroc": float(r.mde_auroc_median)} for r in mde.itertuples()}

    # ---- chapter 4 facts
    env = pd.read_csv(V2 / "environment.csv")
    F["env"] = dict(zip(env["item"], env["value"]))
    stages = {}
    for f in sorted((R / ".stages").glob("*.json")):
        d = json.loads(f.read_text())
        stages[d["stage"]] = {"status": d["status"], "secs": d["wall_seconds"], "notes": d.get("notes", "")}
    F["stages"] = stages
    F["device_map"] = json.loads((V2 / "device_map.json").read_text())
    F["selected_v2"] = json.loads((V2 / "selected_v2.json").read_text())
    F["selected_v1"] = {k: v for k, v in json.loads((R / "selected_models.json").read_text()).items() if v["role"] != "sweep"}
    F["prereg_commit"] = (ROOT / "PREREG_COMMIT.txt").read_text().split(" committed in ")[1].split(" at ")[0]
    F["prereg_time"] = (ROOT / "PREREG_COMMIT.txt").read_text().split(" at ")[1].split(" ")[0]
    ft_t = pd.read_csv(V2 / "finetune_results_v2.csv")
    F["ft_seconds"] = {m: float(g.train_seconds.mean()) for m, g in ft_t.groupby("mode")}
    cvv2 = pd.read_csv(V2 / "cv_results_v2.csv")
    F["b_seconds"] = {a: float(g.train_seconds.mean()) for a, g in cvv2.groupby("arch")}
    # embedding timings
    et = pd.read_csv(R / "embedding_timings.csv")
    F["emb"] = et.astype(object).where(et.notna(), None).to_dict("records")
    # Kaggle kernel run times (from the kernel logs) and the local Python version, saved as a results file for traceability
    import glob, sys
    krows = []
    for f in glob.glob(str(ROOT / "data" / "external" / "kaggle_*_out" / "*.log")):
        t = open(f).read()
        try:
            t = "".join(e.get("data", "") for e in json.loads(t))
        except Exception:
            pass
        for mm in re.finditer(r"\[(\d+)s\] (RUN|DONE) ?(.*)", t):
            krows.append({"kernel": f.split("/")[-1].replace(".log", ""), "elapsed_seconds": int(mm.group(1)), "event": mm.group(2), "detail": mm.group(3)[:120]})
    kdf = pd.DataFrame(krows)
    kdf.to_csv(V2 / "kaggle_runtimes.csv", index=False)
    F["kaggle"] = {k: int(g[g.event == "DONE"].elapsed_seconds.iloc[0]) for k, g in kdf.groupby("kernel") if (g.event == "DONE").any()}
    F["kaggle_b_cv_s"] = int(kdf[(kdf.kernel == "aip-phase-b-gpu") & (kdf.event == "RUN") & kdf.detail.str.contains("final")].elapsed_seconds.iloc[0])
    F["python"] = sys.version.split()[0]
    F["requirements"] = dict(l.split("==") for l in (ROOT / "requirements.txt").read_text().split() if "==" in l)
    (R / "thesis" / "ch5_data.json").write_text(json.dumps({"F": F, "T": T}, indent=1, default=str))
    print("wrote ch5_data.json;", len(order), "models;", list(T))


if __name__ == "__main__":
    main()
