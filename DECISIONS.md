# DECISIONS

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
