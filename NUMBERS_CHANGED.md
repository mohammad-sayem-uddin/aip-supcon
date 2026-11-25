# NUMBERS_CHANGED (completion run)

Everything in the chapters that this run invalidated or made stale. Nothing here was silently rewritten, except where the run's rules asked for it (the repository address in Chapter 4, and the two wording corrections in section 1). Chapter scripts are in `src/thesis/`; after you edit them, build each chapter twice in the order 1 to 6 (`NODE_PATH=/private/tmp/ch3build/node_modules node chN.js`).

## 1. Differential leakage gaps (task 2.1) — new test, two wording corrections already applied

New files: `results/tables/T5.12_leakage_gap_per_model.csv`, `T5.12b_leakage_gap_family_contrasts.csv`, `T5.12c_leakage_gap_family_summary.csv`, `results/v2/gap_decision.json`; code `src/v2/gap_tests.py`. The gap is MCC(Regime A) minus MCC(Regime B), computed on **seed-ensemble predictions**; resampling is stratified over the test peptides (2,000 resamples, same resamples for every model). Pre-declared rule: keep "largest for flexible non-linear models" as an inferential claim only if the Flexible minus Linear contrast (mean of both sets) has BH-adjusted p < 0.05, an interval above 0, and the model-level Mann-Whitney p < 0.05. **Result: the rule is met, so the claim stays.**

| Contrast (mean gap, both test sets averaged) | Difference | 95% interval | BH-adjusted p | Mann-Whitney p (models) |
|---|---|---|---|---|
| Flexible non-linear (32 models) minus linear (3) | +0.135 | +0.100 to +0.170 | 0.0009 | 0.023 |
| Residue-level networks minus linear | +0.159 | +0.119 to +0.199 | 0.0009 | 0.024 |
| MLP on frozen vectors minus linear | +0.138 | +0.103 to +0.174 | 0.0009 | 0.004 |
| Random forests (6) minus linear | +0.187 | +0.145 to +0.230 | 0.0009 | 0.024 |
| Trees (RF and LightGBM, 12) minus linear | +0.119 | +0.084 to +0.155 | 0.0009 | 0.22 |
| LightGBM (6) minus linear | +0.051 | +0.016 to +0.086 | 0.007 | 1.0 |
| LightGBM (6) minus random forest (6) | −0.136 | −0.166 to −0.108 | 0.0009 | 0.030 |
| Fine-tuned 8M minus linear | +0.048 | +0.006 to +0.091 | 0.029 | n/a (one model) |
| Fine-tuned 8M minus MLP on frozen vectors | −0.091 | −0.128 to −0.054 | 0.0009 | n/a |
| Capacity: slope of the gap per decade of parameters (8M to 650M MLP) | −0.008 | −0.029 to +0.012 | 0.46 | n/a |

Per-test-set values are in T5.12b (Ind_425 and Ind_1049 columns). Limits to state wherever the claim is made: only three linear models (all logistic regression on ESM-2 embeddings); inference is over test peptides with the models fixed (the Mann-Whitney test is the model-level sensitivity check); linear models also score lower in absolute terms, so part of their smaller gap may be a floor effect.

**Wording corrected in the chapters (done):** "smallest for linear classifiers *and gradient-boosted trees*" was not supported (LightGBM is above linear and far below random forest). Changed to "smallest for linear classifiers (gradient-boosted trees lie in between)" in `ch1.js` (contribution paragraph), `ch6.js` (6.1, Objective 1) and, in `ch5.js` 5.4.3, "for gradient-boosted trees on the hand-crafted features" became "for one gradient-boosted model on the hand-crafted features".

**Still to update by you (stale):**
- `ch5.js` Section 5.4.3, second paragraph: "The differences between the drops of different models were not tested formally ..." is now false. Replace with the results above.
- Section 5.4.3, first paragraph and Section 5.9.1: the gap values quoted there are **per-seed means** (Table 5.4); T5.12 uses **ensemble predictions**, so they differ for the neural models (example: 8M MLP, Ind_1049: 0.150 per-seed mean, 0.169 ensemble). Say which basis a number uses.
- `ch5.js` 5.10 limitation 9 and Section 5.4.3 "was not investigated" (why models with large gaps profit more) remain true.
- Chapter 1 contribution paragraph and abstract: may add "(tested: +0.135 MCC, 95% interval 0.100 to 0.170)".

## 2. Table 5.16 (task 2.3) — rebuilt from the open-access full texts

`results/tables/T5_7_published_reported.csv` (18 rows, each with paper, PMCID, table label, row label); code `src/thesis/published_numbers.py`; full texts in `data/external/papers2/`. Table 5.16 in `ch5.js` now has columns ACC, SN, SP, MCC, AUC for AntiInflam, AIPpred, PreAIP (three thresholds), iAIPs, AIEpred (as reported by the iAIPs authors), AIPFusion-Net and AIPStack, plus this thesis' Regime A and B rows. Still TODO: IF-AIP and AIEpred own figures (papers not open access; abstracts give none), AIPStack SN and SP (Figure 5E/F only).

