# HANDOFF REPORT

_Generated 2026-11-25T08:52:33 by `python -m src.report`; rebuilt after every stage._

## 1. STATUS

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

## 2. S1 VERIFICATION

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
| results/tables/ | 30 | Thesis tables as CSV + LaTeX |
| results/predictions/ | 114 | Per-sample predictions |
| results/latents/ | 26 | Latent vectors for t-SNE |
| results/models/ | 66 | Final model weights + scalers |

## 6. FIGURES

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

Files in figures/: fig5_1_roc_ind_1049_regimeA.pdf, fig5_1_roc_ind_1049_regimeA.png, fig5_1_roc_ind_1049_regimeB.pdf, fig5_1_roc_ind_1049_regimeB.png, fig5_1_roc_ind_425_regimeA.pdf, fig5_1_roc_ind_425_regimeA.png, fig5_1_roc_ind_425_regimeB.pdf, fig5_1_roc_ind_425_regimeB.png, fig5_2_pr_ind_1049_regimeB.pdf, fig5_2_pr_ind_1049_regimeB.png, fig5_2_pr_ind_425_regimeB.pdf, fig5_2_pr_ind_425_regimeB.png, fig5_3_tsne_ind_1049.pdf, fig5_3_tsne_ind_1049.png, fig5_3_tsne_ind_425.pdf, fig5_3_tsne_ind_425.png, fig5_4_lambda_sweep.pdf, fig5_4_lambda_sweep.png, fig5_5_leakage_gap.pdf, fig5_5_leakage_gap.png, fig5_6_confusion_matrices.pdf, fig5_6_confusion_matrices.png, figA_training_curves.pdf, figA_training_curves.png

## 7. BLOCKERS


Everything that failed or could not run, with diagnosis.

## T5.7 needs published numbers
_2026-11-25T08:04:09_

Table 5.7 (comparison with AIPpred, PreAIP, etc.) contains only this study's Regime A results. No verified published figures were available to the run and none were invented; copy them from the original papers into `results/tables/T5_7_comparison_published.csv`.


## 8. DECISIONS


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

1. **Decide the thesis framing before writing Chapter 5.** The data supports "leakage audit as headline, SupCon as a rigorous null/negative ablation" (playbook Risk 1). Read `INTERPRETATION.md`; if you agree, soften Chapter 1's "superior predictive stability" and the contribution wording, as the playbook suggests.
2. **Find out why AAC+RF beats every ESM-2 model.** Regime B MCC 0.425/0.374 (AAC+RF) vs 0.330/0.265 (best ESM-2). Cheap, informative checks: RF on ESM embeddings + AAC, and whether benchmark negatives are fragments of positive-source proteins. This is the examiner's likeliest first question.
3. **Fill Table 5.7** with published AIPpred/PreAIP/etc. numbers from the original papers (none were available to me and none were invented). Keep the Regime A caveat.
4. **Sanity-read the headline tables and figures** in `results/tables/` and `figures/` (all 12 figure jobs succeeded; I looked at the t-SNE and leakage-gap figures only).
5. **Optional extensions (all cheap on CPU):** extend lambda beyond 2.0 (best lambda sat on the grid edge at 8M and 150M); report the tuned-threshold results (`T5_2b`) next to the 0.5-threshold ones; consider a larger-n test by pooling Ind_425 and Ind_1049 Regime B (note the 77-sequence overlap between them).
6. **Chapters 1-2 fixes and Chapters 3-6 drafting** (playbook Prompts 12-14) were out of scope for this run and remain to do.
7. **Housekeeping.** The disk was close to full all night (free space swung from 0.1 to 8 GB); `.venv` is 1.3 GB and `embeddings/` holds the four cached checkpoints (gitignored). Kaggle was not needed: all four ESM-2 checkpoints ran on this Mac's CPU (650M took about 51 minutes), and the Kaggle CLI is logged in as the new account if you want to use it later.
