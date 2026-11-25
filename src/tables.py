"""Build every thesis table from results/*.csv into results/tables/ as CSV and LaTeX."""
from __future__ import annotations

import json
import traceback

import numpy as np
import pandas as pd

from src.evaluate import METRIC_NAMES
from src.utils import ROOT, Timer, append_note, mark_stage, setup_logging

log = setup_logging("tables")
R = ROOT / "results"
T = R / "tables"
HEAD = "esm2_t6_8M"
DEEP_COLS = METRIC_NAMES


def _tex_escape(s) -> str:
    return str(s).replace("\\", "\\textbackslash{}").replace("_", "\\_").replace("%", "\\%").replace("&", "\\&") \
        .replace("±", "$\\pm$")


def save(df: pd.DataFrame, name: str, caption: str) -> None:
    T.mkdir(parents=True, exist_ok=True)
    df.to_csv(T / f"{name}.csv", index=False)
    cols = "l" * len(df.columns)
    lines = ["\\begin{table}[ht]", "\\centering\\small", f"\\caption{{{_tex_escape(caption)}}}",
             f"\\label{{tab:{name}}}", f"\\begin{{tabular}}{{{cols}}}", "\\hline",
             " & ".join(_tex_escape(c) for c in df.columns) + " \\\\", "\\hline"]
    for _, r in df.iterrows():
        lines.append(" & ".join("" if (isinstance(v, float) and np.isnan(v)) else _tex_escape(v) for v in r) + " \\\\")
    lines += ["\\hline", "\\end{tabular}", "\\end{table}"]
    (T / f"{name}.tex").write_text("\n".join(lines) + "\n")
    log.info("table %s written (%d rows)", name, len(df))


def ms(g: pd.Series) -> str:
    return f"{g.mean():.4f} ± {g.std(ddof=1):.4f}" if len(g) > 1 else f"{g.mean():.4f}"


def agg(df: pd.DataFrame, keys: list[str], metrics=DEEP_COLS) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby(keys, sort=False):
        k = k if isinstance(k, tuple) else (k,)
        r = dict(zip(keys, k))
        r["n_runs"] = len(g)
        for m in metrics:
            r[m] = ms(g[m])
        rows.append(r)
    return pd.DataFrame(rows)


def _load_all_models() -> pd.DataFrame:
    frames = [pd.read_csv(R / f) for f in ("cv_results.csv", "baseline_results.csv", "final_results.csv") if (R / f).exists()]
    return pd.concat(frames, ignore_index=True)


def display_name(model: str, sel: dict) -> str:
    fixed = {"AAC_SVM": "AAC + SVM", "AAC_RF": "AAC + RF", "AAC_DPC_CTD_LGBM": "AAC+DPC+CTD + LightGBM"}
    if model in fixed:
        return fixed[model]
    if model.endswith("_LR"):
        return f"{model[:-3].replace('esm2_', 'ESM-2 ')} + LogReg"
    d = sel.get(model)
    ck = model.split("_lam")[0].replace("esm2_", "ESM-2 ")
    lam = float(model.split("_lam")[1].split("_")[0])
    return f"{ck} + MLP (lambda=0)" if lam == 0 else f"{ck} + SupCon (lambda={lam:g}, tau={model.split('_tau')[1]})"


