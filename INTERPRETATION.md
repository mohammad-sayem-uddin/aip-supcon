# Honest interpretation of the results (S12)

All numbers below are copied from `results/*.csv` and `results/tables/`. "Headline model" = the model chosen by the pre-specified protocol (lambda* by 5-fold CV, then tau* by CV at lambda*), compared with the identical network at lambda = 0.

## 1. Does SupCon (lambda > 0) beat BCE alone (lambda = 0)?

**No. On the leakage-free test sets the difference is not statistically significant at the 8M checkpoint, and it is significantly negative at larger checkpoints.**

8M headline (lambda = 2, tau = 0.1) minus lambda = 0, Regime B, seed-ensemble predictions, 95% paired stratified bootstrap CIs:

| Test set | n | MCC diff | AUROC diff | DeLong p | McNemar p |
|---|---|---|---|---|---|
| Ind_425 | 214 | -0.0168 [-0.0869, +0.0557] | +0.0036 [-0.0222, +0.0288] | 0.7732 | 0.4545 |
| Ind_1049 | 751 | -0.0035 [-0.0484, +0.0455] | +0.0018 [-0.0118, +0.0158] | 0.8017 | 0.9020 |

Neither difference is statistically significant. The 5-fold CV agrees: 8M CV MCC is 0.2687 at lambda = 0 and 0.2746 at lambda = 2 (tau 0.07), a gain of 0.0059 against a per-run standard deviation of about 0.023; at the CV-selected tau = 0.1 it is 0.2780 (+0.0093). That is well inside run-to-run noise. The confidence intervals are wide enough that effects of up to roughly +-0.05 MCC on Ind_1049 and +-0.08 on Ind_425 cannot be excluded, so the correct statement is "no evidence of an improvement", not "proof of no effect".

## 2. Is the effect consistent across checkpoints, seeds, test sets and regimes?

It is not, and the inconsistency is itself the finding.

- **Checkpoints (Regime B, DeLong p on AUROC).** 8M: n.s. on both sets. 35M (lambda 0.5): n.s. on both (MCC diff +0.0552 on Ind_425 and -0.0037 on Ind_1049). 150M (lambda 2): AUROC significantly *lower* on both sets (-0.0276, p = 0.0272; -0.0234, p = 0.0011). 650M (lambda 1, tau 0.05): n.s. on Ind_425 (p = 0.5714) and significantly lower on Ind_1049 (AUROC -0.0231, p = 0.0004). Of the 8 Regime-B DeLong tests for the headline models, 3 reach p < 0.05 and all 3 are negative; none is positive. McNemar is non-significant in all 24 headline comparisons across regimes A, B and C.
- **Regimes.** The only significant *positive* effects appear under Regime A (as published, leaky): 8M AUROC +0.0260 (p = 0.0013) on Ind_425 and +0.0167 (p = 0.0018) on Ind_1049, and 35M +0.0122 (p = 0.0206) on Ind_425. They disappear under Regime B (p = 0.77 and 0.80 at 8M) and Regime C. A contrastive term that helps only when near-duplicates of the test sequences are in the training set is consistent with better memorisation rather than better generalisation (this is a hypothesis; the experiments do not isolate it).
- **Seeds.** For the 8M headline model the per-seed Regime-B MCC difference ranges from -0.057 to +0.066 on Ind_1049 and is positive in all 5 seeds on Ind_425 (mean +0.054) while the ensemble difference is -0.017 and the mean per-seed AUROC difference on Ind_425 is 0.0000. A fixed-threshold MCC at 0.5 is therefore sensitive to calibration shifts that the contrastive term induces, not to ranking quality. Seed variability (SD about 0.04-0.05 MCC) exceeds every effect.
- **Multiplicity.** About 24 tests per regime family were run without correction. After a Bonferroni factor of 8 (per regime) the surviving Regime-B results are the two *negative* ones (150M and 650M on Ind_1049).
- **Latent geometry.** The t-SNE panels show heavily overlapping classes in all three views. On Ind_1049 silhouette is 0.007 (raw), 0.009 (lambda = 0) and 0.008 (lambda = 2); Davies-Bouldin is 18.54, 9.35 and 8.27 (raw/encoder dimensions differ, so raw-vs-encoder is not like for like; the lambda = 0 vs lambda = 2 comparison is). SupCon lowers Davies-Bouldin by about 12% but leaves silhouette unchanged, and the classes remain essentially unseparated.
- **Exploration.** Two-view feature-space augmentation (dropout views, with and without input noise), 12 configurations at 8M, left CV MCC between 0.271 and 0.278 for every lambda, including the lambda = 0 two-view baseline (0.274). It did not rescue the effect.

