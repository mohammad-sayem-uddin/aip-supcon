# HANDOFF REPORT

_Generated 2026-11-25T07:27:04 by `python -m src.report`; rebuilt after every stage._

## 1. STATUS

Wall-clock is compute time recorded by the stage runners (it excludes code-writing time).

| Stage | What | Status | Compute wall-clock | Notes |
|---|---|---|---|---|
| S1 | Data pipeline, audit, regimes A/B + hard gate | complete | 0.2s | hard gate passed; regimes A/B written |
| S2 | Sequence-identity screen, Regime C | complete | 0.3s | regime C written; identity_screen.csv |
| S3 | ESM-2 embeddings (8M, 35M, 150M, 650M) | partial | 3.7 min | esm2_t12_35M: complete; esm2_t30_150M: complete; esm2_t6_8M: complete |
| S4 | AIPNet + SupConLoss + unit tests | complete | 2.8s | AIPNet + SupConLoss + 14 passing tests |
| S5 | Training loop + trial runs (lambda=0, 0.5) | complete | 25.0s | trial: lambda=0 (MCC .2575) and lambda=0.5 (MCC .2754), seed 0 x 5 folds; sane |
| S6 | Classical + ESM-LR baselines | skipped | - | not reached |
| S7 | Lambda sweep on 8M (6 lambdas x 5 seeds x 5 folds) | skipped | - | not reached |
| S8 | Other checkpoints: lambda + temperature sweeps | skipped | - | not reached |
| S9 | Final models, all regimes, both test sets | skipped | - | not reached |
| S10 | DeLong, McNemar, bootstrap CIs | skipped | - | not reached |
| S11 | Tables and figures | skipped | - | not reached |
| S12 | Honest interpretation | skipped | - | not reached |

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
| 0.0 | 0.2575 | 0.0233 | 0.6665 | 0.0208 |
| 0.5 | 0.2754 | 0.029 | 0.6713 | 0.0142 |

_Final models / statistical tests (S9-S10) have not run yet._

## 4. LEAKAGE IMPACT

Mean over 5 seeds of each model's per-seed metrics (threshold 0.5). Gap = Regime A minus Regime B.

| model | eval_set | mcc_A | mcc_B | mcc_C | auroc_A | auroc_B | auroc_C | mcc_gap_A-B | auroc_gap_A-B |
|---|---|---|---|---|---|---|---|---|---|
| AAC_RF | ind_1049 | 0.5516 | 0.3743 | 0.3571 | 0.8568 | 0.7568 | 0.75 | 0.1773 | 0.1 |
| AAC_RF | ind_425 | 0.6745 | 0.4251 | 0.4454 | 0.9234 | 0.7853 | 0.7957 | 0.2493 | 0.1381 |
| AAC_SVM | ind_1049 | 0.4312 | 0.2469 | 0.2347 | 0.7893 | 0.6841 | 0.6823 | 0.1844 | 0.1052 |
| AAC_SVM | ind_425 | 0.5401 | 0.311 | 0.3177 | 0.8634 | 0.7382 | 0.7463 | 0.2291 | 0.1252 |

## 5. FULL RESULTS

| File | Rows | Contents |
|---|---|---|
| results/data_audit.csv | 78 | Tidy dataset audit and cross-set overlap table (Table 3.1/3.2) |
| results/s1_verification.csv | 14 | S1 hard-gate expected vs actual |
| results/identity_screen.csv | 10 | Sequences removed per identity threshold (0.8/0.9/0.95/1.0 and exact) |
| results/embedding_timings.csv | 3 | ESM-2 embedding wall-clock, device, peak memory per checkpoint |
| results/cv_results.csv | 10 | Deep model CV rows: one row per (config, seed, fold), all 8 metrics |
| results/baseline_results.csv | 110 | Baselines 1-4: CV rows and independent-set rows (Regimes A/B/C) |
| results/tables/ | 0 | Thesis tables as CSV + LaTeX |
| results/predictions/ | 12 | Per-sample predictions |
| results/models/ | 1 | Final model weights + scalers |

## 6. FIGURES

Files in figures/: none yet

## 7. BLOCKERS


Everything that failed or could not run, with diagnosis.


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

## 9. NEXT ACTIONS

_To be written at the end of the run._