def t3_tables() -> None:
    a = pd.read_csv(R / "data_audit.csv")
    ds = a[a["section"] == "dataset"].pivot(index="subject", columns="metric", values="value").reset_index()
    cols = ["subject", "n", "n_positive", "n_negative", "pos_rate", "len_min", "len_max", "len_mean", "n_unique_sequences"]
    t31 = ds[cols].copy()
    t31["pos_rate"] = t31["pos_rate"].astype(float).round(3)
    t31["len_mean"] = t31["len_mean"].astype(float).round(2)
    save(t31.rename(columns={"subject": "dataset"}), "T3_1_dataset_composition", "Dataset composition")
    ov = a[a["section"] == "overlap"].pivot(index="subject", columns="metric", values="value").reset_index()
    t32 = pd.concat([ds[["subject", "n_duplicate_rows", "n_label_conflicts"]].rename(
        columns={"subject": "item", "n_duplicate_rows": "duplicate_rows", "n_label_conflicts": "label_conflicts"}),
        ov[["subject", "n_overlap", "same_label", "conflicting_label", "share_of_b"]].rename(
            columns={"subject": "item", "n_overlap": "overlap", "share_of_b": "share_of_second_set"})], ignore_index=True)
    rb = a[a["section"] == "regime_b"].pivot(index="subject", columns="metric", values="value").reset_index()
    for c in ("duplicate_rows", "label_conflicts", "overlap", "same_label", "conflicting_label"):
        t32[c] = t32[c].astype("Int64")
    t32["share_of_second_set"] = t32["share_of_second_set"].round(4)
    save(t32, "T3_2_data_cleaning_audit", "Data-cleaning audit: duplicates, label conflicts, cross-set overlap")
    idf = pd.read_csv(R / "identity_screen.csv")
    save(pd.concat([rb.rename(columns={"subject": "test_set"}).assign(note="Regime B sizes"), idf], ignore_index=True),
         "T3_3_regimes_and_identity_screen", "Test-set sizes under exact-match removal (Regime B) and identity screen")


def t41() -> None:
    from src.train import Config
    c = Config()
    rows = [("Encoder", "512-256, Linear-BatchNorm-ReLU-Dropout"), ("Dropout", c.dropout), ("Projection dim", c.proj_dim),
            ("Optimiser", "AdamW"), ("Learning rate", c.lr), ("Weight decay", c.weight_decay),
            ("LR schedule", "CosineAnnealingLR, T_max=200"), ("Batch size", c.batch_size),
            ("Max epochs / patience", f"{c.max_epochs} / {c.patience} (early stopping on validation MCC)"),
            ("pos_weight", "n_negative / n_positive of the training fold"),
            ("lambda (search)", "0, 0.1, 0.25, 0.5, 1.0, 2.0"), ("tau (search, at best lambda)", "0.05, 0.07, 0.1, 0.5"),
            ("Seeds", "0-4"), ("CV", "5-fold stratified, scaler fitted on training fold only")]
    cv = pd.read_csv(R / "cv_results.csv")
    h = cv[(cv["checkpoint"] == HEAD) & (cv["family"] == "deep")]
    rows.append(("CPU time per training run, 8M, median (s)", f"{h['train_seconds'].median():.1f} "
                 "(Apple M1, 1 thread/run; measured while other jobs were running)"))
    et = pd.read_csv(R / "embedding_timings.csv")
    for _, r in et.iterrows():
        rows.append((f"Embedding time {r['checkpoint']} ({r['device']})", f"{r['embed_seconds']:.1f} s for {r['n_sequences']} sequences"))
    save(pd.DataFrame(rows, columns=["setting", "value"]), "T4_1_hyperparameters", "Hyperparameters and compute")


def t51(sel: dict) -> None:
    cv = _load_all_models()
    cv = cv[cv["eval_set"] == "cv"]
    keep = ["AAC_SVM", "AAC_RF", "AAC_DPC_CTD_LGBM", f"{HEAD}_LR"] + [n for n, d in sel.items() if d["checkpoint"] == HEAD and d["role"] in ("baseline", "best")]
    cv = cv[cv["model"].isin(keep) & ((cv["temperature"].isna()) | (cv["temperature"] == 0.07) | cv["model"].isin(keep[4:]))]
    t = agg(cv, ["model"])
    t["model"] = [display_name(m, sel) for m in t["model"]]
    save(t, "T5_1_cv_results", "5-fold CV on cleaned Benchmark (mean ± std over seeds and folds)")


