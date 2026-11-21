"""Data pipeline: FASTA parsing, audit, cleaning, leakage regimes A/B/C.

Regime A: test set as published. Regime B: exact-match leakage removed.
Regime C: Regime B plus removal of test sequences with >= 90% identity to any
training sequence (global NW alignment, BLOSUM62).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import ROOT, Timer, append_note, mark_stage, setup_logging

log = setup_logging("data")

RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

FASTAS = {
    "Benchmark": RAW / "Benchmark_Dataset.fasta",
    "Ind_425": RAW / "Ind_425.fasta",
    "Ind_1049": RAW / "Ind_1049.fasta",
}

# S1 hard gate: values the pipeline must reproduce exactly.
GATE = {
    "benchmark_n": 3790,
    "benchmark_pos": 1451,
    "benchmark_neg": 2339,
    "benchmark_unique": 3753,
    "benchmark_label_conflicts": 37,
    "benchmark_clean_n": 3716,
    "bench_x_ind425_overlap": 211,
    "bench_x_ind425_same_label": 204,
    "bench_x_ind425_conflicting": 7,
    "ind425_regime_b_n": 214,
    "bench_x_ind1049_overlap": 298,
    "bench_x_ind1049_same_label": 286,
    "bench_x_ind1049_conflicting": 12,
    "ind1049_regime_b_n": 751,
}


def parse_fasta(path: str | Path) -> pd.DataFrame:
    """Parse a FASTA file; label = 1 if the header contains 'positive' (any case)."""
    rows: list[tuple[str, str]] = []
    header: str | None = None
    chunks: list[str] = []
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header is not None:
                    rows.append((header, "".join(chunks)))
                header, chunks = line[1:], []
            else:
                chunks.append(line)
    if header is not None:
        rows.append((header, "".join(chunks)))
    df = pd.DataFrame(rows, columns=["header", "sequence"])
    df["sequence"] = df["sequence"].str.upper().str.replace(r"\s+", "", regex=True)
    df["label"] = df["header"].str.lower().str.contains("positive").astype(int)
    return df[["sequence", "label", "header"]]


def _conflicted_sequences(df: pd.DataFrame) -> set[str]:
    g = df.groupby("sequence")["label"].nunique()
    return set(g[g > 1].index)


def audit_dataset(df: pd.DataFrame, name: str) -> dict:
    lens = df["sequence"].str.len()
    counts = df["sequence"].value_counts()
    return {
        "dataset": name,
        "n": int(len(df)),
        "n_positive": int((df["label"] == 1).sum()),
        "n_negative": int((df["label"] == 0).sum()),
        "pos_rate": float((df["label"] == 1).mean()),
        "n_unique_sequences": int(df["sequence"].nunique()),
        "len_min": int(lens.min()),
        "len_max": int(lens.max()),
        "len_mean": float(lens.mean()),
        "n_duplicate_rows": int(len(df) - df["sequence"].nunique()),
        "n_duplicated_sequences": int((counts > 1).sum()),
        "n_label_conflicts": len(_conflicted_sequences(df)),
    }


def audit_overlap(df_a: pd.DataFrame, df_b: pd.DataFrame, name_a: str, name_b: str) -> dict:
    """Exact-match overlap on unique sequences, split by label agreement."""
    la = df_a.groupby("sequence")["label"].agg(lambda s: set(s))
    lb = df_b.groupby("sequence")["label"].agg(lambda s: set(s))
    common = sorted(set(la.index) & set(lb.index))
    same = conflict = ambiguous = 0
    for s in common:
        a, b = la[s], lb[s]
        if len(a) > 1 or len(b) > 1:
            ambiguous += 1
        elif a == b:
            same += 1
        else:
            conflict += 1
    n_a, n_b = df_a["sequence"].nunique(), df_b["sequence"].nunique()
    return {
        "set_a": name_a,
        "set_b": name_b,
        "n_overlap": len(common),
        "same_label": same,
        "conflicting_label": conflict,
        "ambiguous": ambiguous,
        "share_of_a": len(common) / n_a,
        "share_of_b": len(common) / n_b,
    }


def clean_benchmark(df: pd.DataFrame) -> pd.DataFrame:
    """Drop ALL copies of label-conflicted sequences, then deduplicate."""
    conflicted = _conflicted_sequences(df)
    step1 = df[~df["sequence"].isin(conflicted)]
    log.info(
        "clean_benchmark: %d rows; %d conflicted sequences -> dropped %d rows -> %d rows",
        len(df), len(conflicted), len(df) - len(step1), len(step1),
    )
    step2 = step1.drop_duplicates("sequence", keep="first")
    log.info("clean_benchmark: dropped %d same-label duplicates -> %d rows", len(step1) - len(step2), len(step2))
    return step2.reset_index(drop=True)


def build_regimes(benchmark_clean: pd.DataFrame, ind_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Regime A: unchanged. Regime B: every sequence found in benchmark_clean removed."""
    train_seqs = set(benchmark_clean["sequence"])
    regime_b = ind_df[~ind_df["sequence"].isin(train_seqs)].reset_index(drop=True)
    return ind_df.reset_index(drop=True), regime_b


