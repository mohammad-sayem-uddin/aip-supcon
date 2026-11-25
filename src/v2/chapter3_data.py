"""Collect every number and table quoted in Chapter 3 from results/ into results/v2/chapter3_data.json (the .docx builder reads only this)."""
from __future__ import annotations

import json
import re

import pandas as pd

from src.utils import ROOT
from src.v2.common import R, TABLES, V2

n0 = lambda x: f"{int(round(float(x))):,}"
pct = lambda x, d=1: f"{100 * float(x):.{d}f}%"


def main() -> None:
    audit = pd.read_csv(R / "data_audit.csv")
    ds = audit[audit.section == "dataset"].pivot(index="subject", columns="metric", values="value")
    F: dict = {}
    for k, name in (("bench", "Benchmark"), ("i425", "Ind_425"), ("i1049", "Ind_1049"), ("clean", "Benchmark_clean")):
        r = ds.loc[name]
        F[k] = {"n": int(r.n), "pos": int(r.n_positive), "neg": int(r.n_negative), "pos_rate": float(r.pos_rate), "unique": int(r.n_unique_sequences),
                "len_min": int(r.len_min), "len_max": int(r.len_max), "len_mean": float(r.len_mean), "dup_rows": int(r.n_duplicate_rows),
                "dup_seqs": int(r.n_duplicated_sequences), "conflicts": int(r.n_label_conflicts)}
    F["removed_rows"] = F["bench"]["n"] - F["clean"]["n"]
    F["removed_pct"] = F["removed_rows"] / F["bench"]["n"]
    F["pos_weight_clean"] = F["clean"]["neg"] / F["clean"]["pos"]
    F["majority_accuracy_clean"] = F["clean"]["neg"] / F["clean"]["n"]
    F["train_fold_n"] = round(F["clean"]["n"] * 0.8)
    F["val_fold_n"] = F["clean"]["n"] - F["train_fold_n"]

    prov = pd.read_csv(R / "provenance.csv")
    summ = json.loads((V2 / "phaseA_summary.json").read_text())["provenance_facts"]
    t35 = pd.read_csv(TABLES / "T3.5_cross_benchmark_leakage.csv")
    g = lambda tr, te: t35[(t35.training_set.astype(str).str.startswith(tr)) & (t35.independent_set.astype(str).str.startswith(te))].iloc[0]
    def pair(tr, te):
        r = g(tr, te)
        return {"n_train": int(r.n_train), "n_test": int(r.n_test), "exact": int(r.exact_overlap), "same": int(r.exact_same_label), "opp": int(r.exact_conflicting_label),
                "share": float(r.exact_overlap_share_of_test), "id09": int(r["identity_ge_0.9"]), "id09_share": float(r["identity_ge_0.9_share"]), "id08": int(r["identity_ge_0.8"])}
    F["pairs"] = {"ap_ap": pair("AIPpred_benchmark", "AIPpred_independent"), "ap_ai": pair("AIPpred_benchmark", "AntiInflam_validation"),
                  "ai_ap": pair("AntiInflam_training", "AIPpred_independent"), "ai_ai": pair("AntiInflam_training", "AntiInflam_validation")}
    ii = t35[t35.training_set == "(independent vs independent)"].iloc[0]
    F["ind_ind"] = {"exact": int(ii.exact_overlap), "same": int(ii.exact_same_label), "opp": int(ii.exact_conflicting_label)}
    # published counts strings from provenance.csv
    pc = prov.set_index("local_file")["published_counts_pos_neg"]
    m = re.search(r"AIPpred benchmark (\d+)/(\d+); AntiInflam training (\d+)/(\d+)", pc["Benchmark_Dataset.fasta"])
    F["ap_bench_pos"], F["ap_bench_neg"], F["ai_train_pos"], F["ai_train_neg"] = (int(x) for x in m.groups())
    F["ap_ind_pos"], F["ap_ind_neg"] = (int(x) for x in pc["Ind_1049.fasta"].split("/"))
    F["ai_val_pos"], F["ai_val_neg"] = (int(x) for x in re.match(r"(\d+)/(\d+)", pc["Ind_425.fasta"]).groups())
    F["prov"] = summ
    lin = pd.read_csv(V2 / "lineage_shared_training.csv").set_index("quantity")["value"]
    F["lin"] = {"shared": int(lin.iloc[0]), "same": int(lin.iloc[1]), "opp": int(lin.iloc[2]), "local_conf": int(lin.iloc[3]), "opp_equal_local_conf": int(lin.iloc[4]),
                "ai_only": int(lin.iloc[5]), "ai_only_present": int(lin.iloc[6]), "ai_only_absent": int(lin.iloc[7]), "ap_internal_conf": int(lin.iloc[8]),
                "ai_internal_conf": int(lin.iloc[9])}
    val = pd.read_csv(V2 / "sequence_validation.csv")
    F["nonstandard_total"] = int(val.rows_with_non_standard_residues.sum())
    F["n_datasets_checked"] = len(val)
    cl = pd.read_csv(TABLES / "T3.5b_cdhit_style_clustering.csv")
    F["within_set_cluster_survivors"] = {"i1049": int(cl[cl.set.str.contains("Ind_1049@0.8")].n_representatives.iloc[0]), "i425": int(cl[cl.set.str.contains("Ind_425@0.6")].n_representatives.iloc[0])}

    reg = pd.read_csv(V2 / "regime_composition.csv").set_index("file")
    F["regime"] = {k: {"n": int(r.n), "pos": int(r.positive), "neg": int(r.negative), "rate": float(r.positive_rate)} for k, r in reg.iterrows()}
    ids = pd.read_csv(R / "identity_screen.csv")
    F["identity"] = {ts: {str(r.threshold): {"removed": int(r.n_removed), "remaining": int(r.n_remaining), "share": int(r.n_removed) / int(r.n_total)} for _, r in g_.iterrows()}
                     for ts, g_ in ids.groupby("test_set")}
    nc = pd.read_csv(V2 / "null_control_identity.csv")
    F["null"] = {}
    for ts, g_ in nc.groupby("test_set"):
        F["null"][ts] = {}
        for thr, h in g_.groupby("threshold"):
            sh = h[h.condition != "observed"]
            ob = h[h.condition == "observed"]
            F["null"][ts][str(thr)] = {"observed": int(ob.n_at_or_above.iloc[0]), "observed_share": float(ob.fraction.iloc[0]), "null_mean": float(sh.n_at_or_above.mean()),
                                       "null_max": int(sh.n_at_or_above.max()), "replicates": int(sh.replicate.nunique()), "n": int(h.n.iloc[0])}
    fd = pd.read_csv(V2 / "feature_dimensions.csv").set_index("feature")["dimension"]
    F["dim"] = {"aac": int(fd["AAC"]), "dpc": int(fd["DPC"]), "ctd": int(fd["CTD"]), "len": int(fd["length"]), "hand": int(fd["AAC+DPC+CTD+length (hand-crafted set)"]),
                "aac_len": int(fd["AAC+length (AAC baselines)"])}
    pdm = pd.read_csv(V2 / "pooling_dimensions.csv").set_index("variant")["dimension"]
    F["pool_dim"] = {k: int(v) for k, v in pdm.items()}
    F["fusion_dim"] = {"esm650": 1280 + F["dim"]["hand"], "esm8": 320 + F["dim"]["hand"]}
    st = lambda f: json.loads((R / ".stages" / f).read_text())["notes"]
    F["residue_vectors"] = int(re.search(r"\((\d+),", st("V2_embed_esm2_t6_8M.json")).group(1))
    et = pd.read_csv(R / "embedding_timings.csv")
    F["n_unique_embedded"] = int(et.n_sequences.iloc[0])
    par = pd.read_csv(V2 / "methods_parameters.csv")
    F["par"] = {f"{r.group}|{r.parameter}": r.value for r in par.itertuples()}
    lay = pd.read_csv(V2 / "architecture_layers.csv")
    F["arch_total"] = lay.groupby("architecture")["architecture_total_parameters"].first().astype(int).to_dict()
    sf = pd.read_csv(V2 / "supcon_floor.csv")
    F["floor"] = {r.anchor: {"npos": float(r.expected_positives_per_anchor), "floor": float(r.floor_log_P), "frac": float(r.class_fraction_benchmark_clean)} for r in sf.itertuples()}
    mde = pd.read_csv(V2 / "mde_summary.csv")
    F["mde_rows"] = mde.to_dict("records")
    F["prereg_commit"] = (ROOT / "PREREG_COMMIT.txt").read_text().split(" committed in ")[1].split(" at ")[0]
    hp = pd.read_csv(V2 / "half_precision_check.csv").set_index("checkpoint")
    F["half"] = {k: {"max_abs": float(r.max_abs_diff), "rel": float(r.max_abs_diff_relative_to_max_value), "dtype": r.residue_cache_dtype} for k, r in hp.iterrows()}
    F["n_comparisons"] = int(len(pd.read_csv(TABLES / "T5.11_corrected_significance.csv")))
    F["env"] = dict(zip(*[pd.read_csv(V2 / "environment.csv")[c] for c in ("item", "value")]))
    F["et"] = et.astype(object).where(et.notna(), None).to_dict("records")

    # ---- tables (header + rows of strings)
    T: dict = {}
    def row(name, k):
        d = F[k]
        return [name, n0(d["n"]), n0(d["pos"]), n0(d["neg"]), pct(d["pos_rate"]), n0(d["unique"]), f"{d['len_min']}-{d['len_max']}", f"{d['len_mean']:.2f}"]
    T["dataset_composition"] = [["Dataset", "Sequences", "AIP", "Non-AIP", "AIP rate", "Unique", "Length range", "Mean length"],
                                row("Benchmark_Dataset", "bench"), row("Ind_425", "i425"), row("Ind_1049", "i1049"), row("Benchmark_clean", "clean")]
    T["provenance"] = [["Local file", "Published origin", "Published counts (AIP/non-AIP)", "Match with the downloaded original"]]
    for r in prov.itertuples():
        T["provenance"].append([r.local_file.replace(".fasta", ""), re.sub(r"\s*\(Manavalan.*", " (Manavalan et al., 2018)", r.published_origin.split(";")[0]) if "AIPpred independent" in r.published_origin else
                                (r.published_origin if "AntiInflam validation" not in r.published_origin else "AntiInflam validation set (Gupta et al., 2017)"),
                                r.published_counts_pos_neg.split(" in the distributed")[0], r.match.capitalize()])
    T["provenance"][3][1] = "A composite: AIPpred benchmark plus AntiInflam training sequences"
    T["provenance"][1][1] = "AIPpred independent set (Manavalan et al., 2018); identical to the PreAIP test set (Khatun et al., 2019)"
    T["provenance"][2][1] = "AntiInflam validation set (Gupta et al., 2017)"
    T["provenance"][2][2] = f"{F['ai_val_pos']}/{F['ai_val_neg']} (distributed file); the paper text states {F['ai_val_pos']}/{F['ai_val_neg'] + 1}"
    T["provenance"][3][2] = f"AIPpred benchmark {F['ap_bench_pos']:,}/{F['ap_bench_neg']:,}; AntiInflam training {F['ai_train_pos']}/{F['ai_train_neg']:,}"
    T["provenance"][3][3] = "Composite (see text)"
    T["conflicts"] = [["Quantity", "Count"],
                      ["Rows in Benchmark_Dataset", n0(F["bench"]["n"])], ["Unique sequences", n0(F["bench"]["unique"])],
                      ["Sequences occurring twice (duplicated rows)", n0(F["bench"]["dup_rows"])], ["Sequences carrying both labels (label conflicts)", n0(F["bench"]["conflicts"])],
                      ["Sequences shared by the AIPpred benchmark and the AntiInflam training set", n0(F["lin"]["shared"])],
                      ["   of which carry the same label in both", n0(F["lin"]["same"])], ["   of which carry opposite labels", n0(F["lin"]["opp"])],
                      ["Label conflicts inside the AIPpred benchmark file", n0(F["lin"]["ap_internal_conf"])],
                      ["Label conflicts inside the AntiInflam training file", n0(F["lin"]["ai_internal_conf"])]]
    P = F["pairs"]
    def prow(name, p):
        return [name, n0(p["n_train"]), n0(p["n_test"]), n0(p["exact"]), n0(p["same"]), n0(p["opp"]), pct(p["share"]), f"{p['id09']} ({pct(p['id09_share'])})"]
    T["overlap"] = [["Training set and independent set", "Training", "Test", "Shared", "Same label", "Opposite", "Share of test set", "Identity >= 0.9"],
                    prow("AIPpred benchmark and AIPpred independent set", P["ap_ap"]), prow("AntiInflam training and AntiInflam validation set", P["ai_ai"]),
                    prow("AIPpred benchmark and AntiInflam validation set (Finding 1)", P["ap_ai"]), prow("AntiInflam training and AIPpred independent set (Finding 2)", P["ai_ap"])]
    c = F["clean"]
    T["cleaning"] = [["Step", "Operation", "Rows after the step", "AIP", "Non-AIP"],
                     ["0", "Parsed and normalised Benchmark_Dataset", n0(F["bench"]["n"]), n0(F["bench"]["pos"]), n0(F["bench"]["neg"])],
                     ["1", f"Removed every row of the {F['bench']['conflicts']} label-conflicted sequences ({F['removed_rows']} rows)", n0(c["n"]), n0(c["pos"]), n0(c["neg"])],
                     ["2", "Removed same-label duplicate rows (none remained)", n0(c["n"]), n0(c["pos"]), n0(c["neg"])]]
    def rrow(label, key):
        d = F["regime"][key]
        return [label, n0(d["n"]), n0(d["pos"]), n0(d["neg"]), pct(d["rate"])]
    T["regimes"] = [["Test set and regime", "Sequences", "AIP", "Non-AIP", "AIP rate"],
                    rrow("Ind_425, Regime A (as distributed)", "ind_425_regime_a"), rrow("Ind_425, Regime B (exact matches removed)", "ind_425_regime_b"),
                    rrow("Ind_425, Regime C (identity < 0.9)", "ind_425_regime_c"),
                    rrow("Ind_1049, Regime A (as distributed)", "ind_1049_regime_a"), rrow("Ind_1049, Regime B (exact matches removed)", "ind_1049_regime_b"),
                    rrow("Ind_1049, Regime C (identity < 0.9)", "ind_1049_regime_c")]
    T["identity"] = [["Test set", "Threshold", "Observed: sequences at or above", "Shuffled-composition null: mean (maximum) over 20 replicates"]]
    for ts, key in (("Ind_425", "Ind_425"), ("Ind_1049", "Ind_1049")):
        for thr in ("0.8", "0.9", "1.0"):
            o, nl = F["null"][key][thr], F["null"][key][thr]
            T["identity"].append([ts, thr, f"{o['observed']} of {o['n']} ({pct(o['observed_share'])})", f"{nl['null_mean']:.2f} ({nl['null_max']})"])
    T["esm"] = [["Checkpoint", "Layers", "Parameters", "Embedding dimension", "Embedding time, 4,641 sequences (CPU)", "Peak memory"]]
    for r in F["et"]:
        short = r["checkpoint"]
        layers = re.search(r"t(\d+)", short).group(1)
        params = re.search(r"_(\d+M)$", short).group(1)
        tcell = "not reliably measured" if short == "esm2_t33_650M" else f"{r['embed_seconds']:.1f} s"
        T["esm"].append([r["hf_id"].replace("facebook/", ""), layers, params, str(int(r["dim"])), tcell, f"{r['peak_rss_mb']:.0f} MB"])
    pdim = F["pool_dim"]
    T["pooling"] = [["Variant", "Construction (frozen ESM-2 650M, residue positions only)", "Dimension"],
                    ["Mean", "Arithmetic mean of the residue vectors", str(pdim["mean"])], ["Max", "Element-wise maximum over residues", str(pdim["max"])],
                    ["Mean and max", "Concatenation of the mean and the maximum", str(pdim["meanmax"])], ["CLS", "The <cls> token vector", str(pdim["cls"])],
                    ["First and last three", "Residue vectors 1-3 and the last three, concatenated", str(pdim["firstlast"])],
                    ["Attention", "Learned softmax weights over residues (model B6 at 650M), weighted sum of residue vectors", str(pdim["mean"])]]
    p = F["par"]
    T["finetune"] = [["Setting", "Value"],
                     ["Backbone", "ESM-2 8M (facebook/esm2_t6_8M_UR50D), all layers trainable"],
                     ["Pooling and head", "Mean pool over residues; Linear 320 to 256, BatchNorm, ReLU, Dropout 0.3; Linear 256 to 1"],
                     ["Optimiser", "AdamW, weight decay " + str(p["C3 fine-tuning|weight_decay"])],
                     ["Learning rates", f"backbone {p['C3 fine-tuning|lr_bb']}, head {p['C3 fine-tuning|lr_head']}"],
                     ["Batch size", str(p["C3 fine-tuning|bs"])], ["Maximum epochs and patience", f"{p['C3 fine-tuning|max_epochs']} and {p['C3 fine-tuning|patience']} (validation MCC)"],
                     ["Gradient clipping", f"max norm {p['C3 fine-tuning|gradient clipping (max norm)']}"],
                     ["Cross-validation", "5 folds (make_folds), seeds " + str(p["C3 fine-tuning|CV seeds"]).strip("[]")],
                     ["Final models", "seeds " + str(p["C3 fine-tuning|final-model seeds"]).strip("[]") + ", 10% stratified hold-out for early stopping"],
                     ["Control", "Same code with the backbone frozen (identical head, loop and folds)"]]
    lay = pd.read_csv(V2 / "architecture_layers.csv")
    T["layers"] = {}
    for a, grp in lay.groupby("architecture"):
        rows = [["Component", "Description", "Parameters"]] + [[r.component, r.description, n0(r.parameters) if r.parameters else "-"] for r in grp.sort_values("order").itertuples()]
        rows.append(["Total", "", n0(grp.architecture_total_parameters.iloc[0])])
        T["layers"][a] = rows
    T["training"] = [["Setting", "Value"],
                     ["Optimiser", "AdamW"], ["Learning rate and weight decay", f"{p['v1 AIPNet / training loop|lr']} and {p['v1 AIPNet / training loop|weight_decay']}"],
                     ["Schedule", "Cosine annealing over 200 epochs"], ["Batch size", str(p["v1 AIPNet / training loop|batch_size"])],
                     ["Maximum epochs and patience", f"{p['v1 AIPNet / training loop|max_epochs']} and {p['v1 AIPNet / training loop|patience']} (validation MCC)"],
                     ["Dropout", str(p["v1 AIPNet / training loop|dropout"])], ["Projection dimension", str(p["v1 AIPNet / training loop|proj_dim"])],
                     ["Lambda grid", str(p["v1 AIPNet / training loop|lambda_grid"]).strip("[]")], ["Temperature grid", str(p["v1 AIPNet / training loop|temperature_grid"]).strip("[]")],
                     ["Seeds", str(p["v1 AIPNet / training loop|seeds"]).strip("[]")], ["Gradient clipping (Phase B models)", f"max norm {p['Phase B residue-level models|clip']}"],
                     ["Per-residue adapter width (Phase B)", str(p["Phase B residue-level models|per-residue adapter width"])]]
    T["mde"] = [["Test set", "Regime", "Sequences", "Comparisons", "MDE of MCC: median [min, max]", "MDE of AUROC: median"]]
    for r in F["mde_rows"]:
        T["mde"].append([r["test_set"].replace("ind_", "Ind_"), r["regime"], n0(r["n"]), str(int(r["comparisons"])), f"{r['mde_mcc_median']:.3f} [{r['mde_mcc_min']:.3f}, {r['mde_mcc_max']:.3f}]", f"{r['mde_auroc_median']:.3f}"])
    (V2 / "chapter3_data.json").write_text(json.dumps({"F": F, "T": T}, indent=1, default=str))
    print("wrote", V2 / "chapter3_data.json", "| tables:", list(T))


if __name__ == "__main__":
    main()