def t52_53(sel: dict, tuned: bool = False) -> None:
    frames = [pd.read_csv(R / f) for f in ("baseline_results.csv", "final_results.csv") if (R / f).exists()]
    df = pd.concat(frames, ignore_index=True)
    df = df[df["eval_set"].isin(["ind_425", "ind_1049"])]
    keep = ["AAC_SVM", "AAC_RF", "AAC_DPC_CTD_LGBM", f"{HEAD}_LR"] + [n for n, d in sel.items() if d["checkpoint"] == HEAD]
    df = df[df["model"].isin(keep)]
    for ts, name in (("ind_425", "T5_2_ind425"), ("ind_1049", "T5_3_ind1049")):
        t = agg(df[df["eval_set"] == ts], ["model", "regime"])
        t["model"] = [display_name(m, sel) for m in t["model"]]
        t["regime"] = t["regime"].map({"A": "A (as published)", "B": "B (exact-match removed)", "C": "C (<90% identity)"})
        t = t.sort_values(["regime", "model"], kind="stable")
        save(t, name, f"{ts} results under Regimes A, B and C (mean ± std over 5 seeds; threshold 0.5)")
    tuned_f = R / "final_results_tuned.csv"
    if tuned_f.exists():
        d = pd.read_csv(tuned_f)
        d = d[d["eval_set"].isin(["ind_425", "ind_1049"])]
        t = agg(d, ["model", "eval_set", "regime"])
        t["model"] = [display_name(m, sel) for m in t["model"]]
        save(t, "T5_2b_deep_tuned_threshold", "Deep models with the decision threshold tuned on a training hold-out")


def t54(sel: dict) -> None:
    cv = pd.read_csv(R / "cv_results.csv")
    cv = cv[(cv["family"] == "deep") & (cv["checkpoint"] == HEAD) & (cv["temperature"] == 0.07)]
    t = agg(cv.sort_values("lambda_supcon", kind="stable"), ["lambda_supcon"])
    fin = pd.read_csv(R / "final_results.csv") if (R / "final_results.csv").exists() else None
    if fin is not None:
        f = fin[(fin["checkpoint"] == HEAD) & (fin["regime"] == "B") & (fin["temperature"] == 0.07)]
        g = f.groupby(["lambda_supcon", "eval_set"])["mcc"].mean().unstack("eval_set").round(4)
        g.columns = [f"RegimeB_MCC_{c}" for c in g.columns]
        t = t.merge(g.reset_index(), on="lambda_supcon", how="left")
    save(t, "T5_4_lambda_ablation", "Lambda ablation on ESM-2 8M (CV mean ± std; Regime B MCC of final models)")


def t55(sel: dict) -> None:
    cv = pd.read_csv(R / "cv_results.csv")
    cv = cv[cv["family"] == "deep"]
    rows = []
    for ck, g in cv.groupby("checkpoint"):
        base = g[(g["lambda_supcon"] == 0) & (g["temperature"] == 0.07)]
        pos = g[(g["lambda_supcon"] > 0) & (g["temperature"] == 0.07)].groupby("lambda_supcon")["mcc"].mean()
        if len(pos) == 0 or len(base) == 0:
            continue
        bl = pos.idxmax()
        b = g[(g["lambda_supcon"] == bl) & (g["temperature"] == 0.07)]
        rows.append({"checkpoint": ck, "dim": {"esm2_t6_8M": 320, "esm2_t12_35M": 480, "esm2_t30_150M": 640, "esm2_t33_650M": 1280}[ck],
                     "best_lambda": bl, "CV_MCC_lambda0": ms(base["mcc"]), "CV_MCC_best": ms(b["mcc"]),
                     "CV_AUROC_lambda0": ms(base["auroc"]), "CV_AUROC_best": ms(b["auroc"]),
                     "CV_MCC_diff": round(b["mcc"].mean() - base["mcc"].mean(), 4)})
    t = pd.DataFrame(rows)
    fin = R / "final_results.csv"
    if fin.exists():
        f = pd.read_csv(fin)
        f = f[f["regime"] == "B"]
        for ts in ("ind_425", "ind_1049"):
            col = {}
            for ck in t["checkpoint"]:
                for role in ("baseline", "best"):
                    m = [n for n, d in sel.items() if d["checkpoint"] == ck and d["role"] == role]
                    if m:
                        col.setdefault(f"RegimeB_MCC_{ts}_{role}", {})[ck] = round(f[(f["model"] == m[0]) & (f["eval_set"] == ts)]["mcc"].mean(), 4)
            for c, d in col.items():
                t[c] = t["checkpoint"].map(d)
    save(t, "T5_5_checkpoint_ablation", "ESM-2 checkpoint ablation (lambda=0 vs CV-selected lambda)")
    tau = cv[(cv["lambda_supcon"] > 0)]
    sweeps = []
    for ck, g in tau.groupby("checkpoint"):
        best_l = g[g["temperature"] == 0.07].groupby("lambda_supcon")["mcc"].mean().idxmax()
        gg = g[g["lambda_supcon"] == best_l]
        t2 = agg(gg, ["checkpoint", "lambda_supcon", "temperature"], metrics=["mcc", "auroc", "f1"])
        sweeps.append(t2)
    if sweeps:
        save(pd.concat(sweeps), "T5_5b_temperature_sweep", "Temperature sweep at the CV-selected lambda")


