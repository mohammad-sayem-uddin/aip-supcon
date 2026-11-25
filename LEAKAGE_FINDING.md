# LEAKAGE FINDING (Phase A)

**Gate result: PASSED.** The overlap reproduces exactly under independent re-computation. This document states what was measured on specific files, what was not measured, and which alternative explanations were ruled out. It makes no statement about the conduct of any author.

All numbers come from `python -m src.v2.phaseA` (outputs: `results/provenance.csv`, `results/overlap_sequences.csv`, `results/external_sources.csv`, `results/tables/T3.5_cross_benchmark_leakage.csv`, `results/tables/T3.5b_cdhit_style_clustering.csv`, `results/v2/phaseA_summary.json`). The original published dataset files were downloaded (URLs and SHA-256 in `external_sources.csv`) and compared with the local files.

## 1. The measurement

Using a new reader (not the S1 code), with whitespace/case normalisation and a check that every residue is one of the 20 standard amino acids (0 violations in all nine datasets):

| Pair (distributed local files) | Exact overlap | Same label | Opposite label | Share of the test set |
|---|---|---|---|---|
| Benchmark and Ind_425 | 211 | 204 | 7 | 49.6% |
| Benchmark and Ind_1049 | 298 | 286 | 12 | 28.4% |
| Ind_425 and Ind_1049 | 77 | 76 | 1 | 7.3% of Ind_1049 |

The numbers are identical on the raw Benchmark (3,790 rows, 3,753 unique) and on the cleaned Benchmark (3,716), because none of the 37 label-conflicted sequences is in either test set. Under a CD-HIT-style cross-set screen (our re-implementation, identity over the shorter sequence), the share of test sequences with identity >= 0.9 to some Benchmark sequence is 62.1% for Ind_425 (264 of 425) and 31.7% for Ind_1049 (333 of 1,049).

## 2. Provenance, verified against the original files

| Local file | Matches | Evidence |
|---|---|---|
| `Ind_1049.fasta` (420/629) | AIPpred independent set, which equals the PreAIP test set | identical sequences, labels and order |
| `Ind_425.fasta` (173/252) | AntiInflam validation set | identical sequences, labels and order |
| `Benchmark_Dataset.fasta` (1,451/2,339 rows) | a composite, not any single published set | see below |

- **The "253 vs 252" discrepancy is not a missing sequence.** The AntiInflam paper's text says 173 + 253, but its own totals (1,261 negatives minus 1,009 training) give 252, and the distributed validation file contains 252 negatives. Local `Ind_425` equals that file exactly.
- **The Benchmark is AIPpred's benchmark plus AntiInflam training sequences.** It contains 3,141 of AIPpred's 3,145 benchmark sequences (4 absent) and 612 sequences that AIPpred's benchmark does not contain; all 612 occur in the AntiInflam training set (690/1,009), none in AntiInflam's validation set.
- **The 37 label conflicts are exactly the cross-source disagreements.** AIPpred's benchmark and AntiInflam's training set share 856 sequences; 819 carry the same label (present once locally, except 3 absent) and 37 carry opposite labels. Those 37 are exactly the 37 sequences that appear twice in the local Benchmark with opposite labels. Neither source file contains an internal conflict.
- **Each source pair is clean on its own.** AIPpred benchmark vs AIPpred independent: 0 exact overlap (13 of its 1,049 independent sequences have >= 0.9 identity to a benchmark sequence, consistent with their stated 0.8 CD-HIT step plus alignment differences). AntiInflam training vs validation: 0 exact overlap.
- **The cross-literature overlaps are what is inherited.** AIPpred benchmark and AntiInflam validation share 211 sequences (the whole Ind_425 overlap). AntiInflam training and AIPpred independent share 298 sequences (the whole Ind_1049 overlap, all among the 612 added sequences).

So the contamination is a property of how the composite training file was assembled relative to two independent sets that came from a different curation lineage: each published split is internally disjoint, but IEDB-derived sequences recur across the two lineages.

## 3. Alternative explanations tested

1. **Parsing or normalisation artefact.** Ruled out: new reader, normalised strings, 0 non-standard residues, same counts raw and cleaned.
2. **Coincidental identity.** Ruled out: 96.7% (Ind_425) and 96.0% (Ind_1049) of the overlapping sequences carry the same label in both files, and a chance match of two unrelated peptides of length >= 11 is below 5e-15. The 7 and 12 label disagreements are cross-source annotation disagreements, not noise.
3. **Accidental pasting of a test file into the training file.** Ruled out: the overlapping rows are scattered (Benchmark rows 18-2,304 for Ind_425, 1,255-3,789 for Ind_1049) and trace exactly to two published source files.
4. **Within-set redundancy filtering (CD-HIT at the stated thresholds) should have removed them.** Not the case: clustering each set separately (Benchmark at 0.9, Ind_1049 at 0.8, Ind_425 at 0.6; CD-HIT-style) leaves 297 of 298 and 189 of 211 overlapping sequences intact, because within-set clustering cannot see the other set. Only a cross-set screen (the CD-HIT-2D analogue) removes them.
5. **A different file version.** A version with the overlap removed would have smaller test sets (751 and 214 sequences) or a smaller Benchmark. The distributed test sets are the original published sets (1,049 and 425), and the Benchmark carries all 211 and 298 sequences, so no such version is what is distributed here. Whether a published experiment used some other filtered version cannot be decided from these files.

## 4. What was not measured

- **What any paper actually did.** I could not read the AIPFusion-Net paper (publisher returned HTTP 503; web search found no trace of it). Every statement attributed to it in the plan (its training counts, its "no overlapping peptide sequences" sentence, its CD-HIT thresholds, an "Ind-426" set) is **unverified**. The measurement above concerns the files distributed locally and the original AIPpred, PreAIP and AntiInflam files, not that paper's experiments.
- **Whether any published numbers used these exact files.** The counts 1,451/2,339 (Benchmark) and 1,049 / 425 (independent sets) match the local files, but a match of counts is not proof of identical files.
- **AIPStack's independent sets 2 and 3.** Not obtainable (see `BLOCKERS_v2.md`).
- **The CD-HIT binary.** Not installed; all clustering numbers use a re-implementation (`greedy_cluster`) and will differ slightly from CD-HIT. A reproduction check is only approximate: the AIPpred + AntiInflam union (3,988 unique) clusters to 3,784 representatives at 0.9, against 3,753 unique sequences in the local Benchmark; of the 231 AntiInflam-only sequences absent from the local Benchmark, 130 have identity >= 0.9 to a retained sequence, which is consistent with, but does not establish, a 0.9 redundancy filter.

## 5. Safe wording for the thesis

"On the distributed benchmark files, 211 of the 425 sequences in the AntiInflam validation set (49.6%) and 298 of the 1,049 sequences in the AIPpred independent set (28.4%) also occur in the combined training file. The training file is the union of the AIPpred benchmark and AntiInflam training sets; each source split is internally disjoint, but the two literatures share IEDB-derived peptides. Removing the overlap (Regime B) is therefore required for a leakage-free estimate; the effect on performance is measured in Chapter 5."
