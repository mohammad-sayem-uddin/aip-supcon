# HANDOFF REPORT (v1 + v2 extension)

_Generated 2026-11-25T14:59:35 by `python -m src.v2.report`; rebuilt after every stage._

## Deliverables (EXECUTION_PLAN_v2.md)

| Deliverable | Contents | Present |
|---|---|---|
| LEAKAGE_FINDING.md | The Phase A result, stated precisely | True |
| PREREGISTRATION.md | Primary hypothesis, committed before Phase B | True |
| POWER_ANALYSIS.md | Detectable effect size at each n | True |
| results/tables/T3.5_cross_benchmark_leakage.csv | T3.5 cross-benchmark leakage matrix | True |
| results/tables/T5.8_architecture_comparison.csv | T5.8 architecture comparison | True |
| results/tables/T5.9_representation_comparison.csv | T5.9 representation comparison | True |
| results/tables/T5.10_cross_benchmark.csv | T5.10 cross-benchmark generalisation | True |
| results/tables/T5.11_corrected_significance.csv | T5.11 FDR-corrected significance | True |
| figures/fig5_8_architecture_lambda.png | F5.8 architectures x lambda | True |
| figures/fig5_9_pooling_ablation.png | F5.9 pooling ablation | True |
| figures/fig5_10_cross_benchmark_heatmap.png | F5.10 generalisation heatmap | True |
| figures/figF1_negative_resemblance.png | F5.11/F analysis figures (several) | True |
| INTERPRETATION_v2.md | Honest reading of everything | True |
| HANDOFF_REPORT.md | This report, rebuilt after every stage | True |
| results/provenance.csv | A1 provenance | True |
| results/overlap_sequences.csv | A2 every overlapping sequence with labels | True |

## 1. STATUS

**v2 extension phases**

| Stage | What | Status | Compute wall-clock | Notes |
|---|---|---|---|---|
| A | Phase A: provenance, overlap verification (gate), cross-benchmark audit | complete | 8.2s | overlap reproduces: True |
| E1 | E1: PREREGISTRATION.md committed before modelling | complete | - | PREREGISTRATION.md committed in c239f43dcb3719c7c40d6c2afd5217d6723a11f3 at 2026-11-25T14:36:00Z (UTC pushed to origin/main) |
| V2_embed_esm2_t6_8M | Residue-level embeddings 8M | complete | 10.5s | (75589, 320), float32 |
| V2_embed_esm2_t33_650M | Residue-level embeddings 650M | complete | 36.8 min | (75589, 1280), float16 |
| B_cv | Phase B: 5 architectures x 6 lambdas x 5 seeds x 5 folds (CV) | complete | n/a (sliced/remote; see notes) | CV complete: B3,B4,B6 on local CPU; B2,B5 on Kaggle GPU (450 runs in ~27 min); 750 rows |
| B_final | Phase B: final models, Regimes A/B/C | complete | 3.1 min | final models for B2-B6 (lambda=0 and lambda*), Regimes A/B/C, 5 seeds |
| C1_pooling | C1: pooling ablation on frozen 650M | complete | 3.0 min | 5 models |
| C1_attention | C1: attention pooling at 650M | complete | 5.2 min | attention pooling over 650M residues |
| C2_fusion | C2: feature fusion (RF, LightGBM, MLP) | complete | 3.7 min | 15 models |
| C3_finetune | C3: fine-tune 8M vs frozen control | complete | n/a (sliced/remote; see notes) | Kaggle 2xT4 GPU kernel aip-c3-finetune-gpu: ESM-2 8M fine-tune vs frozen control; CV seeds 0-2 x 5 folds, final seeds 0-4 |
| D_cross | D1-D2: cross-benchmark generalisation | complete | 5.7 min | 105 jobs this run; 630 metric rows |
| E5_nested | E5: nested CV for the headline comparison | complete | 5.2 min | 25 outer folds |
| E_stats | E2-E4, E6: BH correction, MDE, seed-vs-sample variance | complete | 10.3 min | 126 comparisons |
| F_analysis | Phase F: why AAC wins, motifs, errors, length | complete | 4.0s | 18 models |
| V2_tables | v2 tables and figures | complete | n/a (sliced/remote; see notes) | T5.8, T5.9, T5.10 and figures |

**v1 stages S1-S12 (complete; not re-run)**

Wall-clock is compute time recorded by the stage runners (it excludes code-writing time).

| Stage | What | Status | Compute wall-clock | Notes |
|---|---|---|---|---|
| S1 | Data pipeline, audit, regimes A/B + hard gate | complete | 0.2s | hard gate passed; regimes A/B written |
| S2 | Sequence-identity screen, Regime C | complete | 0.3s | regime C written; identity_screen.csv |
| S3 | ESM-2 embeddings (8M, 35M, 150M, 650M) | complete | 56.3 min | esm2_t12_35M: complete; esm2_t30_150M: complete; esm2_t33_650M: complete; esm2_t6_8M: complete |
| S4 | AIPNet + SupConLoss + unit tests | complete | 2.8s | AIPNet + SupConLoss + 14 passing tests |
| S5 | Training loop + trial runs (lambda=0, 0.5) | complete | 25.0s | trial: lambda=0 (MCC .2575) and lambda=0.5 (MCC .2754), seed 0 x 5 folds; sane |
| S6 | Classical + ESM-LR baselines | complete | 4.5 min | models: AAC_SVM, AAC_RF, AAC_DPC_CTD_LGBM, esm2_t6_8M_LR, esm2_t12_35M_LR, esm2_t30_150M_LR |
| S7 | Lambda sweep on 8M (6 lambdas x 5 seeds x 5 folds) | complete | 5.2 min | lambda sweep on esm2_t6_8M; best lambda>0 = 2 by mean CV MCC |
| S8 | Other checkpoints: lambda + temperature sweeps | complete | 13.3 min | lambda + temperature sweeps; missing/failed: none |
| S9 | Final models, all regimes, both test sets | complete | 5.2 min | final models for 13 configs; checkpoints without final models: none |
| S10 | DeLong, McNemar, bootstrap CIs | complete | 17.9 min | DeLong, McNemar, bootstrap CIs written |
| S11 | Tables and figures | complete | 117.0s | figures: complete; tables: complete |
| S12 | Honest interpretation | complete | 5.0s | INTERPRETATION.md written from results CSVs |

## 2. S1 / PHASE A VERIFICATION

**Phase A gate: PASSED** (overlap reproduces: 211 and 298). Details: [LEAKAGE_FINDING.md](LEAKAGE_FINDING.md).

**S1 hard gate (v1):**

**PASSED: all numbers match exactly.**

| check | expected | actual | match |
|---|---|---|---|
| benchmark_n | 3790 | 3790 | True |
| benchmark_pos | 1451 | 1451 | True |
| benchmark_neg | 2339 | 2339 | True |
| benchmark_unique | 3753 | 3753 | True |
| benchmark_label_conflicts | 37 | 37 | True |
| benchmark_clean_n | 3716 | 3716 | True |
| bench_x_ind425_overlap | 211 | 211 | True |
| bench_x_ind425_same_label | 204 | 204 | True |
| bench_x_ind425_conflicting | 7 | 7 | True |
| ind425_regime_b_n | 214 | 214 | True |
| bench_x_ind1049_overlap | 298 | 298 | True |
| bench_x_ind1049_same_label | 286 | 286 | True |
| bench_x_ind1049_conflicting | 12 | 12 | True |
| ind1049_regime_b_n | 751 | 751 | True |

## 3. HEADLINE RESULT

**Primary hypothesis H1 (preregistered; outcome known from v1, see PREREGISTRATION.md section 0):** not supported. v1 numbers and the full v1 results are kept in the original sections below.

**H1, Regime B (recomputed with the v2 comparison code):**