def t56() -> None:
    f = R / "stats_tests.csv"
    if not f.exists():
        return
    st = pd.read_csv(f)
    cols = ["checkpoint", "model_a", "model_b", "test_set", "regime", "n", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi",
            "auroc_diff", "auroc_diff_lo", "auroc_diff_hi", "delong_z", "delong_p", "mcnemar_stat", "mcnemar_p"]
    t = st[cols].copy()
    t["significant_delong_0.05"] = t["delong_p"] < 0.05
    t["significant_mcnemar_0.05"] = t["mcnemar_p"] < 0.05
    save(t.round(4), "T5_6_significance", "lambda>0 vs lambda=0: DeLong (AUROC), McNemar (accuracy), paired bootstrap 95% CIs")
    ps = R / "stats_per_seed.csv"
    if ps.exists():
        p = pd.read_csv(ps)
        s = p.groupby(["checkpoint", "model", "test_set", "regime"]).agg(
            mean_mcc_diff=("mcc_diff", "mean"), mean_auroc_diff=("auroc_diff", "mean"),
            seeds_delong_p_lt_005=("delong_p", lambda x: int((x < 0.05).sum())),
            seeds_mcc_positive=("mcc_diff", lambda x: int((x > 0).sum()))).reset_index()
        save(s.round(4), "T5_6b_per_seed_consistency", "Per-seed consistency of the lambda>0 effect")


def t57() -> None:
    fin = R / "final_results.csv"
    base = R / "baseline_results.csv"
    df = pd.concat([pd.read_csv(x) for x in (fin, base) if x.exists()])
    df = df[(df["regime"] == "A") & df["eval_set"].isin(["ind_425", "ind_1049"])]
    t = agg(df, ["model", "eval_set"], metrics=["accuracy", "sensitivity", "specificity", "mcc", "auroc"])
    pub = pd.DataFrame({"model": ["AIPpred", "PreAIP", "AntiInflam", "(others)"],
                        "published_numbers": "NOT FILLED IN: no verified published values were supplied"})
    save(pd.concat([t, pub], ignore_index=True), "T5_7_comparison_published",
         "Our Regime A results; published predictors' numbers must be added from the original papers (leaky test sets)")


def build_all() -> int:
    t = Timer()
    sel = json.loads((R / "selected_models.json").read_text()) if (R / "selected_models.json").exists() else {}
    failed = []
    for name, fn in [("T3", t3_tables), ("T4.1", t41), ("T5.1", lambda: t51(sel)), ("T5.2/5.3", lambda: t52_53(sel)),
                     ("T5.4", lambda: t54(sel)), ("T5.5", lambda: t55(sel)), ("T5.6", t56), ("T5.7", t57)]:
        try:
            fn()
        except Exception:
            failed.append(name)
            append_note("BLOCKERS.md", f"S11 table {name} failed", "```\n" + traceback.format_exc() + "\n```")
            log.exception("table %s failed", name)
    if "T5.7 needs published numbers" not in (ROOT / "BLOCKERS.md").read_text():
        append_note("BLOCKERS.md", "T5.7 needs published numbers",
                "Table 5.7 (comparison with AIPpred, PreAIP, etc.) contains only this study's Regime A results. No "
                "verified published figures were available to the run and none were invented; copy them from the "
                "original papers into `results/tables/T5_7_comparison_published.csv`.")
    mark_stage("S11_tables", "partial" if failed else "complete", t.elapsed(), f"failed: {failed}" if failed else "all tables")
    return 0