# ---------------------------------------------------------------- identity

_ALIGNER = None


def _aligner():
    global _ALIGNER
    if _ALIGNER is None:
        from Bio import Align
        from Bio.Align import substitution_matrices

        a = Align.PairwiseAligner()
        a.mode = "global"
        a.substitution_matrix = substitution_matrices.load("BLOSUM62")
        a.open_gap_score = -10.0
        a.extend_gap_score = -0.5
        _ALIGNER = a
    return _ALIGNER


def pairwise_identity(seq_a: str, seq_b: str) -> float:
    """Global (Needleman-Wunsch, BLOSUM62) alignment identity = matches / len(shorter)."""
    if not seq_a or not seq_b:
        return 0.0
    aln = _aligner().align(seq_a, seq_b)[0]
    return float(aln.counts().identities) / min(len(seq_a), len(seq_b))


def max_identity_to_train(test_seqs: list[str], train_seqs: list[str], floor: float = 0.8) -> np.ndarray:
    """Max alignment identity of each test sequence to any training sequence.

    The LCS length upper-bounds the number of aligned matches, so pairs with
    LCS/min_len < floor are skipped exactly (no approximation). Sequences with
    no pair above the floor return the sentinel -1.0.
    """
    from rapidfuzz.distance import LCSseq
    from rapidfuzz.process import cdist

    lcs = cdist(test_seqs, train_seqs, scorer=LCSseq.similarity, workers=-1, dtype=np.int32)
    tl = np.array([len(s) for s in test_seqs])[:, None]
    rl = np.array([len(s) for s in train_seqs])[None, :]
    bound = lcs / np.minimum(tl, rl)
    out = np.full(len(test_seqs), -1.0)
    ti, ri = np.nonzero(bound >= floor)
    log.info("identity prefilter: %d of %d pairs need alignment", len(ti), lcs.size)
    for i, j in zip(ti, ri):
        ident = pairwise_identity(test_seqs[i], train_seqs[j])
        if ident > out[i]:
            out[i] = ident
    return out


def build_regime_c(benchmark_clean: pd.DataFrame, ind_df: pd.DataFrame, threshold: float = 0.9,
                   max_ident: np.ndarray | None = None) -> pd.DataFrame:
    """Remove every test sequence with identity >= threshold to ANY training sequence."""
    if max_ident is None:
        max_ident = max_identity_to_train(ind_df["sequence"].tolist(), benchmark_clean["sequence"].tolist(),
                                          floor=min(threshold, 0.8))
    keep = max_ident < threshold - 1e-12
    return ind_df[keep].reset_index(drop=True)


# -------------------------------------------------------------------- main


def _load_all() -> dict[str, pd.DataFrame]:
    return {k: parse_fasta(p) for k, p in FASTAS.items()}