| test_set | n | mcc_diff | mcc_diff_lo | mcc_diff_hi | auroc_diff | delong_p | mcnemar_p | mcc_mde80 | auroc_mde80 |
|---|---|---|---|---|---|---|---|---|---|
| ind_425 | 214 | -0.0168 | -0.0869 | 0.0556 | 0.0036 | 0.7732 | 0.4545 | 0.1034 | 0.0357 |
| ind_1049 | 751 | -0.0035 | -0.0484 | 0.0455 | 0.0018 | 0.8016 | 0.902 | 0.0658 | 0.02 |

**H2: lambda* vs lambda=0 for each architecture (Regime B; raw and BH-adjusted p side by side):**

| comparison | test_set | n | mcc_diff | mcc_diff_lo | mcc_diff_hi | delong_p | p_delong_bh_family | mcnemar_p | p_mcnemar_bh_family | supports_claim_rule |
|---|---|---|---|---|---|---|---|---|---|---|
| B3_bilstm lambda*=2 vs 0 | ind_425 | 214 | 0.1039 | 0.0051 | 0.2069 | 0.7924 | 0.7924 | 0.1859 | 0.6196 | False |
| B3_bilstm lambda*=2 vs 0 | ind_1049 | 751 | 0.0158 | -0.0403 | 0.0724 | 0.5732 | 0.7734 | 1.0 | 1.0 | False |
| B4_cnn_bilstm lambda*=2 vs 0 | ind_425 | 214 | 0.1274 | 0.0087 | 0.2378 | 0.3225 | 0.645 | 0.0258 | 0.2313 | False |
| B4_cnn_bilstm lambda*=2 vs 0 | ind_1049 | 751 | -0.004 | -0.0671 | 0.0639 | 0.1042 | 0.3474 | 0.9121 | 1.0 | False |
| B6_attnpool lambda*=2 vs 0 | ind_425 | 214 | -0.0582 | -0.1687 | 0.055 | 0.0566 | 0.283 | 0.4862 | 0.9725 | False |
| B6_attnpool lambda*=2 vs 0 | ind_1049 | 751 | 0.0623 | -0.0065 | 0.1317 | 0.1905 | 0.4763 | 0.0462 | 0.2313 | False |
| B2_cnn lambda*=0.1 vs 0 | ind_425 | 214 | -0.0282 | -0.1234 | 0.0696 | 0.6694 | 0.7734 | 1.0 | 1.0 | False |
| B2_cnn lambda*=0.1 vs 0 | ind_1049 | 751 | -0.0254 | -0.0829 | 0.0345 | 0.0141 | 0.1408 | 0.8391 | 1.0 | False |
| B5_transformer lambda*=2 vs 0 | ind_425 | 214 | -0.0294 | -0.1228 | 0.0546 | 0.5156 | 0.7734 | 0.8036 | 1.0 | False |
| B5_transformer lambda*=2 vs 0 | ind_1049 | 751 | -0.037 | -0.0844 | 0.011 | 0.696 | 0.7734 | 0.2821 | 0.7052 | False |

Comparisons meeting the preregistered support rule (BH-adjusted DeLong p < 0.05 and MCC-difference CI above 0): **0 of 10**.

Full reading: [INTERPRETATION_v2.md](INTERPRETATION_v2.md). v1 reading: [INTERPRETATION.md](INTERPRETATION.md).

**v1 detail:**

**5-fold CV, 8M checkpoint, tau=0.07 (mean/std over seeds x folds):**

| lambda_supcon | mcc_mean | mcc_std | auroc_mean | auroc_std |
|---|---|---|---|---|
| 0.0 | 0.2687 | 0.0229 | 0.6663 | 0.0175 |
| 0.1 | 0.2694 | 0.0223 | 0.6662 | 0.0167 |
| 0.25 | 0.2715 | 0.0243 | 0.6674 | 0.0166 |
| 0.5 | 0.272 | 0.0233 | 0.6678 | 0.0178 |
| 1.0 | 0.2702 | 0.0227 | 0.6672 | 0.0186 |
| 2.0 | 0.2746 | 0.0235 | 0.6702 | 0.016 |

**Regime B (leakage-free), 8M checkpoint, CV-selected lambda>0 minus lambda=0 (seed-ensemble predictions; 95% paired stratified bootstrap CIs, 2000 resamples):**

| test_set | lambda | tau | n | mcc_a | mcc_b | mcc_diff | mcc_diff_lo | mcc_diff_hi | auroc_a | auroc_b | auroc_diff | auroc_diff_lo | auroc_diff_hi | delong_p | mcnemar_p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ind_425 | 2.0 | 0.1 | 214 | 0.306 | 0.3228 | -0.0168 | -0.0869 | 0.0557 | 0.704 | 0.7004 | 0.0036 | -0.0222 | 0.0288 | 0.7732 | 0.4545 |
| ind_1049 | 2.0 | 0.1 | 751 | 0.2553 | 0.2589 | -0.0035 | -0.0484 | 0.0455 | 0.6829 | 0.6812 | 0.0018 | -0.0118 | 0.0158 | 0.8017 | 0.902 |

**Verdict (CV-selected lambda>0 model vs lambda=0):**

- ind_425 (lambda=2, tau=0.1): MCC difference -0.0168 [-0.0869, +0.0557], AUROC difference +0.0036 [-0.0222, +0.0288]; DeLong p = 0.7732 (NOT statistically significant (p >= 0.05)); McNemar p = 0.4545 (NOT statistically significant (p >= 0.05)).
- ind_1049 (lambda=2, tau=0.1): MCC difference -0.0035 [-0.0484, +0.0455], AUROC difference +0.0018 [-0.0118, +0.0158]; DeLong p = 0.8017 (NOT statistically significant (p >= 0.05)); McNemar p = 0.902 (NOT statistically significant (p >= 0.05)).

The full interpretation, including consistency across checkpoints and regimes, is in [INTERPRETATION.md](INTERPRETATION.md).

## 4. LEAKAGE IMPACT

Mean over 5 seeds of each model's per-seed metrics (threshold 0.5). Gap = Regime A minus Regime B.