Stale prose to rewrite:
- `ch5.js` 5.7, first paragraph ("lists ... only the figures that the abstract of its paper reports") and the TODO paragraph after the table.
- `ch5.js` 5.7 last paragraph: "above the values of 0.814 and 0.840 in the abstracts" still true; add that AIPFusion-Net reports MCC 0.654 / AUC 0.884 (Ind-1049) and MCC 0.673 / AUC 0.882 (Ind-426) on the same files, against this thesis' Regime A AAC + RF 0.552 / 0.857 and 0.674 / 0.923.
- `ch1.js` section 1.6 ("the published figures have not been entered in this thesis (Section 5.7)") is false now.
- `ch5.js` 5.10 limitation 9, `ch6.js` 6.3 fifth limitation, `ch6.js` 6.4 first future-work item: reword (the published comparison is now partly made; a retrained comparison is still future work).
- `CITATIONS_TO_VERIFY.md` item A8 (closed except the TODO cells).
- New references used: Zhao et al. 2021 (iAIPs), Zhang et al. 2021 (AIEpred), Gaffar et al. 2024 (IF-AIP), Wang et al. 2026 (AIPFusion-Net). All matched to CrossRef.

## 3. AIPFusion-Net resolved (task 2.4)

The paper is readable (PMC13677489, DOI 10.3389/fmolb.2026.1952395). Its Table 1 gives a training set of 1,451 AIPs and 2,339 non-AIPs and the independent sets Ind-1049 and Ind-426 (173/253); its text says "no overlapping sequences were retained between the training set and the independent test sets" and that the data are in `github.com/ChenYH7693/AIPFusion-Net`. **The three data files in that repository are byte-identical (SHA-256) to the local `Benchmark_Dataset`, `Ind_1049` and `Ind_425`** (`results/v2/aipfusion_repo_check.csv`). So the overlap of 211 and 298 sequences that this thesis measures is a property of the files the paper distributes; whether the paper's experiments used exactly these files is not known from the files. Report it only as a measurement, as before.
Stale text: `BLOCKERS_v2.md` (AIPFusion-Net entry); any chapter sentence saying the paper could not be read (none found in the chapter scripts). Chapter 3 Section 3.3 (provenance) may add the SHA-256 identity.
AIPStack independent sets 2 and 3 are still not obtainable (GitHub 404; Wayback holds only the repository front page). Useful fact from its text: independent sets 2 (135 + 138) and 3 (71 + 72) were built by the AIPStack authors as differences between their own independent set and the AntiInflam and AIPpred benchmarks, i.e. they also screened for overlap. No leakage audit could be run on them.

## 4. Citations and figures (Tier 1)

- Bibliography: added Ke et al. 2017 (NeurIPS 30), Breiman 2001, Cortes and Vapnik 1995, Ioffe and Szegedy 2015 (PMLR 37), Srivastava et al. 2014 (JMLR 15), van der Maaten and Hinton 2008 (JMLR 9), Loshchilov and Hutter 2017 SGDR (kept as the arXiv preprint). Upgraded to the publisher record: Khosla et al. 2020 (NeurIPS 33), Vaswani et al. 2017 (NeurIPS 30), Paszke et al. 2019 (NeurIPS 32), Ilse et al. 2018 (PMLR 80, pp. 2127-2136), Pedregosa et al. 2011 (JMLR 12, pp. 2825-2830). Loshchilov and Hutter's AdamW paper remains the arXiv preprint (OpenReview blocks automated access).
- **Year change:** the scikit-learn citation now reads "Pedregosa et al., 2011" (was 2012) in Chapter 4, Table 4.1 and the reference list. The reference list entry for Khosla et al. is now the NeurIPS record (Vol. 33) instead of arXiv.
- Citations inserted in the chapter scripts: `ch3.js` (SVM, random forest, LightGBM, batch normalisation, dropout, cosine schedule), `ch4.js` Table 4.1 (LightGBM), `ch5.js` Figure 5.3 caption (t-SNE).
- `CITATIONS_TO_VERIFY.md` items A1 to A5 and the venue list in section C are closed (updated there).
- Figures 5.9b, F1 and F5 regenerated (`src/thesis/figures_fix.py`) and viewed; **F1 was redesigned** (the old identity histogram was degenerate): it now shows the share of peptides that share an 8-mer with a peptide of the same or the other class (30.3% / 18.3% for positives, 72.3% / 13.6% for negatives, from TF1). Figure 5.9b has display names; F5 is a heat map with n per length group. None of the three is inserted in a chapter yet; suggested places: 5.9b in Section 5.6.3, F1 and F5 in Section 5.9.3.
- Chapter 4: the repository address (https://github.com/mohammad-sayem-uddin/aip-supcon, public) replaced the TODO; one TODO remains (a permanent archive DOI, needs your account).
- All eight `.docx` files pass the Office XML schema validation (`validate.py`); Word itself is not available here. The LibreOffice build used Carlito and Liberation Serif, which are metric-compatible with Calibri and Times New Roman, so Word pagination should match closely.

## 5. Fine-tuning scale axis (task 2.2) and other protein language models (task 3.1)

See section 6 below once those runs finish (filled in at the end of the run).
