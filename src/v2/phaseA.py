"""Phase A: provenance, adversarial verification of the overlap claim, cross-benchmark audit.

Run: python -m src.v2.phaseA
Writes: results/provenance.csv, results/overlap_sequences.csv, results/external_sources.csv,
        results/tables/T3.5_cross_benchmark_leakage.csv, results/tables/T3.5b_cdhit_style_clustering.csv,
        results/v2/phaseA_summary.json
"""
from __future__ import annotations

import glob
import json
import re
import time

import pandas as pd

from src.utils import ROOT, setup_logging
from src.v2.common import EXT, R, STD, TABLES, V2, block, decide, greedy_cluster, mark, norm_seq, sha256

log = setup_logging("phaseA")


# ------------------------------------------------------------------ readers


def read_fasta_file(path, label_from_header: bool = False, label: int | None = None) -> list[tuple[str, str, int | None]]:
    rows, h = [], None
    for line in open(path, errors="ignore"):
        line = line.strip()
        if not line:
            continue
        if line.startswith(">"):
            h = line[1:]
        else:
            lab = label
            if label_from_header:
                lab = 1 if "positive" in (h or "").lower() else 0
            rows.append((h or "", norm_seq(line), lab))
    return rows


def read_antiinflam(path, label: int) -> list[tuple[str, str, int]]:
    out = []
    for line in open(path, errors="ignore"):
        if "##" in line:
            h, s = line.split("##", 1)
            out.append((h.strip(">").strip(), norm_seq(s), label))
    return out


def df_of(rows) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["header", "sequence", "label"])


def load_sources() -> dict[str, pd.DataFrame]:
    """name -> DataFrame[header, sequence, label] for every obtainable dataset."""
    g = lambda pat: glob.glob(str(EXT / pat))[0]
    ap_bp = read_fasta_file(g("aippred_benchmarking-positive/*.txt"), label=1)
    ap_bn = read_fasta_file(g("aippred_benchmarking-negative/*.txt"), label=0)
    ap_ip = read_fasta_file(g("aippred_Ind-positive/*.txt"), label=1)
    ap_in = read_fasta_file(g("aippred_Ind-negative/*.txt"), label=0)
    pa_tr = read_fasta_file(g("preaip_training-positive/*.txt"), label_from_header=True)
    pa_te = read_fasta_file(g("preaip_test-positive/*.txt"), label=1) + read_fasta_file(g("preaip_test-negative/*.txt"), label=0)
    ai_tr = read_antiinflam(g("antiinflam_1/file.txt"), 1) + read_antiinflam(g("antiinflam_2/file.txt"), 0)
    ai_va = read_antiinflam(g("antiinflam_3/file.txt"), 1) + read_antiinflam(g("antiinflam_4/file.txt"), 0)
    from src.data import FASTAS, parse_fasta
    loc = {k: parse_fasta(p).rename(columns={}) for k, p in FASTAS.items()}
    out = {
        "AIPpred_benchmark": df_of(ap_bp + ap_bn),
        "AIPpred_independent": df_of(ap_ip + ap_in),
        "PreAIP_training": df_of(pa_tr),
        "PreAIP_test": df_of(pa_te),
        "AntiInflam_training": df_of(ai_tr),
        "AntiInflam_validation": df_of(ai_va),
        "local_Benchmark": loc["Benchmark"],
        "local_Ind_425": loc["Ind_425"],
        "local_Ind_1049": loc["Ind_1049"],
    }
    for k, d in out.items():
        d["sequence"] = d["sequence"].map(norm_seq)
    return out


def counts(d: pd.DataFrame) -> str:
    return f"{int((d.label == 1).sum())}/{int((d.label == 0).sum())}"


def lab_map(d: pd.DataFrame) -> dict[str, set]:
    m: dict[str, set] = {}
    for s, l in zip(d["sequence"], d["label"]):
        m.setdefault(s, set()).add(int(l))
    return m