| model | eval_set | mcc_A | mcc_B | mcc_C | auroc_A | auroc_B | auroc_C | mcc_gap_A-B | auroc_gap_A-B |
|---|---|---|---|---|---|---|---|---|---|
| AAC_DPC_CTD_LGBM | ind_1049 | 0.3695 | 0.3063 | 0.2927 | 0.7876 | 0.7291 | 0.7179 | 0.0631 | 0.0586 |
| AAC_DPC_CTD_LGBM | ind_425 | 0.3554 | 0.3187 | 0.3313 | 0.7907 | 0.7328 | 0.765 | 0.0367 | 0.0578 |
| AAC_RF | ind_1049 | 0.5516 | 0.3743 | 0.3571 | 0.8568 | 0.7568 | 0.75 | 0.1773 | 0.1 |
| AAC_RF | ind_425 | 0.6745 | 0.4251 | 0.4454 | 0.9234 | 0.7853 | 0.7957 | 0.2493 | 0.1381 |
| AAC_SVM | ind_1049 | 0.4312 | 0.2469 | 0.2347 | 0.7893 | 0.6841 | 0.6823 | 0.1844 | 0.1052 |
| AAC_SVM | ind_425 | 0.5401 | 0.311 | 0.3177 | 0.8634 | 0.7382 | 0.7463 | 0.2291 | 0.1252 |
| esm2_t12_35M_LR | ind_1049 | 0.3061 | 0.272 | 0.2774 | 0.6929 | 0.6684 | 0.6693 | 0.0341 | 0.0245 |
| esm2_t12_35M_LR | ind_425 | 0.2319 | 0.1224 | 0.1414 | 0.6572 | 0.5867 | 0.5773 | 0.1095 | 0.0705 |
| esm2_t12_35M_lam0.5_tau0.07 | ind_1049 | 0.3359 | 0.2098 | 0.2066 | 0.732 | 0.6559 | 0.6567 | 0.1261 | 0.076 |
| esm2_t12_35M_lam0.5_tau0.07 | ind_425 | 0.472 | 0.3029 | 0.3038 | 0.7858 | 0.6767 | 0.6818 | 0.1691 | 0.1091 |
| esm2_t12_35M_lam0_tau0.07 | ind_1049 | 0.3453 | 0.2228 | 0.2187 | 0.7338 | 0.6619 | 0.6625 | 0.1224 | 0.0719 |
| esm2_t12_35M_lam0_tau0.07 | ind_425 | 0.4474 | 0.2667 | 0.2733 | 0.7784 | 0.6666 | 0.6773 | 0.1807 | 0.1119 |
| esm2_t30_150M_LR | ind_1049 | 0.3153 | 0.2317 | 0.22 | 0.7177 | 0.6664 | 0.6668 | 0.0837 | 0.0513 |
| esm2_t30_150M_LR | ind_425 | 0.2737 | 0.196 | 0.1803 | 0.712 | 0.642 | 0.6437 | 0.0777 | 0.0701 |
| esm2_t30_150M_lam0_tau0.07 | ind_1049 | 0.3534 | 0.2323 | 0.228 | 0.7323 | 0.6578 | 0.657 | 0.121 | 0.0745 |
| esm2_t30_150M_lam0_tau0.07 | ind_425 | 0.407 | 0.2657 | 0.2622 | 0.7585 | 0.6599 | 0.659 | 0.1414 | 0.0986 |
| esm2_t30_150M_lam2_tau0.07 | ind_1049 | 0.3343 | 0.1788 | 0.1688 | 0.7261 | 0.6387 | 0.6365 | 0.1555 | 0.0874 |
| esm2_t30_150M_lam2_tau0.07 | ind_425 | 0.4128 | 0.2118 | 0.1992 | 0.7639 | 0.6417 | 0.6434 | 0.201 | 0.1222 |
| esm2_t33_650M_lam0_tau0.07 | ind_1049 | 0.4006 | 0.265 | 0.2512 | 0.7537 | 0.6692 | 0.663 | 0.1356 | 0.0846 |
| esm2_t33_650M_lam0_tau0.07 | ind_425 | 0.5164 | 0.3296 | 0.3084 | 0.8126 | 0.701 | 0.701 | 0.1868 | 0.1116 |
| esm2_t33_650M_lam1_tau0.05 | ind_1049 | 0.3864 | 0.2263 | 0.2161 | 0.7457 | 0.6496 | 0.6454 | 0.1601 | 0.0962 |
| esm2_t33_650M_lam1_tau0.05 | ind_425 | 0.5322 | 0.3131 | 0.3044 | 0.82 | 0.698 | 0.6888 | 0.2191 | 0.122 |
| esm2_t6_8M_LR | ind_1049 | 0.3341 | 0.2879 | 0.2774 | 0.7061 | 0.6764 | 0.6704 | 0.0462 | 0.0296 |
| esm2_t6_8M_LR | ind_425 | 0.2951 | 0.2135 | 0.2321 | 0.6826 | 0.621 | 0.6338 | 0.0816 | 0.0616 |
| esm2_t6_8M_lam0.1_tau0.07 | ind_1049 | 0.3641 | 0.2306 | 0.2235 | 0.7415 | 0.6637 | 0.6617 | 0.1335 | 0.0778 |
| esm2_t6_8M_lam0.1_tau0.07 | ind_425 | 0.4416 | 0.2586 | 0.279 | 0.7855 | 0.6826 | 0.7028 | 0.183 | 0.1029 |
| esm2_t6_8M_lam0.25_tau0.07 | ind_1049 | 0.3581 | 0.238 | 0.2332 | 0.7395 | 0.6634 | 0.6622 | 0.1201 | 0.0761 |
| esm2_t6_8M_lam0.25_tau0.07 | ind_425 | 0.4177 | 0.2405 | 0.2818 | 0.7754 | 0.6783 | 0.7063 | 0.1772 | 0.097 |
| esm2_t6_8M_lam0.5_tau0.07 | ind_1049 | 0.3698 | 0.2403 | 0.2361 | 0.7409 | 0.6653 | 0.6636 | 0.1295 | 0.0755 |
| esm2_t6_8M_lam0.5_tau0.07 | ind_425 | 0.4397 | 0.2588 | 0.2761 | 0.7675 | 0.6707 | 0.6785 | 0.1809 | 0.0968 |
| esm2_t6_8M_lam0_tau0.07 | ind_1049 | 0.3861 | 0.2362 | 0.2339 | 0.7548 | 0.6668 | 0.667 | 0.1498 | 0.088 |
| esm2_t6_8M_lam0_tau0.07 | ind_425 | 0.4841 | 0.247 | 0.252 | 0.8037 | 0.6915 | 0.7062 | 0.237 | 0.1122 |
| esm2_t6_8M_lam1_tau0.07 | ind_1049 | 0.3398 | 0.2087 | 0.2001 | 0.7331 | 0.6577 | 0.6554 | 0.1311 | 0.0753 |
| esm2_t6_8M_lam1_tau0.07 | ind_425 | 0.4311 | 0.2393 | 0.2839 | 0.7717 | 0.6675 | 0.6863 | 0.1918 | 0.1042 |
| esm2_t6_8M_lam2_tau0.07 | ind_1049 | 0.3639 | 0.2244 | 0.2178 | 0.7451 | 0.6652 | 0.6639 | 0.1396 | 0.0799 |
| esm2_t6_8M_lam2_tau0.07 | ind_425 | 0.4723 | 0.2797 | 0.3111 | 0.7883 | 0.6837 | 0.7032 | 0.1925 | 0.1046 |
| esm2_t6_8M_lam2_tau0.1 | ind_1049 | 0.4035 | 0.2273 | 0.2229 | 0.7648 | 0.6628 | 0.662 | 0.1762 | 0.1019 |
| esm2_t6_8M_lam2_tau0.1 | ind_425 | 0.5544 | 0.3011 | 0.2948 | 0.8264 | 0.6915 | 0.6972 | 0.2533 | 0.1349 |

## 5. FULL RESULTS

| File | Rows |
|---|---|
| results/tables/T3.5_cross_benchmark_leakage.csv | 9 |
| results/tables/T3.5b_cdhit_style_clustering.csv | 16 |
| results/tables/T5.10_cross_benchmark.csv | 126 |
| results/tables/T5.11_corrected_significance.csv | 126 |
| results/tables/T5.11b_seed_vs_sample_variance.csv | 58 |
| results/tables/T5.11c_cv_effect_sizes.csv | 30 |
| results/tables/T5.8_architecture_comparison.csv | 6 |
| results/tables/T5.8b_architecture_all_regimes.csv | 72 |
| results/tables/T5.9_representation_comparison.csv | 26 |
| results/tables/TF1_negatives_fragment_test.csv | 10 |
| results/tables/TF2_motif_enrichment.csv | 45 |
| results/tables/TF3_error_analysis.csv | 3 |
| results/tables/TF3b_errors_by_number_of_models_wrong.csv | 19 |
| results/tables/TF5_length_stratified.csv | 77 |
| results/v2/architecture_layers.csv | 41 |
| results/v2/comparisons_raw.csv | 126 |
| results/v2/cross_benchmark_results_v2.csv | 630 |
| results/v2/cv_results_v2.csv | 750 |
| results/v2/environment.csv | 24 |
| results/v2/feature_dimensions.csv | 6 |
| results/v2/final_results_v2.csv | 300 |
| results/v2/finetune_results_v2.csv | 90 |
| results/v2/half_precision_check.csv | 2 |
| results/v2/hardest_sequences.csv | 61 |
| results/v2/kaggle_runtimes.csv | 5 |
| results/v2/lineage_shared_training.csv | 10 |
| results/v2/mde_summary.csv | 6 |
| results/v2/methods_parameters.csv | 53 |
| results/v2/nested_cv_8M.csv | 25 |
| results/v2/nested_cv_8M_partial.csv | 25 |
| results/v2/null_control_identity.csv | 126 |
| results/v2/pooling_dimensions.csv | 5 |
| results/v2/regime_composition.csv | 7 |
| results/v2/repr_results_v2.csv | 1100 |
| results/v2/sequence_validation.csv | 9 |
| results/v2/supcon_floor.csv | 2 |

