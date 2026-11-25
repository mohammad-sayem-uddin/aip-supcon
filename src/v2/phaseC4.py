"""Completion run 3.1 (C4): frozen ProtBERT and ProtT5-XL (encoder) mean-pooled embeddings, same protocol as the frozen ESM-2 models of Phase C
(512-256 MLP, lambda = 0, 5 seeds x 5 folds, final models for 5 seeds, Regimes A/B/C; random forest for reference).

Embeddings were computed in Kaggle CPU kernels after the weights had been matched to the official sha256 (kaggle_kernel_c4bert/c4t5) and are read from
results/v2/c4/c4_<name>_mean.npz. Usage: python -m src.v2.phaseC4 run [budget_seconds] | stats
"""
from __future__ import annotations
import sys
import numpy as np, pandas as pd
from src.utils import ROOT
from src.v2 import phaseC as C
from src.v2.stats import bh_adjust, compare_files

R = ROOT / "results"; V2 = R / "v2"; TAB = R / "tables"; C4 = V2 / "c4"
NAMES = {"protbert_mean": "c4_protbert_mean.npz", "prott5_mean": "c4_prott5_mean.npz"}

def builder(fname):
    z = np.load(C4 / fname, allow_pickle=True); idx = {s: i for i, s in enumerate(z["sequences"].tolist())}; mat = z["mean"]
    return lambda ss: mat[[idx[s] for s in ss]]

def run(budget=None):
    avail = [n for n, f in NAMES.items() if (C4 / f).exists()]
    for n in avail: C.materialise(n, builder(NAMES[n]))
    models = [(n, c, "C4") for n in avail for c in ("mlp", "rf")]
    return C.run_models(models, "C4_other_plms", budget)

def stats():
    rows = []
    for n in NAMES:
        for clf in ("mlp", "rf"):
            for ts in ("ind_425", "ind_1049"):
                for rg in "BAC":
                    pa = V2 / "predictions" / f"{n}__{clf}_{ts}_{rg}.csv"
                    if not pa.exists(): continue
                    for ref_name, pb in (("ESM-2 650M mean-pooled, same classifier", V2 / "predictions" / f"esm650_mean__{clf}_{ts}_{rg}.csv"), ("AAC + random forest", R / "predictions" / f"AAC_RF_{ts}_{rg}.csv")):
                        if not pb.exists(): continue
                        r = compare_files(pa, pb); r.update({"comparison": f"{n}|{clf} vs {ref_name}", "test_set": ts, "regime": rg, "family": "representation: other PLMs (C4)", "analysis_tier": "exploratory"}); rows.append(r)
    if rows:
        T = pd.DataFrame(rows); T["p_delong_bh_family"] = bh_adjust(T["delong_p"].to_numpy()); T.to_csv(TAB / "T5.14_c4_other_plms_tests.csv", index=False)
        print(T[T.regime == "B"][["comparison", "test_set", "mcc_a", "mcc_b", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi", "delong_p", "p_delong_bh_family"]].round(3).to_string())
    d = pd.read_csv(V2 / "repr_results_v2.csv"); d = d[d.phase == "C4"]
    if len(d):
        s = d.groupby(["model", "eval_set", "regime"]).agg(runs=("mcc", "size"), mcc=("mcc", "mean"), mcc_sd=("mcc", "std"), auroc=("auroc", "mean")).reset_index(); s.to_csv(TAB / "T5.14a_c4_other_plms_summary.csv", index=False); print(s.round(3).to_string())

if __name__ == "__main__":
    if sys.argv[1] == "run": print("tasks left:", run(float(sys.argv[2]) if len(sys.argv) > 2 else None))
    else: stats()