def overlap(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    la, lb = lab_map(a), lab_map(b)
    common = sorted(set(la) & set(lb))
    same = sum(1 for s in common if len(la[s]) == 1 and la[s] == lb[s] and len(lb[s]) == 1)
    conf = sum(1 for s in common if len(la[s]) == 1 and len(lb[s]) == 1 and la[s] != lb[s])
    return {"n": len(common), "same": same, "conflict": conf, "ambiguous": len(common) - same - conf, "seqs": common}


# --------------------------------------------------------------------- main


def run() -> int:
    t0 = time.time()
    V2.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    S = load_sources()
    for k, d in S.items():
        bad = d[~d["sequence"].str.fullmatch(f"[{STD}]+")]
        log.info("%-24s n=%d unique=%d pos/neg=%s nonstandard=%d", k, len(d), d["sequence"].nunique(), counts(d), len(bad))

    # ---- external source register (audit trail)
    reg = []
    for p in sorted(glob.glob(str(EXT / "*/*.txt"))):
        reg.append({"file": p.replace(str(ROOT) + "/", ""), "bytes": len(open(p, "rb").read()), "sha256": sha256(p)})
    pd.DataFrame(reg).to_csv(R / "external_sources.csv", index=False)

    B, I4, I1 = S["local_Benchmark"], S["local_Ind_425"], S["local_Ind_1049"]
    APb, APi, AIt, AIv = S["AIPpred_benchmark"], S["AIPpred_independent"], S["AntiInflam_training"], S["AntiInflam_validation"]

    # ---- A2.1 independent re-computation of the overlap, normalised
    gate = {"Benchmark_x_Ind_425": overlap(B, I4), "Benchmark_x_Ind_1049": overlap(B, I1), "Ind_425_x_Ind_1049": overlap(I4, I1)}
    conflicted = {s for s, l in lab_map(B).items() if len(l) > 1}
    Bclean = B[~B["sequence"].isin(conflicted)].drop_duplicates("sequence")
    gate_clean = {"Benchmark_clean_x_Ind_425": overlap(Bclean, I4), "Benchmark_clean_x_Ind_1049": overlap(Bclean, I1)}
    reproduces = (gate["Benchmark_x_Ind_425"]["n"] == 211 and gate["Benchmark_x_Ind_1049"]["n"] == 298
                  and gate_clean["Benchmark_clean_x_Ind_425"]["n"] == 211 and gate_clean["Benchmark_clean_x_Ind_1049"]["n"] == 298)
    log.info("A2 reproduction (211 / 298): %s | raw %s/%s clean %s/%s", reproduces, gate["Benchmark_x_Ind_425"]["n"],
             gate["Benchmark_x_Ind_1049"]["n"], gate_clean["Benchmark_clean_x_Ind_425"]["n"], gate_clean["Benchmark_clean_x_Ind_1049"]["n"])

    # ---- A1 provenance: local file vs published files
    set_ = lambda d, l=None: set(d[d.label == l].sequence) if l is not None else set(d.sequence)
    order_eq = lambda a, b: list(a["sequence"]) == list(b["sequence"])
    ind1049_id = set_(I1, 1) == set_(APi, 1) and set_(I1, 0) == set_(APi, 0)
    ind425_id = set_(I4, 1) == set_(AIv, 1) and set_(I4, 0) == set_(AIv, 0)
    apb_all, ait_all = set_(APb), set_(AIt)
    b_all = set_(B)
    extras = b_all - apb_all
    missing_from_local = apb_all - b_all
    prov = [
        {"local_file": "Ind_1049.fasta", "local_counts_pos_neg": counts(I1), "published_origin": "AIPpred independent dataset (Manavalan et al. 2018, Front Pharmacol 9:276); identical to PreAIP test set (Khatun et al. 2019, Front Genet 10:129)",
         "published_counts_pos_neg": counts(APi), "verified_against_downloaded_file": True,
         "match": "IDENTICAL" if ind1049_id and order_eq(I1, APi) else ("SET-IDENTICAL" if ind1049_id else "DIFFERS"),
         "evidence": f"set equality per class={ind1049_id}; same order as AIPpred Ind-positive then Ind-negative={order_eq(I1, APi)}; PreAIP test == AIPpred independent={set_(S['PreAIP_test'])==set_(APi)}",
         "source_url": "http://www.thegleelab.org/AIPpred/AIPpredData.html"},
        {"local_file": "Ind_425.fasta", "local_counts_pos_neg": counts(I4), "published_origin": "AntiInflam validation dataset (Gupta et al. 2017, J Transl Med 15:7)",
         "published_counts_pos_neg": counts(AIv) + " in the distributed file; the paper text says 173/253", "verified_against_downloaded_file": True,
         "match": "IDENTICAL" if ind425_id else "DIFFERS",
         "evidence": f"set equality per class={ind425_id}; same order={order_eq(I4, AIv)}. The 'missing' 253rd negative does not exist: the paper's own totals (1261 negatives - 1009 training) give 252, and the distributed file has 252 lines",
         "source_url": "http://metagenomics.iiserb.ac.in/antiinflam/data.php (Wayback snapshot 20220925172033)"},
        {"local_file": "Benchmark_Dataset.fasta", "local_counts_pos_neg": counts(B),
         "published_origin": "NOT AIPpred's benchmark alone: AIPpred benchmark (1258/1887) plus sequences from the AntiInflam training set (690/1009)",
         "published_counts_pos_neg": f"AIPpred benchmark {counts(APb)}; AntiInflam training {counts(AIt)}", "verified_against_downloaded_file": True, "match": "COMPOSITE",
         "evidence": (f"{len(b_all)} unique local sequences = {len(apb_all & b_all)} of AIPpred's {len(apb_all)} benchmark sequences ({len(missing_from_local)} absent) + {len(extras)} others; "
                      f"all {len(extras & ait_all)} of those {len(extras)} others occur in the AntiInflam training set; none in AntiInflam validation ({len(extras & set_(AIv))}); "
                      f"{len(extras & set_(I1))} of them are in AIPpred's independent set"),
         "source_url": "AIPpred + AntiInflam files (see results/external_sources.csv)"},
    ]
    pd.DataFrame(prov).to_csv(R / "provenance.csv", index=False)

    # ---- conflict origin
    ap_pos, ap_neg = set_(APb, 1), set_(APb, 0)
    ap_internal_conflict = ap_pos & ap_neg
    pa_tr = S["PreAIP_training"]
    facts = {
        "aippred_bench_x_aippred_ind": overlap(APb, APi)["n"],
        "antiinflam_train_x_antiinflam_val": overlap(AIt, AIv)["n"],
        "aippred_bench_x_antiinflam_val": overlap(APb, AIv)["n"],
        "antiinflam_train_x_aippred_ind": overlap(AIt, APi)["n"],
        "local_benchmark_unique": len(b_all),
        "aippred_bench_unique": len(apb_all),
        "n_extras_not_in_aippred_bench": len(extras),
        "extras_in_antiinflam_train": len(extras & ait_all),
        "extras_in_aippred_ind": len(extras & set_(APi)),
        "extras_in_antiinflam_val": len(extras & set_(AIv)),
        "aippred_bench_seqs_absent_locally": len(missing_from_local),
        "label_conflicts_in_local_benchmark": len(conflicted),
        "label_conflicts_already_in_AIPpred_benchmark_files": len(ap_internal_conflict),
        "conflicts_in_AIPpred_bench_that_equal_local_conflicts": len(ap_internal_conflict & conflicted),
        "preaip_training_equals_aippred_benchmark": set_(pa_tr, 1) == set_(APb, 1) and set_(pa_tr, 0) == set_(APb, 0),
        "preaip_test_equals_aippred_independent": set_(S["PreAIP_test"]) == set_(APi),
    }
    log.info("provenance facts: %s", json.dumps(facts))

    # ---- A2 overlap_sequences.csv (auditable list)
    pos_in_B = {s: i for i, s in enumerate(B["sequence"])}
    rows = []
    for pair, (a, b, na, nb) in {
        "local_Benchmark x local_Ind_425": (B, I4, "Benchmark", "Ind_425"),
        "local_Benchmark x local_Ind_1049": (B, I1, "Benchmark", "Ind_1049"),
        "local_Ind_425 x local_Ind_1049": (I4, I1, "Ind_425", "Ind_1049"),
    }.items():
        la, lb = lab_map(a), lab_map(b)
        for s in overlap(a, b)["seqs"]:
            rows.append({"pair": pair, "sequence": s, "length": len(s),
                         "label_in_" + na: "/".join(map(str, sorted(la[s]))), "label_in_" + nb: "/".join(map(str, sorted(lb[s]))),
                         "labels_agree": la[s] == lb[s] and len(la[s]) == 1,
                         "in_AIPpred_benchmark": s in apb_all, "in_AntiInflam_training": s in ait_all,
                         "in_AIPpred_independent": s in set_(APi), "in_AntiInflam_validation": s in set_(AIv),
                         "first_row_in_Benchmark_file": pos_in_B.get(s, -1)})
    ov = pd.DataFrame(rows)
    # unify label columns into stable names
    ov["label_a"] = ov.filter(like="label_in_").bfill(axis=1).iloc[:, 0]
    out = []
    for pair, g in ov.groupby("pair"):
        cols = [c for c in g.columns if c.startswith("label_in_")]
        gg = g.dropna(axis=1, how="all")
        c2 = [c for c in gg.columns if c.startswith("label_in_")]
        gg = gg.rename(columns={c2[0]: "label_in_file_a", c2[1]: "label_in_file_b"}).drop(columns=["label_a"], errors="ignore")
        out.append(gg)
    pd.concat(out)[["pair", "sequence", "length", "label_in_file_a", "label_in_file_b", "labels_agree", "in_AIPpred_benchmark",
                    "in_AntiInflam_training", "in_AIPpred_independent", "in_AntiInflam_validation", "first_row_in_Benchmark_file"]] \
        .to_csv(R / "overlap_sequences.csv", index=False)

    # ---- chance / structure checks (alternative explanations)
    pair_df = pd.read_csv(R / "overlap_sequences.csv")
    b425 = pair_df[pair_df.pair == "local_Benchmark x local_Ind_425"]
    b1049 = pair_df[pair_df.pair == "local_Benchmark x local_Ind_1049"]
    structure = {
        "agree_425": float(b425.labels_agree.mean()), "agree_1049": float(b1049.labels_agree.mean()),
        "benchmark_rows_of_overlap_425_min_max": [int(b425.first_row_in_Benchmark_file.min()), int(b425.first_row_in_Benchmark_file.max())],
        "benchmark_rows_of_overlap_1049_min_max": [int(b1049.first_row_in_Benchmark_file.min()), int(b1049.first_row_in_Benchmark_file.max())],
        "overlap_425_all_from_AIPpred_benchmark": bool(b425.in_AIPpred_benchmark.all()),
        "overlap_1049_all_from_AntiInflam_training": bool(b1049.in_AntiInflam_training.all()),
        "overlap_1049_any_in_AIPpred_benchmark": bool(b1049.in_AIPpred_benchmark.any()),
    }
    # chance: probability two independent random 11-30mers coincide is astronomically small; report the 20^11 bound
    structure["chance_bound_for_any_random_11mer_pair"] = 20.0 ** -11

    # ---- A3 cross-benchmark matrix (exact + 90% identity)
    from src.data import max_identity_to_train
    trains = {"AIPpred_benchmark (= PreAIP_training)": APb, "AntiInflam_training": AIt, "local_Benchmark_clean": Bclean}
    tests = {"AIPpred_independent (= local Ind_1049 = PreAIP_test)": APi, "AntiInflam_validation (= local Ind_425)": AIv}
    rows = []
    for tn, tr in trains.items():
        trs = list(dict.fromkeys(tr["sequence"]))
        for en, te in tests.items():
            tes = list(dict.fromkeys(te["sequence"]))
            ov_ = overlap(tr, te)
            mx = max_identity_to_train(tes, trs, floor=0.8)
            rows.append({"training_set": tn, "independent_set": en, "n_train": len(trs), "n_test": len(tes),
                         "exact_overlap": ov_["n"], "exact_overlap_share_of_test": round(ov_["n"] / len(tes), 4),
                         "exact_same_label": ov_["same"], "exact_conflicting_label": ov_["conflict"],
                         "identity_ge_0.9": int((mx >= 0.9 - 1e-12).sum()), "identity_ge_0.9_share": round(float((mx >= 0.9 - 1e-12).mean()), 4),
                         "identity_ge_0.8": int((mx >= 0.8 - 1e-12).sum())})
    ind_ind = overlap(APi, AIv)
    rows.append({"training_set": "(independent vs independent)", "independent_set": "AIPpred_independent x AntiInflam_validation",
                 "n_train": APi.sequence.nunique(), "n_test": AIv.sequence.nunique(), "exact_overlap": ind_ind["n"],
                 "exact_overlap_share_of_test": round(ind_ind["n"] / AIv.sequence.nunique(), 4), "exact_same_label": ind_ind["same"],
                 "exact_conflicting_label": ind_ind["conflict"], "identity_ge_0.9": None, "identity_ge_0.9_share": None, "identity_ge_0.8": None})
    for nm, why in (("AIPStack independent sets 2 and 3", "not obtainable (see BLOCKERS_v2.md)"),
                    ("AIPFusion-Net splits", "paper unreadable (see BLOCKERS_v2.md)")):
        rows.append({"training_set": nm, "independent_set": why})
    mat = pd.DataFrame(rows)
    mat.to_csv(TABLES / "T3.5_cross_benchmark_leakage.csv", index=False)
    print(mat.to_string(index=False))

    # ---- A2.3 CD-HIT-style clustering at the thresholds named in the plan
    cl = []
    def run_cl(name, seqs, thr):
        reps, assign = greedy_cluster(list(seqs), thr)
        cl.append({"set": name, "threshold": thr, "n_unique_in": len(set(seqs)), "n_representatives": len(reps), "removed": len(set(seqs)) - len(reps)})
        return set(reps)
    union = set(apb_all) | set(ait_all)
    r_b09 = run_cl("local_Benchmark (unique)", b_all, 0.9)
    r_union09 = run_cl("AIPpred_benchmark U AntiInflam_training", union, 0.9)
    r_i1 = run_cl("local_Ind_1049", set_(I1), 0.8)
    r_i4 = run_cl("local_Ind_425", set_(I4), 0.6)
    run_cl("local_Ind_425", set_(I4), 0.9)
    run_cl("local_Ind_1049", set_(I1), 0.9)
    cl.append({"set": "overlap surviving within-set clustering: Benchmark@0.9 reps x Ind_1049@0.8 reps", "threshold": "0.9/0.8",
               "n_unique_in": None, "n_representatives": len(r_b09 & r_i1), "removed": None})
    cl.append({"set": "overlap surviving within-set clustering: Benchmark@0.9 reps x Ind_425@0.6 reps", "threshold": "0.9/0.6",
               "n_unique_in": None, "n_representatives": len(r_b09 & r_i4), "removed": None})
    # cross-set (CD-HIT-2D style): test sequences with identity >= thr to training
    trs = list(set_(Bclean))  # the cleaned benchmark (3,716 sequences) is the single reference point for every identity figure
    for en, te in (("local_Ind_1049", I1), ("local_Ind_425", I4)):
        mx = max_identity_to_train(list(set_(te)), trs, floor=0.6)
        for thr in (0.6, 0.8, 0.9, 1.0):
            n = int((mx >= thr - 1e-12).sum())
            cl.append({"set": f"CROSS-SET (CD-HIT-2D style): {en} sequences with identity>={thr} to local_Benchmark_clean", "threshold": thr,
                       "n_unique_in": len(set_(te)), "n_representatives": len(set_(te)) - n, "removed": n})
    cl_df = pd.DataFrame(cl)
    cl_df.to_csv(TABLES / "T3.5b_cdhit_style_clustering.csv", index=False)
    print(cl_df.to_string(index=False))

    summary = {"overlap_reproduces_211_298": bool(reproduces), "gate": {k: {kk: vv for kk, vv in v.items() if kk != "seqs"} for k, v in {**gate, **gate_clean}.items()},
               "provenance_facts": facts, "structure": structure,
               "ind1049_identical_to_aippred_independent": bool(ind1049_id), "ind425_identical_to_antiinflam_validation": bool(ind425_id)}
    (V2 / "phaseA_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    mark("A", "complete" if reproduces else "failed", time.time() - t0, f"overlap reproduces: {reproduces}")
    return 0 if reproduces else 2


if __name__ == "__main__":
    raise SystemExit(run())