v1 files:

| File | Rows | Contents |
|---|---|---|
| results/data_audit.csv | 78 | Tidy dataset audit and cross-set overlap table (Table 3.1/3.2) |
| results/s1_verification.csv | 14 | S1 hard-gate expected vs actual |
| results/identity_screen.csv | 10 | Sequences removed per identity threshold (0.8/0.9/0.95/1.0 and exact) |
| results/embedding_timings.csv | 4 | ESM-2 embedding wall-clock, device, peak memory per checkpoint |
| results/cv_results.csv | 1200 | Deep model CV rows: one row per (config, seed, fold), all 8 metrics |
| results/baseline_results.csv | 330 | Baselines 1-4: CV rows and independent-set rows (Regimes A/B/C) |
| results/final_results.csv | 390 | Deep final models, per seed, independent sets x regimes, threshold 0.5 |
| results/final_results_tuned.csv | 390 | Same, threshold tuned on a 10% hold-out of the training data |
| results/selected_models.json | - | Which (lambda, tau) was selected per checkpoint by CV |
| results/stats_tests.csv | 54 | DeLong, McNemar and paired-bootstrap CIs, lambda>0 vs lambda=0 |
| results/stats_per_seed.csv | 270 | Per-seed paired differences and DeLong p-values |
| results/bootstrap_cis.csv | 78 | 95% bootstrap CIs for AUROC and MCC of every final model |
| results/tables/ | 44 | Thesis tables as CSV + LaTeX |
| results/predictions/ | 114 | Per-sample predictions |
| results/latents/ | 26 | Latent vectors for t-SNE |
| results/models/ | 66 | Final model weights + scalers |

## 6. FIGURES

fig3_1_dataset_lineage.png, fig3_2_aipnet_architecture.png, fig5_10_cross_benchmark_heatmap.png, fig5_1_roc_ind_1049_regimeA.png, fig5_1_roc_ind_1049_regimeB.png, fig5_1_roc_ind_425_regimeA.png, fig5_1_roc_ind_425_regimeB.png, fig5_2_pr_ind_1049_regimeB.png, fig5_2_pr_ind_425_regimeB.png, fig5_3_tsne_ind_1049.png, fig5_3_tsne_ind_425.png, fig5_4_lambda_sweep.png, fig5_5_leakage_gap.png, fig5_6_confusion_matrices.png, fig5_8_architecture_lambda.png, fig5_9_pooling_ablation.png, fig5_9b_fusion_finetune.png, figA_training_curves.png, figF1_negative_resemblance.png, figF2_residue_enrichment.png, figF5_length_stratified.png

v1 figure status:

| Figure | Status |
|---|---|
| F5.1 ROC Ind_425 B | ok: figures/fig5_1_roc_ind_425_regimeB.pdf, figures/fig5_1_roc_ind_425_regimeB.png |
| F5.1 ROC Ind_1049 B | ok: figures/fig5_1_roc_ind_1049_regimeB.pdf, figures/fig5_1_roc_ind_1049_regimeB.png |
| F5.1 ROC Ind_425 A | ok: figures/fig5_1_roc_ind_425_regimeA.pdf, figures/fig5_1_roc_ind_425_regimeA.png |
| F5.1 ROC Ind_1049 A | ok: figures/fig5_1_roc_ind_1049_regimeA.pdf, figures/fig5_1_roc_ind_1049_regimeA.png |
| F5.2 PR Ind_425 B | ok: figures/fig5_2_pr_ind_425_regimeB.pdf, figures/fig5_2_pr_ind_425_regimeB.png |
| F5.2 PR Ind_1049 B | ok: figures/fig5_2_pr_ind_1049_regimeB.pdf, figures/fig5_2_pr_ind_1049_regimeB.png |
| F5.3 t-SNE Ind_1049 | ok: figures/fig5_3_tsne_ind_1049.pdf, figures/fig5_3_tsne_ind_1049.png |
| F5.3 t-SNE Ind_425 | ok: figures/fig5_3_tsne_ind_425.pdf, figures/fig5_3_tsne_ind_425.png |
| F5.4 lambda sweep | ok: figures/fig5_4_lambda_sweep.pdf, figures/fig5_4_lambda_sweep.png |
| F5.5 leakage gap | ok: figures/fig5_5_leakage_gap.pdf, figures/fig5_5_leakage_gap.png |
| F5.6 confusion matrices | ok: figures/fig5_6_confusion_matrices.pdf, figures/fig5_6_confusion_matrices.png |
| FA training curves | ok: figures/figA_training_curves.pdf, figures/figA_training_curves.png |

Files in figures/: fig3_1_dataset_lineage.pdf, fig3_1_dataset_lineage.png, fig3_2_aipnet_architecture.pdf, fig3_2_aipnet_architecture.png, fig5_10_cross_benchmark_heatmap.pdf, fig5_10_cross_benchmark_heatmap.png, fig5_1_roc_ind_1049_regimeA.pdf, fig5_1_roc_ind_1049_regimeA.png, fig5_1_roc_ind_1049_regimeB.pdf, fig5_1_roc_ind_1049_regimeB.png, fig5_1_roc_ind_425_regimeA.pdf, fig5_1_roc_ind_425_regimeA.png, fig5_1_roc_ind_425_regimeB.pdf, fig5_1_roc_ind_425_regimeB.png, fig5_2_pr_ind_1049_regimeB.pdf, fig5_2_pr_ind_1049_regimeB.png, fig5_2_pr_ind_425_regimeB.pdf, fig5_2_pr_ind_425_regimeB.png, fig5_3_tsne_ind_1049.pdf, fig5_3_tsne_ind_1049.png, fig5_3_tsne_ind_425.pdf, fig5_3_tsne_ind_425.png, fig5_4_lambda_sweep.pdf, fig5_4_lambda_sweep.png, fig5_5_leakage_gap.pdf, fig5_5_leakage_gap.png, fig5_6_confusion_matrices.pdf, fig5_6_confusion_matrices.png, fig5_8_architecture_lambda.pdf, fig5_8_architecture_lambda.png, fig5_9_pooling_ablation.pdf, fig5_9_pooling_ablation.png, fig5_9b_fusion_finetune.pdf, fig5_9b_fusion_finetune.png, figA_training_curves.pdf, figA_training_curves.png, figF1_negative_resemblance.pdf, figF1_negative_resemblance.png, figF2_residue_enrichment.pdf, figF2_residue_enrichment.png, figF5_length_stratified.pdf, figF5_length_stratified.png

## 7. BLOCKERS


Everything in the v2 extension that failed or could not be done.

## AIPFusion-Net could not be read
_2026-11-25_

The plan cites AIPFusion-Net (doi 10.3389/fmolb.2026.1952395). The DOI resolves to frontiersin.org, which returned HTTP 503 to automated requests, and web search found no record of the paper. Every statement about what that paper claims or used (training counts, "no overlapping peptide sequences", CD-HIT thresholds, Ind-426) is therefore taken from the plan text and is UNVERIFIED by me. The leakage finding below is stated only as a measurement on the local files and on the original AIPpred / AntiInflam / PreAIP files.

## AIPStack independent sets 2 and 3 not obtainable
_2026-11-25_

