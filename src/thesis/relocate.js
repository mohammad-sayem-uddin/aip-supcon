// Tables that live in an appendix instead of in the chapter that discusses them.
//
// The thesis has to fit 22,000-23,000 words on definition (b) - body prose plus tables
// and captions - and the appendices sit outside that count. Nothing listed here is
// deleted: each table is still generated from the same results file, still carries its
// caption and source, and is still cited by number from the chapter it came from.
// The chapters keep the figures and the prose that carry the argument.
//
// Keeping a label OUT of this list keeps its table in the chapter. Two are deliberately
// kept in the body because the thesis's central finding rests on them:
//   tab:overlap  - how much of each independent set occurs in the training file
//   tab:gaps     - what removing that overlap does to every model
module.exports = {
  // Chapter 2 (Literature Review) and Chapter 4 (Results and Discussion) -> Appendix A
  A: [
    'tab:aip_predictors', // Chapter 2's evidence table of published AIP predictors
    'tab:cv',            // cross-validated performance of every configuration
    'tab:gapc',          // contrasts between the leakage gaps of model families
    'tab:checkpoints',   // best SupCon weight at the four checkpoints
    'tab:arch',          // lambda* against lambda = 0 in six architectures
    'tab:survivors',     // contrasts surviving correction
    'tab:families',      // size of each family of tests
    'tab:pool5',         // pooling variants
    'tab:fusion',        // hand-crafted features, embeddings and their fusion
    'tab:ft5',           // the fine-tuned model and its comparators
    'tab:c4',            // other protein language models
    'tab:c4_tests',      // their paired comparisons
    'tab:published',     // published figures of earlier predictors
    'tab:mde5',          // minimum detectable effect per test set and regime
  ],
  // Chapter 3 (Methodology) -> Appendix B
  B: [
    'tab:dataset_composition',
    'tab:provenance',
    'tab:conflicts',
    'tab:cleaning',
    'tab:identity',
    'tab:esm',
    'tab:pooling',
    'tab:finetune',
    'tab:training',
    'tab:mde',
    'tab:hashes',
    // tab:software and tab:devices are written directly in Appendix B, not parked by a
    // chapter. tab:hyper was a second printing of the same rows as tab:training; the
    // duplicate is gone and Appendix B B.3 now cites tab:training.
  ],
};
