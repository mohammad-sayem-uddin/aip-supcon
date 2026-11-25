# List of Tables

Generated from the caption text embedded in the chapter build scripts (`src/thesis/*.js`); regenerate with the chapter build (see `src/thesis/lib.js`, which now also writes `results/thesis/captions_chN.json`) rather than editing this file by hand.

Page numbers are left as `[page]` because each chapter is currently a separate `.docx` file; they can only be filled in once the chapters are combined into one paginated document (not done by this run, which produces content only, per Priority 3's instruction).

Table 2.1: Reported performance of AIP predictors discussed in this chapter, with whether a check for sequence overlap between training and test... .......... [page]

Table 3.1: Composition of the three distributed files and of the cleaned training collection (Benchmark_clean, Section 3.3). .......... [page]

Table 3.2: Provenance of the three local files, established by comparison with the downloaded original files. .......... [page]

Table 3.3: Duplicates and label conflicts in Benchmark_Dataset and their origin. .......... [page]

Table 3.4: Exact overlap between each training set and each independent set, by direction, with the number of independent-set sequences at identity of... .......... [page]

Table 3.5: SHA-256 digests of the local data files and of the files in the AIPFusion-Net repository, downloaded from... .......... [page]

Table 3.6: Cleaning of Benchmark_Dataset, with the number of rows after each step. .......... [page]

Table 3.7: Size and class composition of the three evaluation regimes for each independent set. .......... [page]

Table 3.8: Identity screen of the independent sets against Benchmark_clean, and the shuffled-composition null control. .......... [page]

Table 3.9: The ESM-2 checkpoints used as frozen feature extractors. .......... [page]

Table 3.10: Pooling variants compared on frozen ESM-2 650M embeddings. .......... [page]

Table 3.11: Fine-tuning protocol for the ESM-2 8M checkpoint and its frozen control. .......... [page]

Table 3.12: Layers of model B1. .......... [page]

Table 3.13: Layers of model B2. .......... [page]

Table 3.14: Layers of model B3. .......... [page]

Table 3.15: Layers of model B4. .......... [page]

Table 3.16: Layers of model B5. .......... [page]

Table 3.17: Layers of model B6. .......... [page]

Table 3.18: Training settings of the multilayer perceptron and of the residue-level models. .......... [page]

Table 3.19: Minimum detectable effect (80% power, two-sided α = 0.05) of the paired comparisons of λ > 0 with λ = 0 for each test set and regime. .......... [page]

Table 4.1: Main software packages and versions on the local machine (from requirements.txt). .......... [page]

Table 4.2: Compute time recorded for each stage of the experiments (results/.stages and results/v2/kaggle_runtimes.csv). .......... [page]

Table 4.3: Device on which each architecture and the fine-tuning experiment were trained (results/v2/device_map.json). .......... [page]

Table 4.4: Training hyperparameters and search ranges. .......... [page]

Table 5.1: Five-fold cross-validated performance on Benchmark_clean (mean ± standard deviation over 25 runs; 15 runs for the fine-tuning experiment). .......... [page]

Table 5.2: Performance on Ind_425 (425 sequences in Regime A, 214 in Regime B, 162 in Regime C), mean over the five final models of each configuration. .......... [page]

Table 5.3: Performance on Ind_1049 (1,049 sequences in Regime A, 751 in Regime B, 716 in Regime C), mean over the five final models of each... .......... [page]

Table 5.4: Drop in performance from Regime A (as distributed) to Regime B (exact matches removed) and to Regime C (identity ≥ 0.9 also removed), for... .......... [page]

Table 5.5: Contrasts between the leakage gaps (MCC in Regime A minus MCC in Regime B) of model families. .......... [page]

Table 5.6: Cross-benchmark evaluation: MCC of AAC + RF and of the frozen 650M multilayer perceptron (λ = 0) for each pairing of a training set with an... .......... [page]

Table 5.7: Effect of the SupCon weight λ on the multilayer perceptron with the frozen 8M embedding (τ = 0.07). .......... [page]

Table 5.8: Effect of the best SupCon weight at the four ESM-2 checkpoints (multilayer perceptron). .......... [page]

Table 5.9: Temperature sweep at the selected λ of each checkpoint (cross-validated, mean ± standard deviation over 25 runs). .......... [page]

Table 5.10: The contrast λ* versus λ = 0 in six architectures on the frozen 8M embedding, Regime B. .......... [page]

Table 5.11: The λ-contrasts that remain significant after Benjamini–Hochberg correction (within family or globally). .......... [page]

Table 5.12: Number of comparisons in each family of tests, with the number significant at 5% before correction, after correction within the family, and... .......... [page]

Table 5.13: Pooling variants on the frozen 650M embedding (multilayer perceptron, λ = 0), with AAC + RF for reference. .......... [page]

Table 5.14: Hand-crafted features, ESM-2 embeddings and their concatenation with three classifiers. .......... [page]

Table 5.15: The fine-tuned 8M model and its comparators. .......... [page]

Table 5.16: Paired comparisons of the representation study (exploratory). .......... [page]

Table 5.17: Published performance figures, each read from the table named in the last column of the open-access full text of the cited paper... .......... [page]

Table 5.18: Minimum detectable effect (80% power, 5% level) for paired comparisons of two models on each test set and regime: median over the... .......... [page]