The AIPStack paper (PMC9449674) returned a bot-check page, and the Nicole-DH/AIPStack GitHub repository returned 404 (and the GitHub API was rate-limited). Those datasets are therefore not in the cross-benchmark matrix. If you can get the files, drop them into `data/external/aipstack_*/` and re-run `python -m src.v2.phaseA`.

## C4 (ProtBERT / ProtT5) not attempted
_2026-11-25_

C4 is optional in the plan. ProtBERT needs a 1.6 GB and ProtT5-XL (half, encoder) a 2.3 GB download; this Mac had 3.7 GB of free disk (which fluctuates), and the Kaggle kernels have no internet, so the weights would need uploading as a dataset. The question C4 asks (is the weakness ESM-2 specific?) is partly answered by C3: end-to-end adaptation of the same ESM-2 backbone changes the result, so the frozen-embedding setting rather than ESM-2 itself is implicated. To run it: `python -m src.v2.embed_res` generalised to `Rostlab/prot_bert` (sequences need spaces between residues), then `python -m src.v2.phaseC` with the new features.

## D3 (AMP / ACP related-task transfer) not attempted
_2026-11-25_

D3 is optional. It needs antimicrobial or anticancer peptide datasets; no verified download URL was in the plan, and I did not guess one. Phase D2 (cross-dataset generalisation) was run on every AIP dataset that could be obtained (AIPpred, AntiInflam and the local composite).

## Fine-tuning scope and GPU determinism
_2026-11-25_

Only ESM-2 8M was fine-tuned (CV seeds 0-2 x 5 folds, final seeds 0-4). Fine-tuning 150M or 650M was not run. B2, B5 and the fine-tuning ran on Kaggle T4 GPUs, whose floating-point reductions are not bit-identical to the CPU runs used for B3, B4, B6 and v1; each architecture's lambda grid is entirely on one device (results/v2/device_map.json).


Everything that failed or could not run, with diagnosis.

## T5.7 needs published numbers
_2026-11-25T08:04:09_

Table 5.7 (comparison with AIPpred, PreAIP, etc.) contains only this study's Regime A results. No verified published figures were available to the run and none were invented; copy them from the original papers into `results/tables/T5_7_comparison_published.csv`.

## Housekeeping: latent vectors were briefly committed
_2026-11-25_

`results/latents/*.npz` (36 MB; they contain copies of raw ESM-2 embeddings) were committed in f2c18a4 before the ignore rule existed, and untracked in ed4fdc8 (and gitignored). The repository has no remote, so nothing was pushed; the files remain in local history. To purge them: `git filter-repo --path results/latents --invert-paths` (rewrites history, so I did not do it unasked).

## 8. DECISIONS


Choices made during the v2 extension (EXECUTION_PLAN_v2.md). The v1 DECISIONS.md and BLOCKERS.md are left untouched; HANDOFF_REPORT.md section 8 embeds both.

## V2-D1: Plan wins; v2 writes only new files
_2026-11-25_

Per the run brief, nothing from S1-S12 is modified or re-run. New code lives in `src/v2/`, new results in `results/v2/` plus plan-named files (`results/provenance.csv`, `results/tables/T*.csv`), and v2 decisions/blockers go to `DECISIONS_v2.md` / `BLOCKERS_v2.md`. Only HANDOFF_REPORT.md is rewritten, by `src/v2/report.py`, which keeps the v1 status table and result sections.

## V2-D2: latents purge already done before the first push
_2026-11-25_

The brief asks to purge `results/latents` from history with git filter-repo before the first push. git-filter-repo is not installed; I had already removed that directory from every commit with `git filter-branch --index-filter` (equivalent result) before the first push, and verified `git log --all` contains no latents path. No further action needed.

## V2-D3: External downloads are plain-text data, each in its own directory
_2026-11-25_

All dataset downloads (AIPpred, PreAIP, AntiInflam) are small text files fetched from the authors' stated pages (AntiInflam and PreAIP via Wayback Machine snapshots because the original servers are offline). Each file sits in its own directory under `data/external/`, is parsed only as text with `python -I`, validated to contain only sequence lines, and recorded with URL and SHA-256 in `results/external_sources.csv`.

## V2-D4: CD-HIT is re-implemented, not the binary
_2026-11-25_

