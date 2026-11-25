# Table of Contents

Generated from the `H1`/`H2`/`H3` headings in `src/thesis/*.js`, in build order; page numbers are left blank for the same reason as the List of Tables/Figures (chapters are still separate `.docx` files).

ABSTRACT .......... [page]

CHAPTER 1: INTRODUCTION .......... [page]

  1.1 Background and Motivation .......... [page]

  1.2 Problem Statement .......... [page]

  1.3 Research Motivation .......... [page]

  1.4 Aim of the Research .......... [page]

  1.5 Research Objectives .......... [page]

  1.6 Scope and Contributions .......... [page]

  1.7 Organisation of the Thesis .......... [page]

  1.8 Position within the Literature .......... [page]

  1.9 Significance of the Study .......... [page]

CHAPTER 2: LITERATURE REVIEW .......... [page]

  2.1 Overview of Anti-Inflammatory Peptides (AIPs) .......... [page]

  2.2 Traditional Machine Learning Approaches for AIP Prediction .......... [page]

  2.3 Deep Learning and Protein Language Models .......... [page]

  2.4 Contrastive Learning .......... [page]

  2.5 Benchmark Datasets and Evaluation in AIP Prediction .......... [page]

  2.6 Research Gap .......... [page]

  2.7 Contribution .......... [page]

  2.8 Summary .......... [page]

CHAPTER 3: MATERIALS AND METHODS .......... [page]

  3.1 Datasets .......... [page]

  3.2 Data integrity audit .......... [page]

    3.2.1 Label conflicts within the training collection .......... [page]

    3.2.2 Overlap between training and independent sets, by direction .......... [page]

  3.3 Data cleaning protocol .......... [page]

  3.4 Evaluation regimes .......... [page]

    3.4.1 Identity screen .......... [page]

    3.4.2 Shuffled-composition null control .......... [page]

  3.5 Feature representations .......... [page]

    3.5.1 Hand-crafted descriptors .......... [page]

    3.5.2 ESM-2 embeddings and pooling variants .......... [page]

    3.5.3 Fine-tuning protocol .......... [page]

  3.6 Model architectures .......... [page]

  3.7 Loss functions .......... [page]

    3.7.1 Binary cross-entropy with a positive-class weight .......... [page]

    3.7.2 Supervised contrastive loss .......... [page]

    3.7.3 Combined objective and the roles of λ and τ .......... [page]

    3.7.4 The analytic floor of the contrastive loss .......... [page]

    3.7.5 Training protocol .......... [page]

  3.8 Evaluation metrics .......... [page]

  3.9 Statistical protocol .......... [page]

    3.9.1 The pre-registered hypothesis .......... [page]

    3.9.2 Paired tests .......... [page]

    3.9.3 Confidence intervals and effect sizes .......... [page]

    3.9.4 Multiplicity .......... [page]

    3.9.5 Power and the minimum detectable effect .......... [page]

    3.9.6 Nested cross-validation .......... [page]

CHAPTER 4: IMPLEMENTATION AND EXPERIMENTAL SETUP .......... [page]

  4.1 Hardware and Software Environment .......... [page]

  4.2 Organisation of the Experiments and Compute Time .......... [page]

  4.3 Hyperparameters and Search Ranges .......... [page]

  4.4 Training Protocol .......... [page]

  4.5 Pre-registration and Analysis Tiers .......... [page]

  4.6 Reproducibility .......... [page]

  4.7 Deviations from the Plan and Problems Encountered .......... [page]

CHAPTER 5: RESULTS AND DISCUSSION .......... [page]

  5.1 Cross-Validated Performance of All Models .......... [page]

  5.2 Performance on the Independent Sets as Distributed (Regime A) .......... [page]

  5.3 Performance after Removing the Overlap (Regimes B and C) .......... [page]

  5.4 The Impact of Overlap between Training and Test Data .......... [page]

    5.4.1 How much of each independent set is shared .......... [page]

    5.4.2 The size of the effect .......... [page]

    5.4.3 Is the inflation a function of model capacity? .......... [page]

    5.4.4 The overlap is a property of the pairing of the files .......... [page]

    5.4.5 What this does and does not show .......... [page]

  5.5 Does the Contrastive Objective Improve Prediction? .......... [page]

    5.5.1 The λ sweep .......... [page]

    5.5.2 The other checkpoints and the temperature .......... [page]

    5.5.3 The primary hypothesis (H1) .......... [page]

    5.5.4 Six architectures (H2) .......... [page]

    5.5.5 All comparisons and their correction .......... [page]

    5.5.6 Nested cross-validation and in-distribution effects .......... [page]

    5.5.7 The latent space .......... [page]

  5.6 The Representation: Pooling, Fusion and Fine-Tuning .......... [page]

    5.6.1 Pooling .......... [page]

    5.6.2 Fusion .......... [page]

    5.6.3 Fine-tuning .......... [page]

    5.6.4 Fine-tuning at 150M and 650M, and other protein language models .......... [page]

  5.7 Comparison with Published Predictors .......... [page]

  5.8 Statistical Power: What the Test Sets Could Detect .......... [page]

  5.9 Discussion .......... [page]

    5.9.1 Evaluation validity .......... [page]

    5.9.2 The contrastive objective .......... [page]

    5.9.3 Why frozen embeddings underperform composition .......... [page]

    5.9.4 The three findings together .......... [page]

  5.10 Limitations .......... [page]

CHAPTER 6: CONCLUSIONS AND FUTURE WORK .......... [page]

  6.1 Summary of Findings by Objective .......... [page]

    Objective 1: audit of the benchmark files and the effect of overlap .......... [page]

    Objective 2: a reproducible pipeline .......... [page]

    Objective 3: does the contrastive term improve prediction? .......... [page]

    Objective 4: why frozen embeddings underperform composition .......... [page]

  6.2 Contributions .......... [page]

  6.3 Limitations .......... [page]

  6.4 Future Work .......... [page]

  6.5 Concluding Remarks .......... [page]

REFERENCES .......... [page]


APPENDICES (if any) .......... [page]
