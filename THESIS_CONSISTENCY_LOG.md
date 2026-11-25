# Consistency pass over Chapters 1-6 and the abstract (overnight run, part 2)

Numbered, worst first. "Fixed" means the chapter scripts in `src/thesis/` were changed and every chapter was rebuilt twice so that cross-references resolve.

1. **Capacity claim (Ch. 1, 5, 6, abstract).** The brief asked for "inflation largest for high-capacity models". The A-minus-B MCC gap is not monotonic in capacity (linear and LightGBM smallest, 650M MLP no larger than AAC + RF, B5 and fine-tuned 8M at the low end of the non-linear models). All four places now say "largest for flexible non-linear models, not a monotonic function of capacity", and Section 5.4.3 states that gap differences were not tested. Decision V2-D15. **Needs your sign-off.**
2. **Ch. 1 promised what Ch. 5/6 did not deliver.** Objective 3 and the contributions mention the latent-space geometry; Chapter 5 had no such section. Added Section 5.5.7 (silhouette and Davies-Bouldin from `results/tables/cluster_metrics_*.csv`) and the answer in 6.1.
3. **"Adequately powered" (Ch. 1, 6) contradicted the power analysis** (minimum detectable effect 0.08 to 0.14 MCC). Reworded to "with the power of the tests stated".
4. **263 vs 264 identity matches** (Ch. 3 vs LEAKAGE_FINDING.md): one reference point (Benchmark_clean: 263 = 61.9%, 333 = 31.7%); `phaseA.py` patched, tables regenerated (V2-D11). No stray 264 remains in the chapters.
5. **Chapter 1 defects:** outline said something other than "Materials and Methods"; numbering jumped 1.7 to 1.9; broken sentences in 1.3 and 1.9; Objective 4 formatted differently from Objectives 1-3; raw LaTeX in 1.1. All rebuilt (sections 1.1 to 1.8, objectives uniformly formatted).
6. **Unsupported claims in Ch. 2 removed** (AIEpred / Pep-CNN / IALP; PreAIP feature list; "ESM outperforms traditional encodings"; "contrastive learning applied effectively in bioinformatics"; NF-kB / MAPK mechanism sentence). "First predictor" is now attributed to the AIPpred authors, not the AntiInflam paper. Listed in CITATIONS_TO_VERIFY.md.
7. **Pre-registration timing (Ch. 3, 4, 6)** said "before the extended experiments"; the audit (Phase A) preceded the commit. Now "after the audit of Phase A and before the experiments of Phases B to F" (V2-D18).
8. **Chapter 4 statements corrected against the code:** fine-tuning protocol (3 seeds, 8 epochs maximum, patience 3, learning rates 5e-5 / 1e-3, validation-fold stopping), Kaggle kernel covers B2 and B5 (B6 ran locally), stage times of 0 s now "< 1 s", cumulative-time wording removed.
9. **Chapter 5 draft statements corrected on review:** CV gains "less than one fifth of the SD" (actually less than one third); AUROC drop range 0.03-0.17 (actually 0.025-0.206); "identity screen mostly coincides with exact matches" (it removes 52 and 35 further sequences); top Regime A models on Ind_1049 (the hand-crafted RF, not AAC + RF); nested-CV explanation (inner hold-out stopping, not "shorter allotment"); which negative survivors are in Regime A; Regime B direction for 8M on Ind_1049.
10. **Table 5.1 grouping bug:** the 650M mean-pooled MLP row sat under the fusion header; moved under pooling (`ch5_data.py`).
11. **Cross-chapter label collisions** (`tab:pooling`, `tab:mde`, `tab:finetune` used in both Ch. 3 and Ch. 5) would have resolved references to the wrong table; Chapter 5 labels renamed (V2-D19).
12. **Tables never cited in the text:** Tables 3.12 to 3.16 (layer tables of B2 to B6) and the paired-comparison table of Chapter 5 now have a citing sentence.
13. **INTERPRETATION_v2.md** gave the per-seed SD range as 0.02-0.17; the full T5.11b range is 0.015-0.247. Fixed; Chapter 5 quotes the full range.
14. **Raw result strings in tables** ("lambda=0", "esm650 fusion ... (rf)") replaced by the thesis notation.
15. **Terminology:** AIP and SupCon are used throughout; "supervised contrastive loss" appears only as the generic term, "SCL" nowhere. "ESM2", "lambda" and raw LaTeX do not occur in the running text (pandoc shows TeX only for the native Word equations of Chapter 3).
16. **Chapter 1 objectives vs Chapter 6:** Objectives 1 to 4 are answered under identically named headings in Section 6.1.
17. **Section references** ("Section 5.7", "5.8" in Ch. 1; Sections 3.5.2, 4.5, 5.x elsewhere) all point to headings that exist (checked mechanically).

Not changed, and why: Figures 5.9b, F1 and F5 were left out (raw model keys as labels / overlapping legend); the text carries their numbers. The year of the scikit-learn citation (2012 arXiv vs JMLR 2011) is logged in CITATIONS_TO_VERIFY.md section C.