CD-HIT / CD-HIT-2D are not installed and not available as a Homebrew formula. I implemented the CD-HIT greedy incremental algorithm (length-sorted, identity = matches over the shorter sequence's length) in `src/v2/common.py` and label every result "CD-HIT-style". It will not reproduce CD-HIT's exact cluster counts, so counts are compared as approximate corroboration only.

## V2-D5: Third-party dataset files stay out of git
_2026-11-25_

`data/external/` (downloaded AIPpred / PreAIP / AntiInflam text files, ~0.3 MB) is added to `.gitignore` (a one-line housekeeping change to an existing file, necessary so redistributed third-party data is not published). Reproducibility is preserved by `results/external_sources.csv` (URL-derived path, byte count, SHA-256) and the download URLs in `results/provenance.csv`.

## V2-D6: Phase A gate passed; the premise stands, with a refined mechanism
_2026-11-25_

The 211 / 298 overlap reproduced exactly, so the run continues. The measured mechanism is more specific than the plan's framing: the local Benchmark is a composite of the AIPpred benchmark and AntiInflam training sequences, and the overlaps come from each source's cross-literature overlap with the other's independent set. Claims about AIPFusion-Net remain unverified and are not made.

## V2-D7: Residue-level architectures use a learned per-residue bottleneck (d -> 64)
_2026-11-25_

Unadapted 320-d (and 1280-d) residue input made a single CNN fold take about 20 minutes on one M1 core (1.2 s per step), which makes the pre-specified 750-run Phase B grid impossible. B2-B5 therefore start with a learned Linear(d, 64)+ReLU+Dropout(0.2) applied per residue, then the named architecture (CNN kernels 3/5/7 with 64 channels each; 2-layer BiLSTM with 64 hidden units per direction; CNN-BiLSTM with 64 channels and 64 hidden; 2-layer 4-head Transformer encoder with d_model 128 and learned positions). The LSTM hidden size is 64 rather than the 128 in the plan for the same reason. B6 (attention pooling) keeps the full-width vector so that B1 vs B6 isolates pooling. Gradient-norm clipping at 1.0 is applied to all Phase B models for stability. These choices are fixed before seeing any Phase B result.

## V2-D8: Phase B runs on 6 CPU workers; the 650M residue cache is float16
_2026-11-25_

The 8 GB machine swapped heavily while the 650M embedding ran alongside training (swap 4.7 GB, 1.2 s per tiny step), so training was started only after the embedding finished. 650M residue vectors are stored as float16 (max abs difference from the v1 float32 pooled embedding 0.0018, relative 2e-4); the 8M residue cache is float32 and reproduces v1 pooled embeddings to 1e-6.

## V2-D9: Kaggle GPU for Phase B (CNN, Transformer, attention-pool) and C3; foreground slices locally
_2026-11-25_

At your request the Kaggle GPU (new account, 2x Tesla T4, no internet) is used where it pays off: Phase B CV and final models for B2_cnn, B5_transformer and B6_attnpool, and the C3 fine-tuning. B3_bilstm was completed on CPU before the switch, and B4_cnn_bilstm is finished on CPU, so every architecture's lambda grid (and its lambda=0 baseline) is trained on one device; GPU and CPU runs of the same architecture are never mixed. Local jobs run in the foreground in time-budgeted slices that write a flushed line per CV run to `results/phase_b_progress.log`; the pool of 6 worker processes inside each foreground call is retained because serial execution would take about 20 hours (say if you want it serial). Kaggle inputs are a private dataset (code, splits, 8M embeddings, 8M weights) in the user's own account.

## V2-D10: Resume bug found and fixed
_2026-11-25_

The first resumed slice re-ran 22 already-saved CNN-BiLSTM runs because `pd.read_csv(usecols=...)` returns columns in file order, not list order, so the resume keys never matched. The 22 duplicate rows were dropped (originals kept), the lookup now selects columns explicitly, and the fix is noted in `results/phase_b_progress.log`. Phases C, D, E and the fine-tuning script use `usecols` in an order that equals file order and were checked.

## V2-D11: One reference point for identity figures: Benchmark_clean
_2026-11-25_

The 0.9-identity counts were 263 (Ind_425) against the cleaned benchmark in Chapter 3 and 264 in `LEAKAGE_FINDING.md`, which had screened against the raw benchmark (3,753 unique sequences including the 37 conflicted ones). Benchmark_clean (3,716 sequences) is the training collection used for every model and for Regime C, so it is now the only reference point: `src/v2/phaseA.py` was changed accordingly, T3.5 and T3.5b were regenerated (263 = 61.9% and 333 = 31.7%), and `LEAKAGE_FINDING.md` and `INTERPRETATION_v2.md` were corrected. The text of Chapter 3 states which benchmark the figures refer to.

## V2-D12: 650M extraction time deleted, not re-measured
_2026-11-25_

The overnight brief allowed a re-timing only if it took under 15 minutes on an unloaded machine. The 2.6 GB checkpoint could not be re-downloaded (2.0 GB of disk free), so the number was removed and the text says that the timing was not reliably measurable. The half-precision cache check was re-run over all 4,641 sequences and saved (`results/v2/half_precision_check.csv`); the text now cites that file.

## V2-D13: Bibliography built only from indexed records; unverifiable items dropped
_2026-11-25_

`src/thesis/build_bib.py` writes `references.bib` / `references.json` using only CrossRef records (title similarity >= 0.90, first author and year matched) and arXiv records fetched by identifier and re-checked on title, first author and year. 26 works were verified. The Cai et al. (2003) citation for CTD was removed because the record that matched is the SVM-Prot paper and nothing verified shows it defines CTD; LightGBM (Ke et al.) could not be matched and is mentioned without a citation. Conference papers (Khosla et al., Vaswani et al., Ilse et al., Loshchilov and Hutter, Paszke et al., Pedregosa et al.) are cited as the arXiv preprints, with the year of the arXiv record (Loshchilov and Hutter is therefore 2017, not 2019); their conference venues were not verified and are not stated.

## V2-D14: Fine-tuned 8M vs frozen 650M added to the corrected comparison families
_2026-11-25_

To answer whether fine-tuned 8M beats frozen 650M, the comparison was added to Phase E and the corrections re-run (126 comparisons). No significance flag changed; adjusted p-values moved by at most 0.0055 and the few quoted values in `INTERPRETATION_v2.md` were updated.

## V2-D15: The "inflation is largest for high-capacity models" claim is not stated as given
_2026-11-26_

The overnight brief asked Chapters 1, 5 and 6 to say that the leakage inflation is largest for high-capacity models. The A-minus-B MCC gap does not support that as a monotonic statement: it is smallest for linear classifiers on frozen embeddings (about 0.05 to 0.09) and for LightGBM (0.04 to 0.06), large for the random forest (0.249 / 0.177), the RBF SVM (0.229 / 0.184), the CNN (0.285 / 0.211), the 8M MLP (0.237 / 0.150) and the 650M fusion random forest (0.337 / 0.188), and the frozen 650M MLP, the Transformer and the fine-tuned 8M model are no larger than AAC + RF. The thesis therefore says "largest for flexible non-linear models, not a monotonic function of capacity" (Ch. 1, 5.4.3, 6.1, abstract) and does not test differences between gaps formally.

## V2-D16: Chapter 1 reframed around three measured findings; Chapter 2 rebuilt on verified sources only
_2026-11-26_

Chapters 1 and 2 were rebuilt by `src/thesis/ch1.js` and `ch2.js` (originals kept as `CHAPTER 1/2 thesis (original).docx`, local only). Removed because no record could be matched: AIEpred / Pep-CNN / IALP; PreAIP's feature list beyond the abstract; "ESM consistently outperforms traditional encodings"; "contrastive learning applied effectively in bioinformatics"; the NF-kB / MAPK / LPS-binding mechanism sentence (replaced by two examples that the AIPpred introduction states, with the second-hand status said in the text). Full list in `CITATIONS_TO_VERIFY.md`.

## V2-D17: Table 5.16 carries abstract-level published figures only
_2026-11-26_

`results/tables/T5_7_comparison_published.csv` holds only our own results. Table 5.16 in Chapter 5 lists the figures that the abstracts of AIPpred (independent AUC 0.814), PreAIP (test AUC 0.840), AIPStack (independent set 3: AUC 0.819, MCC 0.510) and AntiInflam (validation MCC 0.31 for RF) report, each marked as abstract-only, and TODO everywhere else. No published number was entered from memory.

## V2-D18: Pre-registration timing stated precisely
_2026-11-26_

The text previously said the plan was committed "before the extended experiments". The audit (Phase A) was run first and the pre-registration (commit c239f43, 2026-11-25T14:36:00Z) followed it, so Chapters 3, 4 and 6 now say "after the audit of Phase A and before the experiments of Phases B to F".

## V2-D19: Chapter label namespace
_2026-11-26_

Table labels are shared across chapters through `results/thesis/labels_chN.csv`; two chapter-5 labels (`tab:pooling`, `tab:mde`) collided with chapter-3 labels and were renamed (`tab:pool5`, `tab:mde5`, `tab:ft5`). Each chapter must be built twice, in order 1 to 6, so that every cross-reference resolves.


Choices made autonomously during the overnight run, each with the reasoning.

## D1: CLAUDE.md does not exist; the playbook docx is the ground truth
_2026-11-21_

The run prompt refers to CLAUDE.md, but no such file exists in the folder. `AIP Thesis — Build Plan & Claude Code Prompt Playbook.docx` contains every item the prompt attributes to CLAUDE.md (verified dataset numbers, architecture, rules, experiment matrix, tables/figures), so I treated it as the ground truth and mapped S1-S12 onto its Prompts 1-14.

## D2: Repo root is /Users/sayemuddin/Desktop/Yassir_Thesis (git init here)
_2026-11-21_

The folder was not a git repository. I initialised git in place, using the playbook's `aip-supcon` layout inside it, and ignore the thesis .docx files and root-level FASTA copies; raw FASTAs are copied to data/raw/ (gitignored per the rules).

## D3: Python 3.11 venv, CPU/MPS only
_2026-11-21_

Python 3.14 has patchy ML wheel support, so I used Homebrew Python 3.11 in .venv with pinned versions in requirements.txt. This Mac (M1, 8 GB RAM) has no CUDA; all compute is CPU unless noted.

## D4: Kaggle GPU is not used
_2026-11-21_

The run prompt defines the fallback as CPU plus a BLOCKERS entry, and the Kaggle account was only just switched (new, unverified for internet access). Anything that cannot run locally is listed in BLOCKERS.md with the exact command.

## D5: Identity definition for Regime C
_2026-11-21_

Identity is the matches in a global Needleman-Wunsch alignment (Biopython, BLOSUM62, gap open -10 / extend -0.5) divided by the length of the shorter sequence, as the playbook specifies. Pairs are pre-filtered with an exact LCS upper bound (LCS/min_len < 0.8 cannot reach 0.8 identity), so the filter loses nothing; note that normalising by the shorter sequence also flags short test peptides fully contained in longer training peptides (25 extra sequences at threshold 1.0 in Ind_425).

## D6: All four ESM-2 checkpoints are embedded locally on CPU
_2026-11-21_

The prompt's fallback was "8M and 35M on CPU, the rest to BLOCKERS". The 8M model embeds all 4,641 unique sequences in 26 s on this M1, so 150M and 650M are also feasible on CPU (short peptides, ~18 tokens). I run them locally and keep CUDA detection in the code; if the 650M checkpoint cannot be downloaded (disk) or fits poorly, it goes to BLOCKERS.md with the Kaggle command. Each downloaded checkpoint is purged from the HF cache after embedding to protect the nearly-full disk.

## D7: SupCon "near-zero loss" test uses the analytic floor
_2026-11-21_

The playbook says perfectly clustered embeddings should give near-zero loss, but for the L_out form the minimum is log|P(i)| when an anchor has |P| positives (the positives share the denominator). The tests therefore assert near-zero only for |P|=1 (2 samples per class) and assert the analytic floor log(7) for 8 samples per class, plus a naive-loop reference comparison; this is the correct mathematics, not a weaker test.

## D8: Frozen 8M ESM-2 underperforms AAC+RF; proceed anyway
_2026-11-25_

Sanity check before the grid: AAC+length RF reaches 5-fold CV AUROC 0.7735 (playbook: ~0.77, pipeline OK), while 8M mean-pooled ESM-2 gives LR 0.63 and the MLP 0.667 (embedding cache verified identical to fresh embeddings, pooling asserted padding-invariant). So the embedding is genuinely less informative than composition for this benchmark, not a pipeline bug; I continue with the specified protocol and report this plainly rather than tuning the architecture to rescue it.

## D9: CV protocol details
_2026-11-25_

For each seed s the 5 folds use StratifiedKFold(shuffle, random_state=s), and the model seed is 1000*s+fold, so lambda=0 and lambda>0 see identical splits, initial weights and batch order. CV rows report metrics at threshold 0.5 (threshold-free AUROC/AUPRC are unaffected); the tuned threshold is applied only to final models, tuned on the 10% hold-out and never on test data. SupCon is computed on every step even at lambda=0 (multiplied by 0) so both settings share a single code path and its value can be logged.

## D10: Environment repairs
_2026-11-25_

While the session was idle the venv lost its python symlinks and torch's compiled libraries (macOS refused to load them); I rebuilt .venv from requirements.txt (pinned) and restarted the embeddings that had failed because of it. Disk free space swings between ~0.1 and ~8 GB for reasons outside this project, so embed.py has a free-space preflight that writes a BLOCKERS entry instead of risking a full disk.

## D11: Exploratory two-view feature-space augmentation (not part of the pre-specified grid)
_2026-11-25_

The playbook names feature-space augmentation as the first thing to try if SupCon results are flat, and the 8M sweep was flat, so I ran two stochastic dropout views per sample (with and without Gaussian input noise sigma=0.1 on standardised features) over all six lambdas at 8M. Rows are stored with family `deep_explore`, kept out of every selection step and headline table to avoid selecting on extra comparisons; CV MCC stayed within about 0.271-0.278 for all 12 configs (lambda=0 two-view baseline 0.274), so augmentation does not change the conclusion.

## D12: Best lambda sits on the edge of the pre-specified grid
_2026-11-25_

Lambda=2.0 was CV-best at 8M and 150M, the upper end of the grid {0,...,2}. I did not extend the grid (it was specified in the brief and extending it after seeing results would add selection freedom); the mean CV gain at lambda=2 is 0.006 MCC against a fold/seed std of about 0.023, so extending would be unlikely to change the conclusion, but it is listed in NEXT ACTIONS.

## D13: Statistics use seed-ensemble predictions
_2026-11-25_

DeLong, McNemar and bootstrap CIs compare the mean probability of the 5 seeds' final models (one prediction vector per model, as the paired tests require); y_pred uses threshold 0.5. Seed-to-seed variance is reported separately in stats_per_seed.csv (per-seed MCC/AUROC difference and per-seed DeLong p-value), because the ensemble comparison treats test-sample noise only and ignores training noise.

## D14: Headline model per checkpoint is (lambda*, tau*) from CV, in the pre-specified order
_2026-11-25_

The first S9 pass trained the 8M "best" model at the default tau=0.07 because the 8M temperature sweep had not yet run; the sweep then selected tau=0.1 at lambda=2. Following the order lambda sweep -> temperature sweep at best lambda -> final models, I trained (lambda=2, tau=0.1) and made it the headline 8M model; the earlier (lambda=2, tau=0.07) model stays in the lambda ablation and in every table, so nothing is hidden. Roles are now assigned deterministically at the end of S9.

## 9. NEXT ACTIONS

Ranked, most important first:

1. **Read `LEAKAGE_FINDING.md` and `INTERPRETATION_v2.md`, then fix the thesis framing.** The data support: (a) the cross-lineage overlap mechanism as the headline contribution, (b) the contrastive objective as a well-powered null (no detectable effect larger than about 0.08-0.14 MCC; every Regime-B survivor of correction is negative), (c) end-to-end fine-tuning (+0.15 to +0.22 MCC over frozen) as the constructive finding. Soften Chapter 1's "superior predictive stability" accordingly.
2. **Verify the AIPFusion-Net claims yourself.** The paper could not be fetched (HTTP 503) and I found no trace of it, so nothing about its training counts, overlap statement or CD-HIT thresholds is verified. If you can open it in a browser, check those three things before any sentence about it enters the thesis; keep the finding framed as a measurement on the distributed files.
3. **Fine-tune larger checkpoints on the Kaggle GPU** (150M, then 650M). The fine-tune script and kernel pattern work (`data/external/kaggle_kernel_C3`), but the weights need uploading as a dataset (no internet on kernels). This tests whether the frozen-vs-fine-tuned gap persists at scale and whether fine-tuned models overtake AAC+RF on Ind_425.
4. **Fill Table 5.7** with published AIPpred / PreAIP / AntiInflam numbers from the original papers (none were available to me; none were invented).
5. **Optional extensions:** C4 (ProtBERT/ProtT5; needs 1.6-2.3 GB of weights), D3 (AMP/ACP transfer; needs verified dataset URLs), AIPStack independent sets (the GitHub repo returned 404). Details in `BLOCKERS_v2.md`.
6. **Chapters 1-2 fixes and Chapters 3-6 drafting** (playbook Prompts 12-14) remain to do and now have far more material: the mechanism section, T3.5, T5.8-T5.11, the preregistration and the power analysis.
7. **Housekeeping.** The Kaggle dataset `aip-supcon-data` and two kernels are private in the `yeasinarafatshihab` account and can be deleted if not wanted. Local free disk fluctuates (3-8 GB); the 650M weights are purged after use.

## 10. THESIS WRITING STATUS (overnight run, part 2)

**Chapters (the .docx files are local and gitignored; the build scripts are in `src/thesis/`, run each twice in order 1 to 6).**

| Part | Status | Pages | Tables | Figures | Verified citations | TODO | [CITATION NEEDED] |
|---|---|---|---|---|---|---|---|
| Abstract | complete | 1 | 0 | 0 | 0 | 0 | 0 |
| Chapter 1 Introduction | complete | 4 | 0 | 0 | 7 | 0 | 0 |
| Chapter 2 Literature Review | complete | 4 | 0 | 0 | 10 | 0 | 0 |
| Chapter 3 Materials and Methods | complete | 20 | 18 | 2 | 20 | 0 | 0 |
| Chapter 4 Implementation and Experimental Setup | complete (with TODO) | 6 | 4 | 0 | 4 | 1 | 0 |
| Chapter 5 Results and Discussion | complete (with TODO) | 26 | 17 | 6 | 5 | 1 | 0 |
| Chapter 6 Conclusions and Future Work | complete | 4 | 0 | 0 | 0 | 0 | 0 |


**Total rendered length: 68 pages** including the references (3 pages), US Letter, 11 pt, as rendered by LibreOffice; check the page count in Word.

**Remaining TODOs and what closes them**

- Chapter 4 Implementation and Experimental Setup: add the public address or archive identifier of the repository and confirm that its visibility permits the citation
- Chapter 5 Results and Discussion: fill the TODO cells of Table 5.16 from the full texts of the four papers (AUROC and MCC on the independent set, with the training collection each paper used), and state for each whether its training collection includes sequences of the independent set
- Table 5.16 is intentionally TODO beyond the abstract-level figures: needs the full texts of AntiInflam, AIPpred, PreAIP and AIPStack (the PreAIP and AIPStack pages could not be read automatically).
- Figures 5.9b, F1 and F5 are not in the thesis (raw model keys as labels / overlapping legend): regenerate with readable labels if wanted.
- Chapters 1 and 2 are short (4 pages each) because only verified sources are used: add literature only from papers you can verify, then add them to `CANDIDATES` in `src/thesis/build_bib.py`.
- Not attempted (BLOCKERS_v2.md): C4 other protein language models, D3 transfer to AMP/ACP, AIPStack independent sets, larger-checkpoint fine-tuning.
- Word rendering was checked only through LibreOffice.

**Unverified citations** (full list with exact sentences in [CITATIONS_TO_VERIFY.md](CITATIONS_TO_VERIFY.md)): LightGBM (Ke et al. 2017), random forest (Breiman 2001), SVM (Cortes and Vapnik 1995), cosine schedule, batch normalisation and dropout have no entry; the venues of the six arXiv-cited works are unverified; the RDP58/VIP examples in Chapter 2 are second-hand; Table 5.16 uses abstract-level figures only. Eight claims from the earlier drafts were removed rather than cited.

### Three weakest points an examiner will attack

1. **"Not significant" is not "no effect".** *Attack:* the leakage-free test sets are small (214 and 751 sequences), so a real 0.01 to 0.05 MCC benefit of the contrastive term would be invisible, and the cross-validation does show +0.003 to +0.014 at lambda 2 in 5 of 6 architectures. *Honest answer:* agreed. The minimum detectable effect is about 0.14 MCC (Ind_425) and 0.08 MCC (Ind_1049); the CV gain is an order of magnitude below it, its intervals are optimistic, and nested CV gives -0.011 (95% interval -0.023 to +0.001). The thesis says "no effect larger than about 0.08 to 0.14 MCC was detectable", every Regime B survivor of correction is negative, and a larger leakage-free test set is the stated next step. It does not claim equivalence.
2. **The leakage finding: how far does it reach, and is "capacity" the explanation?** *Attack:* it is a measurement on the distributed files, the mechanism evidence (within-lineage cells show no inflation, crossed cells do) is a pattern across training sets that differ in more than lineage, nothing shows that a published result was affected, and "largest for high-capacity models" is not what the table shows. *Honest answer:* the thesis claims only the measurement (211 / 298 shared sequences, 204 / 286 with the same label; drops of 0.03 to 0.38 MCC in 48 configurations), says that published numbers were not re-examined, and states that the drop is largest for flexible non-linear models but not monotonic in capacity, without a formal test of gap differences. The user's requested wording was therefore not used (V2-D15).
3. **The representation result, the process, and what is missing.** *Attack:* a 21-feature random forest still beats the best ESM-2 model on Ind_425; fine-tuning was done once, for the 8M model only, with three seeds and validation-fold stopping; fine-tuned 8M vs frozen 650M was added after the results were seen; the explanation from dataset structure (negatives sharing 8-mers, length) is correlational; the pre-registration followed the first part of the study (H1 known), the residue-level models use a 64-d bottleneck (plan: 128), and there is no comparison with the published predictors (Table 5.16 is mostly TODO). *Honest answer:* the thesis claims "adaptation matters", not "ESM-2 beats composition" (fine-tuned 8M is -0.109 MCC against AAC + RF on Ind_425 and indistinguishable on Ind_1049); the post hoc comparison is labelled exploratory and included in the correction (126 tests); every deviation was logged before its results were seen (DECISIONS_v2.md); the missing published comparison and larger-model fine-tuning are listed as open work, not hidden.


**Inconsistencies found and fixed** (worst first): see [THESIS_CONSISTENCY_LOG.md](THESIS_CONSISTENCY_LOG.md).

## Appendix: LEAKAGE_FINDING.md (verbatim)

# LEAKAGE FINDING (Phase A)

## Headline: two internally disjoint lineages, combined across a train/test boundary

**The AIPpred and AntiInflam datasets are each internally disjoint, and the overlap appears only when data from the two lineages meet across a train/test boundary.** Each lineage's own partition is clean: AIPpred benchmark vs AIPpred independent has 0 exact overlap, and AntiInflam training vs AntiInflam validation has 0 exact overlap. Both lineages drew peptides from the same underlying source (IEDB), so a training set from one lineage and an independent set from the other share sequences: AIPpred's benchmark shares 211 sequences with AntiInflam's validation set, and AntiInflam's training set shares 298 with AIPpred's independent set. The distributed `Benchmark_Dataset.fasta` is the union of the AIPpred benchmark and part of the AntiInflam training set, so when it is paired with the two independent sets (`Ind_1049` = AIPpred's, `Ind_425` = AntiInflam's) it inherits both cross-lineage overlaps. The counts below (211 and 298) are the evidence for this mechanism; the mechanism is the finding. It is a consequence of combining two separately curated, correctly partitioned resources, not an error in either one.

**Gate result: PASSED.** The overlap reproduces exactly under independent re-computation. This document states what was measured on specific files, what was not measured, and which alternative explanations were ruled out. It makes no statement about the conduct of any author.

All numbers come from `python -m src.v2.phaseA` (outputs: `results/provenance.csv`, `results/overlap_sequences.csv`, `results/external_sources.csv`, `results/tables/T3.5_cross_benchmark_leakage.csv`, `results/tables/T3.5b_cdhit_style_clustering.csv`, `results/v2/phaseA_summary.json`). The original published dataset files were downloaded (URLs and SHA-256 in `external_sources.csv`) and compared with the local files.

## 1. The measurement

Using a new reader (not the S1 code), with whitespace/case normalisation and a check that every residue is one of the 20 standard amino acids (0 violations in all nine datasets):

| Pair (distributed local files) | Exact overlap | Same label | Opposite label | Share of the test set |
|---|---|---|---|---|
| Benchmark and Ind_425 | 211 | 204 | 7 | 49.6% |
| Benchmark and Ind_1049 | 298 | 286 | 12 | 28.4% |
| Ind_425 and Ind_1049 | 77 | 76 | 1 | 7.3% of Ind_1049 |

The numbers are identical on the raw Benchmark (3,790 rows, 3,753 unique) and on the cleaned Benchmark (3,716), because none of the 37 label-conflicted sequences is in either test set. Under a CD-HIT-style cross-set screen (our re-implementation, identity over the shorter sequence), the share of test sequences with identity >= 0.9 to some Benchmark sequence is 61.9% for Ind_425 (263 of 425) and 31.7% for Ind_1049 (333 of 1,049), measured against the cleaned Benchmark (Benchmark_clean, 3,716 sequences), which is the single reference point used for every identity figure in the thesis.

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

So the overlap is a property of pairing training data from one curation lineage with an independent set from the other: each published split is internally disjoint, but IEDB-derived sequences recur across the two lineages. Precisely: the 211 Ind_425 overlaps already exist between the *unmodified* AIPpred benchmark and the AntiInflam validation set; the 298 Ind_1049 overlaps arise because the local Benchmark also contains AntiInflam training sequences. Neither source dataset contains an error.

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

"The AIPpred and AntiInflam datasets are each internally disjoint, but they were curated separately from the same source (IEDB) and therefore share peptides across lineages. The combined training file used here is the union of the AIPpred benchmark and part of the AntiInflam training set; paired with each lineage's independent set, 211 of 425 AntiInflam-validation sequences (49.6%) and 298 of 1,049 AIPpred-independent sequences (28.4%) also occur in the training file. Removing the overlap (Regime B) is therefore required for a leakage-free estimate; its effect on performance is measured in Chapter 5."
