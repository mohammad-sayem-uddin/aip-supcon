# PREREGISTRATION (v2 extension)

Written 2026-11-25, **before** any Phase B, C, D or F computation of the v2 extension. The commit that contains this file is recorded in `PREREG_COMMIT.txt`; the thesis should cite that commit hash and its GitHub timestamp.

## 0. A disclosure that limits what this document can claim

The primary hypothesis below was already tested in the v1 run (stages S7-S10), and its outcome was known when this file was written: it was **not supported**. This document therefore cannot claim that the 8M test was pre-registered blind. What it does is (a) fix the hypothesis, the decision rule and the family of comparisons in writing, with the v1 outcome stated openly, so that nothing in v2 can be promoted to a headline after the fact; and (b) pre-specify the v2 analysis so that the new architecture comparisons are not subject to forking paths. The v1 result is not re-run and not altered.

## 1. Primary hypothesis (H1)

**H1: At the ESM-2 8M checkpoint, a classifier trained with BCE + lambda * SupCon (lambda > 0) has higher Matthews correlation coefficient than the identical classifier trained with BCE alone (lambda = 0), on the leakage-free (Regime B) versions of both Ind_425 and Ind_1049.**

**The single test that settles it.** For each test set, the paired difference in MCC (seed-ensemble predictions, threshold 0.5, model at the CV-selected lambda* minus model at lambda = 0) with a 95% paired stratified bootstrap confidence interval (2,000 resamples). H1 is supported if and only if the lower bound of that interval is above 0 on **both** Ind_425 and Ind_1049 (an intersection-union rule, so no multiplicity correction is needed for H1 at a 5% level). The DeLong test on the AUROC difference is reported alongside but is not the decision rule.

**v1 outcome (already known, stated here for transparency).** Headline model 8M, lambda = 2, tau = 0.1: MCC difference -0.0168 (95% CI -0.0869 to +0.0557) on Ind_425 and -0.0035 (-0.0484 to +0.0455) on Ind_1049. **H1 is not supported.** This stays the primary result whatever v2 finds.

## 2. Secondary hypotheses (confirmatory in form, explicitly secondary)

**H2 (architecture robustness).** The H1 contrast, repeated for each Phase B architecture B2-B6 on residue-level 8M embeddings (Regime B, both test sets: 10 comparisons). Decision rule per comparison: supported only if the BH-adjusted DeLong p-value is below 0.05 **and** the MCC-difference CI lower bound is above 0 on that test set. The statement "the contrastive objective helps in some architecture" requires at least one comparison to meet that rule.

## 3. Everything else is exploratory

All of the following are labelled **exploratory** in every table (column `analysis_tier`): Regimes A and C results; every checkpoint other than 8M; the pooling ablation (C1); feature fusion (C2); fine-tuning (C3); other protein language models (C4); external and cross-dataset benchmarks (D); related-task transfer (D3); all of Phase F. Exploratory results can generate hypotheses for the discussion; they cannot support a claim in the abstract.

## 4. Fixed protocol (no forking paths)

- **Folds and seeds.** `make_folds` from `src/train.py`, seeds 0-4, 5 folds, for every model. A model not on these folds is not tabled.
- **Lambda grid.** {0, 0.1, 0.25, 0.5, 1.0, 2.0}. It is not extended. lambda* per architecture is the lambda > 0 with the highest mean 5-fold CV MCC (25 runs); ties go to the smaller lambda.
- **Temperature.** Fixed at 0.07 for all Phase B architectures (the v1 temperature sweep is not repeated).
- **Final models.** Trained on the cleaned Benchmark with a stratified 10% hold-out for early stopping (patience 20, max 200 epochs), 5 seeds, predictions averaged over seeds for paired tests; evaluated under Regimes A, B and C. Regime B is the regime for claims; Regime A is for comparability only.
- **No test-set tuning**, including which test set to feature: both are always reported.
- **Multiplicity.** Benjamini-Hochberg at q = 0.05. Raw and adjusted p-values are reported side by side, within the families (H2; all lambda-contrast tests; representation comparisons) and globally across every secondary and exploratory p-value in the thesis.
- **Effect sizes.** Every p-value is accompanied by an effect estimate with a 95% CI, and the minimum detectable effect (80% power, alpha 0.05, derived from the paired bootstrap standard error) is reported for every test set. "Not significant" is worded as "no effect larger than X was detectable at this n".
- **Nested CV** (outer 5 x inner 3) for the headline 8M comparison only.
- **Published numbers.** Never invented. An empty cell reads "not reported".
- **Excluded by design.** No object-detection or image models (YOLO, Faster R-CNN, etc.), no ImageNet-pretrained encoders on sequence data.

## 5. What would change my reading

If H1 had been supported, or any H2 comparison meets its rule after BH correction, I will report it with the effect size and the minimum detectable effect, and say that H1 itself remains unsupported. If no comparison meets the rule, the thesis claim is: "no evidence that the contrastive objective improves leakage-free MCC, and effects smaller than the reported detectable effect cannot be excluded".
