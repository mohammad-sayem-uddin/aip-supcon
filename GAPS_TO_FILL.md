# GAPS_TO_FILL

Claims considered while expanding Chapters 1 and 2 (autonomous run, Priority 2, 2026-11-25/26) and left out because no source retrieved through OpenAlex, Scite or SciSpace could be read and verified to support them. Each entry records what was searched and why the candidate was not used, per the run's hard rule: every added sentence making a factual claim must cite a source retrieved and read, or be left out and recorded here.

## Peptide synthesis / assay cost figures

Searched: `search_literature` for "peptide synthesis cost biological assay in vitro validation time-consuming expensive drug candidate" and several related queries, looking for a specific, quotable figure on the cost or throughput of wet-laboratory AIP/peptide screening (e.g. cost per candidate, assay turnaround time) to sharpen the "why computational screening" argument in Chapter 1, Section 1.1.

Why not used: no hit returned a concrete, attributable number for peptide screening cost or throughput; results were either generic AI-in-drug-discovery reviews with no specific figure (one such review, Hashemi et al. 2024, was used, but only for its general argument, explicitly flagged in the text as not an AIP-specific figure) or unrelated papers (QSPR blood-brain-barrier prediction, siderophore biosynthesis, compound management logistics). Left as a qualitative claim ("expensive and time-consuming", already cited to Manavalan et al. 2018) rather than attaching an invented number.

## AntiInflam-era review quantitative detail (Raza et al. 2024, Asim et al. 2025)

Searched: `get_work` and `search_literature` (dois-only lookup, no `term`) for `10.1007/s11831-024-10078-7` (Raza et al. 2024, AIP predictor review) and `10.1016/j.compbiomed.2025.109821` (Asim et al. 2025, peptide classification landscape review).

Why not used: both are closed-access; neither OpenAlex nor Scite returned an abstract or any readable text (`contentDenied: true`, `no_full_text`). Both papers are already cited for the qualitative point that the AIP predictor literature is large and still growing, which is as much as could be verified from the metadata alone. No count of predictors, no specific performance figure, and no dataset statistic was taken from either paper, because none could be read.

## Pep-CNN (Zhang & Li 2022) reported performance figures

Searched: `get_work` and `search_literature` (dois-only) for `10.1016/j.chemolab.2022.104490`.

Why not used: closed access; no abstract or full text returned by either tool. The paper is cited in Chapter 1 and Chapter 2 only for the qualitative fact that a convolutional network has been applied to short therapeutic peptides generally, combining sequence and physicochemical features — a description already confirmed in a prior session's citation audit (CITATION_AUDIT.md) — not for any accuracy, AUC or MCC figure, because none was retrievable.

## NeXtMD (Xie et al. 2025) and PepNet (Han et al. 2024) numeric magnitudes

Searched: `search_literature` and `get_work` for `10.1186/s12915-025-02314-8` (NeXtMD) and `10.1038/s42003-024-06911-1` (PepNet), looking for the specific magnitude behind each paper's claim of outperforming compared methods, to replace the qualitative "no magnitude given" note in Table 2.1 (`tab:aip_predictors`) with an actual number.

Why not used: the abstracts available describe the outcome only in comparative terms ("great superiority", "generalises to peptides unseen in training", "outperforms compared methods") without a specific accuracy/AUC/MCC delta in the text that was readable through these tools. Table 2.1 and the surrounding prose in Chapter 2, Section 2.2 report this honestly as "no magnitude given in the available text" rather than inferring or estimating one.

## A second, independently-sourced protein-language-model family comparison on AIPs specifically

Searched: combinations of "ESM ProtBERT ProtT5 comparison anti-inflammatory peptide prediction benchmark" via `search_literature`, looking for a single study that evaluates more than one pre-trained protein language model family (ESM vs. ProtBERT/ProtT5) under matched conditions on an AIP benchmark, which would have let Chapter 2, Section 2.3 state which backbone family performs best on AIPs specifically, rather than noting that the comparison has not been made.

Why not used: no such matched-condition, multi-backbone comparison on an AIP benchmark was found. The individual AIP predictors reviewed (Zhu et al. 2024 and Li et al. 2026, both ProtT5-based; this thesis, ESM-2-based) each use one backbone family without comparing it against another on the same data and split, which is exactly the gap Section 2.3 now states explicitly rather than filling with an unsupported claim.

## D3 (AMP/ACP related-task transfer) and the remaining AIPStack independent sets

Not attempted in Priority 2 and not a citation gap specifically — carried over unchanged from `BLOCKERS_v2.md` ("D3 (AMP/ACP transfer): not attempted" and "AIPStack independent sets 2 and 3: still not obtainable"). Recorded here only as a pointer so this file and `BLOCKERS_v2.md` are read together; no new attempt was made on either during this run, consistent with the instruction to work on what does not depend on the university template documents and to leave Priority 4 items (IF-AIP/AIEpred full texts, the Kaggle check) to Priority 4 rather than Priority 2.