def run_s1() -> int:
    t = Timer()
    PROC.mkdir(parents=True, exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    dfs = _load_all()
    bench, i425, i1049 = dfs["Benchmark"], dfs["Ind_425"], dfs["Ind_1049"]

    audits = [audit_dataset(df, name) for name, df in dfs.items()]
    bench_clean = clean_benchmark(bench)
    audits.append({**audit_dataset(bench_clean, "Benchmark_clean")})

    overlaps = [
        audit_overlap(bench_clean, i425, "Benchmark_clean", "Ind_425"),
        audit_overlap(bench_clean, i1049, "Benchmark_clean", "Ind_1049"),
        audit_overlap(i425, i1049, "Ind_425", "Ind_1049"),
        audit_overlap(bench, i425, "Benchmark_raw", "Ind_425"),
        audit_overlap(bench, i1049, "Benchmark_raw", "Ind_1049"),
    ]

    a425, b425 = build_regimes(bench_clean, i425)
    a1049, b1049 = build_regimes(bench_clean, i1049)

    bench_clean.to_csv(PROC / "benchmark_clean.csv", index=False)
    a425.to_csv(PROC / "ind_425_regime_a.csv", index=False)
    b425.to_csv(PROC / "ind_425_regime_b.csv", index=False)
    a1049.to_csv(PROC / "ind_1049_regime_a.csv", index=False)
    b1049.to_csv(PROC / "ind_1049_regime_b.csv", index=False)

    # tidy audit table for thesis Table 3.1 / 3.2
    rows = []
    for a in audits:
        for k, v in a.items():
            if k != "dataset":
                rows.append({"section": "dataset", "subject": a["dataset"], "metric": k, "value": v})
    for o in overlaps:
        subj = f"{o['set_a']} x {o['set_b']}"
        for k, v in o.items():
            if k not in ("set_a", "set_b"):
                rows.append({"section": "overlap", "subject": subj, "metric": k, "value": v})
    for name, n0, n1 in [("Ind_425", len(i425), len(b425)), ("Ind_1049", len(i1049), len(b1049))]:
        rows.append({"section": "regime_b", "subject": name, "metric": "n_regime_a", "value": n0})
        rows.append({"section": "regime_b", "subject": name, "metric": "n_regime_b", "value": n1})
    pd.DataFrame(rows).to_csv(RESULTS / "data_audit.csv", index=False)

    # ---- hard gate
    ab = audits[0]
    actual = {
        "benchmark_n": ab["n"],
        "benchmark_pos": ab["n_positive"],
        "benchmark_neg": ab["n_negative"],
        "benchmark_unique": ab["n_unique_sequences"],
        "benchmark_label_conflicts": ab["n_label_conflicts"],
        "benchmark_clean_n": len(bench_clean),
        "bench_x_ind425_overlap": overlaps[0]["n_overlap"],
        "bench_x_ind425_same_label": overlaps[0]["same_label"],
        "bench_x_ind425_conflicting": overlaps[0]["conflicting_label"],
        "ind425_regime_b_n": len(b425),
        "bench_x_ind1049_overlap": overlaps[1]["n_overlap"],
        "bench_x_ind1049_same_label": overlaps[1]["same_label"],
        "bench_x_ind1049_conflicting": overlaps[1]["conflicting_label"],
        "ind1049_regime_b_n": len(b1049),
    }
    ver = pd.DataFrame(
        [{"check": k, "expected": GATE[k], "actual": actual[k], "match": GATE[k] == actual[k]} for k in GATE]
    )
    ver.to_csv(RESULTS / "s1_verification.csv", index=False)
    (RESULTS / "s1_verification.json").write_text(json.dumps(ver.to_dict("records"), indent=2, default=int))
    print(ver.to_string(index=False))

    if not ver["match"].all():
        bad = ver[~ver["match"]]
        msg = "S1 HARD GATE FAILED. Mismatches (expected vs actual):\n\n" + bad.to_markdown(index=False) \
            if hasattr(bad, "to_markdown") else bad.to_string(index=False)
        append_note("BLOCKERS.md", "S1 HARD GATE FAILED - run aborted", msg + "\n\nDiagnosis: see log.")
        mark_stage("S1", "failed", t.elapsed(), "hard gate mismatch")
        log.error("S1 gate failed; aborting entire run")
        return 2

    log.info("S1 gate PASSED: all %d numbers match", len(ver))
    mark_stage("S1", "complete", t.elapsed(), "hard gate passed; regimes A/B written")
    return 0


def run_s2() -> int:
    t = Timer()
    bench_clean = pd.read_csv(PROC / "benchmark_clean.csv")
    train = bench_clean["sequence"].tolist()
    rows = []
    for name, f in [("Ind_425", "ind_425"), ("Ind_1049", "ind_1049")]:
        a = pd.read_csv(PROC / f"{f}_regime_a.csv")
        t0 = time.time()
        mx = max_identity_to_train(a["sequence"].tolist(), train, floor=0.8)
        log.info("%s: identity screen %.1fs", name, time.time() - t0)
        a = a.assign(max_identity=mx)
        a.to_csv(PROC / f"{f}_max_identity.csv", index=False)
        exact = int(a["sequence"].isin(set(train)).sum())
        rows.append({"test_set": name, "threshold": "exact", "n_total": len(a), "n_removed": exact, "n_remaining": len(a) - exact})
        for thr in (0.8, 0.9, 0.95, 1.0):
            removed = int((mx >= thr - 1e-12).sum())
            rows.append({"test_set": name, "threshold": thr, "n_total": len(a), "n_removed": removed, "n_remaining": len(a) - removed})
        c = build_regime_c(bench_clean, a, threshold=0.9, max_ident=mx)
        c.drop(columns=["max_identity"]).to_csv(PROC / f"{f}_regime_c.csv", index=False)
        log.info("%s Regime C (<0.9 identity): %d sequences", name, len(c))
    pd.DataFrame(rows).to_csv(RESULTS / "identity_screen.csv", index=False)
    print(pd.DataFrame(rows).to_string(index=False))
    mark_stage("S2", "complete", t.elapsed(), "regime C written; identity_screen.csv")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--identity", action="store_true", help="run S2 identity screen")
    args = ap.parse_args()
    sys.exit(run_s2() if args.identity else run_s1())