## 3. How much of the Regime A performance is leakage?

Mean over 5 seeds, MCC (AUROC in brackets), Regime A -> Regime B:

| Model | Ind_425 | Ind_1049 |
|---|---|---|
| AAC + RF | 0.674 -> 0.425 (0.923 -> 0.785), gap 0.249 (0.138) | 0.552 -> 0.374 (0.857 -> 0.757), gap 0.177 (0.100) |
| AAC + SVM | 0.540 -> 0.311, gap 0.229 | 0.431 -> 0.247, gap 0.184 |
| AAC+DPC+CTD + LightGBM | 0.355 -> 0.319, gap 0.037 | 0.369 -> 0.306, gap 0.063 |
| ESM-2 8M + MLP (lambda 0) | 0.484 -> 0.247, gap 0.237 | 0.386 -> 0.236, gap 0.150 |
| ESM-2 8M + SupCon (2, 0.1) | 0.554 -> 0.301, gap 0.253 | 0.403 -> 0.227, gap 0.176 |
| ESM-2 650M + MLP (lambda 0) | 0.516 -> 0.330, gap 0.187 | 0.401 -> 0.265, gap 0.136 |

The leakage inflation of 0.18-0.25 MCC for the simple composition classifiers is larger than almost any difference between published AIP predictors, which supports the data-integrity contribution. The 8M SupCon model loses more than its lambda = 0 twin (gap 0.253 vs 0.237 and 0.176 vs 0.150). Regime C (< 90% identity) is almost identical to Regime B, so removing near-duplicates beyond exact matches changed results little.

## 4. Strongest defensible claim (abstract sentence)

"When 'independent' test sequences that also occur in the training data are removed (49.6% of Ind_425 and 28.4% of Ind_1049), MCC of simple composition-based classifiers falls by 0.18-0.25, and under this leakage-free evaluation adding a supervised contrastive objective to a classifier head on frozen ESM-2 embeddings gave no statistically significant improvement at the 8M scale and a significant AUROC reduction at the 150M and 650M scales."

## 5. The three weakest points an examiner will attack

1. **The frozen ESM-2 pipeline is beaten by a 21-feature Random Forest.** Regime-B MCC: AAC+RF 0.425 (Ind_425) and 0.374 (Ind_1049), versus 0.330 and 0.265 for the best ESM-2 model (650M, lambda = 0); 5-fold CV AUROC is 0.773 for AAC+RF and 0.666 for the 8M MLP. *Honest response:* this is a measured result. It means the contrastive question is being asked of a representation that is weaker than composition for this benchmark. A plausible but untested explanation is that negatives are composition-distinct fragments of parent proteins; the leakage section of the playbook flags the same concern. Report it as a limitation, and do not claim ESM-2 superiority in Chapter 1.
2. **Statistical power and selection.** Ind_425 Regime B has only 214 sequences, so MCC CIs are about +-0.07-0.09 wide on differences; lambda and tau were chosen on CV (lambda = 2 sits on the edge of the grid) and seed-ensemble tests ignore training variance. *Honest response:* state the result as "no detectable effect larger than the CI half-width", show the per-seed table (T5.6b), and note that selection on CV never touched the test sets.
3. **Claims in Chapter 1 and the novelty framing.** "Superior predictive stability" is not supported (the CV std at lambda 2 is 0.0235 vs 0.0229 at lambda 0), and the CPU-efficiency framing is only partly what was run (the 650M embeddings took about 51 minutes on CPU, and the sweep ran on CPU). *Honest response:* soften the contribution wording as the playbook recommends and promote the leakage audit to the headline contribution.

Also note: Table 5.7 (comparison with published predictors) could not be filled, because no verified published numbers were available (see BLOCKERS.md).
