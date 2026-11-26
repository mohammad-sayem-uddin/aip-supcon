// Appendices. Tables moved out of the body chapters to keep the thesis inside its
// word budget; every one of them is cited from the chapter it came from.
const fs = require('fs');
const { chapter, ROOT } = require('./lib.js');
const J = JSON.parse(fs.readFileSync(`${ROOT}/results/thesis/ch5_data.json`, 'utf8'));
const T = J.T;
const C = JSON.parse(fs.readFileSync(`${ROOT}/results/v2/chapter3_data.json`, 'utf8'));
const CT = C.T;

// ---------------------------------------------------------------- Appendix A
const A = chapter(7, 'APPENDIX A', 'APPENDIX A thesis.docx', { numberAs: 'A' });
{
  const { add, H1, table, caption, afterTable } = A;
  const P = (s) => A.P(s);
  const shade = (k) => ({ shadeRows: T[k + '_shade'] || T.cv_shade, size: 17 });
  add(H1('APPENDIX A: DETAILED RESULTS'));
  add(P(`This appendix holds the per-model result tables that Chapter 4 cites but does not print in full. The chapter reports the aggregated comparisons and the figures that carry the argument; the tables below give every configuration, so that any number quoted in the chapter can be checked. All of them are generated from the same results files as the chapter (results/thesis/ch5_data.json).`));

  add(caption('tab:ind425', 'Performance on Ind_425 (425 sequences in Regime A, 214 in Regime B, 162 in Regime C), mean over the five final models of each configuration. Shaded rows are the composition-based references. Cited in Section 4.2.'));
  add(table(T.ind_ind_425, [3600, 960, 960, 960, 960, 960, 960], shade('ind_ind_425')), afterTable());

  add(caption('tab:ind1049', 'Performance on Ind_1049 (1,049 sequences in Regime A, 751 in Regime B, 716 in Regime C), mean over the five final models of each configuration. Shaded rows are the composition-based references. Cited in Section 4.2.'));
  add(table(T.ind_ind_1049, [3600, 960, 960, 960, 960, 960, 960], shade('ind_ind_1049')), afterTable());

  add(caption('tab:tau', 'Temperature sweep at the selected λ of each checkpoint (cross-validated, mean ± standard deviation over 25 runs). Cited in Section 4.5.2.'));
  add(table(T.tau, [2400, 1000, 1000, 2480, 2480], { size: 17 }), afterTable());

  add(caption('tab:reptests', 'Paired comparisons of the representation study (exploratory). ΔMCC is for the first model minus the second; the p-values are DeLong p-values for the AUROC difference, raw and Benjamini-Hochberg adjusted within the exploratory family. Cited in Section 4.6.'));
  add(table(T.rep_tests.map((r) => [r[0].replace(/lambda=0/g, 'λ = 0').replace(/esm650 /g, '650M ').replace(/esm8 /g, '8M ').replace(/\(rf\)/g, '(random forest)').replace(/\(mlp\)/g, '(MLP)'), r[1] === 'ind_425' ? 'Ind_425' : 'Ind_1049', r[2], r[3], r[4], r[5]]),
    [3300, 900, 2300, 900, 900, 1060], { size: 15 }), afterTable());
}

// ---------------------------------------------------------------- Appendix B
const B = chapter(8, 'APPENDIX B', 'APPENDIX B thesis.docx', { numberAs: 'B' });
{
  const { add, H1, table, caption, afterTable } = B;
  const P = (s) => B.P(s);
  add(H1('APPENDIX B: MODEL AND IMPLEMENTATION DETAIL'));
  add(P(`This appendix holds the layer-by-layer definitions of the six architectures and two implementation records that Chapter 3 cites. They are reproducibility detail: the chapter describes each architecture in words and states what distinguishes it, and the tables below fix the exact layers, shapes and parameter counts needed to rebuild it.`));

  for (const key of ['B1_mlp', 'B2_cnn', 'B3_bilstm', 'B4_cnn_bilstm', 'B5_transformer', 'B6_attnpool']) {
    const short = key.split('_')[0];
    add(caption(`tab:layers_${short.toLowerCase()}`, `Layers of model ${short}. Dropout and normalisation as described in Section 3.6. Source: results/v2/architecture_layers.csv.`));
    add(table(CT.layers[key], [2200, 5900, 1260], { right: [2], boldLast: true, size: 17 }), afterTable());
  }

  add(caption('tab:stages', 'Compute time recorded for each stage of the experiments (results/.stages and results/v2/kaggle_runtimes.csv). Times are the wall-clock time that the stage runner recorded for its last execution; a stage that was resumed or re-run shows that execution only, and the time spent writing code is not included. Cited in Section 3.11.'));
  add(table(STAGES(), [1100, 5700, 2560]), afterTable());

}

// the stage table is assembled from the same fields Chapter 3 used
function STAGES() {
  const F = J.F, st = F.stages;
  const mins = (s) => `${(s / 60).toFixed(1)} min`;
  const secs = (s) => (s < 1 ? '< 1 s' : s >= 120 ? mins(s) : `${s.toFixed(0)} s`);
  const s3 = ['S3_esm2_t6_8M', 'S3_esm2_t12_35M', 'S3_esm2_t30_150M'].reduce((a, k) => a + st[k].secs, 0);
  return [['Stage', 'Content', 'Recorded compute time'],
    ['S1, S2', 'data pipeline, audit, regimes A and B, identity screen (Regime C)', secs(st.S1.secs + st.S2.secs)],
    ['S3', 'embeddings of the 8M, 35M and 150M checkpoints (CPU); the 650M extraction time was not reliably measurable (Section 3.5.2)', secs(s3)],
    ['S4, S5', 'model and loss with unit tests; trial runs', secs(st.S4.secs + st.S5.secs)],
    ['S6', 'classical and embedding-based baselines (5 seeds × 5 folds, final models, all regimes)', secs(st.S6.secs)],
    ['S7', 'λ sweep at 8M (6 values × 5 seeds × 5 folds)', secs(st.S7.secs)],
    ['S8', 'λ and τ sweeps at the four checkpoints', secs(st.S8.secs)],
    ['S9, S10', 'final models and statistical tests (first part of the study)', secs(st.S9.secs + st.S10.secs)],
    ['Phase A', 'provenance and overlap audit', secs(st.A.secs)],
    ['Phase B', `six architectures: CV and final models; the Kaggle GPU kernel took ${secs(F.kaggle['aip-phase-b-gpu'])} for B2 and B5 (its B6 duplicate was ignored in favour of the local run); the local slices were not timed`, secs(st.B_final.secs) + ' (final models, local)'],
    ['C1, C2', 'pooling variants and fusion (local CPU)', secs(st.C1_pooling.secs + st.C1_attention.secs + st.C2_fusion.secs)],
    ['C3', 'fine-tuning and frozen control: Kaggle GPU kernel', secs(F.kaggle['aip-c3-finetune-gpu'])],
    ['Phase D', 'cross-benchmark generalisation (7 models × 3 training sets × 5 seeds)', secs(st.D_cross.secs)],
    ['Phase E', `nested cross-validation; corrected statistics (${F.n_tests} comparisons)`, `${secs(st.E5_nested.secs)}; ${secs(st.E_stats.secs)}`]];
}

Promise.all([A.build(), B.build()]).then(() => console.log('appendices built'));

module.exports = { A, B };
