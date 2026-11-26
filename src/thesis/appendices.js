// Appendices. Tables moved out of the body chapters to keep the thesis inside its
// word budget; every one of them is cited from the chapter it came from.
const fs = require('fs');
const { chapter, ROOT } = require('./lib.js');
const J = JSON.parse(fs.readFileSync(`${ROOT}/results/thesis/ch5_data.json`, 'utf8'));
const T = J.T;
const C = JSON.parse(fs.readFileSync(`${ROOT}/results/v2/chapter3_data.json`, 'utf8'));
const CT = C.T;


// tables parked by the chapters (see relocate.js): rendered here, in the order their
// chapter emitted them, each keeping its own caption and source line
function relocatedInto(app, api) {
  const { add, table, caption, afterTable } = api;
  let n = 0;
  for (const ch of [1, 2, 3, 4, 5]) {
    const f = `${ROOT}/results/thesis/relocated_ch${ch}.json`;
    if (!fs.existsSync(f)) continue;
    for (const r of JSON.parse(fs.readFileSync(f, 'utf8'))) {
      if (r.appendix !== app) continue;
      add(caption(r.label, r.text));
      add(table(r.rows, r.widths, r.opts), afterTable());
      n += 1;
    }
  }
  return n;
}

// ---------------------------------------------------------------- Appendix A
const A = chapter(7, 'APPENDIX A', 'APPENDIX A thesis.docx', { numberAs: 'A', isAppendix: true });
{
  const { add, H1, table, caption, afterTable } = A;
  const P = (s) => A.P(s);
  const shade = (k) => ({ shadeRows: T[k + '_shade'] || T.cv_shade, size: 17 });
  add(H1('APPENDIX A: DETAILED RESULTS'));
  add(P(`This appendix holds the per-model result tables that Chapter 4 cites but does not print in full. The chapter reports the aggregated comparisons and the figures that carry the argument; the tables below give every configuration, so that any number quoted in the chapter can be checked. All of them are generated from the same results files as the chapter (results/thesis/ch5_data.json).`));

  console.log('  Appendix A takes', relocatedInto('A', A), 'relocated tables');
  add(caption('tab:ind425', 'Performance on Ind_425 (425 sequences in Regime A, 214 in Regime B, 162 in Regime C), mean over the five final models of each configuration. Shaded rows are the composition-based references. Cited in Section 4.2.'));
  add(table(T.ind_ind_425, [3600, 960, 960, 960, 960, 960, 960], shade('ind_ind_425')), afterTable());

  add(caption('tab:ind1049', 'Performance on Ind_1049 (1,049 sequences in Regime A, 751 in Regime B, 716 in Regime C), mean over the five final models of each configuration. Shaded rows are the composition-based references. Cited in Section 4.2.'));
  add(table(T.ind_ind_1049, [3600, 960, 960, 960, 960, 960, 960], shade('ind_ind_1049')), afterTable());

  add(caption('tab:tau', 'Temperature sweep at the selected λ of each checkpoint (cross-validated, mean ± standard deviation over 25 runs). Cited in Section 4.5.2.'));
  add(table(T.tau, [2400, 1000, 1000, 2480, 2480], { size: 17 }), afterTable());

  add(caption('tab:reptests', 'Paired comparisons of the representation study (exploratory). ΔMCC is for the first model minus the second; the p-values are DeLong p-values for the AUROC difference, raw and Benjamini-Hochberg adjusted within the exploratory family. Cited in Section 4.6.'));
  add(table(T.rep_tests.map((r) => [r[0].replace(/lambda=0/g, 'λ = 0').replace(/esm650 /g, '650M ').replace(/esm8 /g, '8M ').replace(/\(rf\)/g, '(random forest)').replace(/\(mlp\)/g, '(MLP)'), r[1] === 'ind_425' ? 'Ind_425' : 'Ind_1049', r[2], r[3], r[4], r[5]]),
    [3300, 900, 2300, 900, 900, 1060], { size: 15 }), afterTable());

  // The provenance of the published figures and the observations drawn from them.
  // Section 4.7 states the one like-for-like comparison and cites this section for the rest.
  const ref = (l) => A.ref(l);
  const f = (x, d = 3) => Number(x).toFixed(d);
  const AF = J.F;
  const I = (k, s, r, m = 'mcc') => f(AF.ind[k][s][r][m]);
  const RF = 'AAC_RF';
  const csvRow = (l) => { const o = []; let cur = '', q = false; for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { o.push(cur); cur = ''; } else cur += ch; } o.push(cur); return o; };
  const PUBCSV = fs.readFileSync(`${ROOT}/results/tables/T5_7_published_reported.csv`, 'utf8').trim().split('\n');
  const PH = csvRow(PUBCSV[0]);
  const PR = PUBCSV.slice(1).map((l) => Object.fromEntries(csvRow(l).map((v, k) => [PH[k], v])));
  const pv = (pred, ev, fld = 'AUC') => Number(PR.find((r) => r.predictor === pred && r.evaluation.includes(ev))[fld]);

  add(A.H2('A.1 Provenance of the published figures, and what they show'));
  add(P(`Each published value in Table ${ref('tab:published')} was read from a table of the open-access full text of the cited paper, named in the table's last column; AIPStack's figures come from its text, and AIEpred's are the values the iAIPs authors report for it, because the AIEpred paper is not open access. One predictor can differ between sources: AIPpred's independent-set AUC is 0.814 in its own paper and 0.813 in the PreAIP paper. Values marked n/a are not publicly available rather than merely unchecked: IF-AIP and AIEpred are both closed access, and retrying them through full-text, PDF-link and extraction tools returned only IF-AIP's relative improvements, while AIPStack's sensitivity and specificity exist only inside a figure image.`));
  add(P(`Three observations follow, each limited to what the table shows. First, the published predictors on the AIPpred independent set report AUCs and MCCs of the same order as AAC + RF in this thesis under Regime A, and higher than it under Regime B. Second, and this is the only like-for-like comparison available, AIPFusion-Net reports an MCC of ${f(pv('AIPFusion-Net (Wang et al., 2026)', 'Ind-1049', 'MCC'))} on Ind-1049 and ${f(pv('AIPFusion-Net (Wang et al., 2026)', 'Ind-426', 'MCC'))} on Ind-426, on data files that are byte-identical to the ones audited here (Section 3.2.2); against that, AAC + RF reaches ${I(RF, 'ind_1049', 'A')} and ${I(RF, 'ind_425', 'A')} in Regime A but only ${I(RF, 'ind_1049', 'B')} and ${I(RF, 'ind_425', 'B')} once the overlap is removed. Third, AIPStack was evaluated on an independent set built by its authors that is not available here, so its figures are listed but not compared. None of this shows that one model is better than another: the training collections and protocols differ, the Regime A scores of this thesis depend on the overlap (Section 4.4), and the published figures were not recomputed. A fair comparison would retrain each published method on Benchmark_clean and score it in Regime B, which was not done here.`));
}

// ---------------------------------------------------------------- Appendix B
const B = chapter(8, 'APPENDIX B', 'APPENDIX B thesis.docx', { numberAs: 'B', isAppendix: true });
{
  const { add, H1, H2, table, caption, afterTable } = B;
  const P = (s) => B.P(s);
  const ref = (l) => B.ref(l);
  const cit = (...k) => B.cit(...k);
  const n = B.n;
  const F = C.F;
  const A2 = J.F, env = A2.env, req = A2.requirements, st = A2.stages;
  const gib = (Number(env['local memory (bytes)']) / 2 ** 30).toFixed(0);
  const mins = (x) => `${(x / 60).toFixed(1)} min`;
  const secs = (x) => (x < 1 ? '< 1 s' : x >= 120 ? mins(x) : `${x.toFixed(0)} s`);
  add(H1('APPENDIX B: MODEL AND IMPLEMENTATION DETAIL'));
  add(P(`This appendix holds the implementation record of the study and the tables of detail that Chapter 3 cites: the hardware and software the experiments ran on, the compute time each stage took, the layer-by-layer definitions of the six architectures, and the parameter settings. It is reproducibility detail - the chapter describes each choice and states what it does; the material here fixes the exact values needed to rebuild the work.`));

add(H2('B.1 Hardware and software environment'));
add(P(`Most of the work was carried out on a single laptop-class machine with an ${env['local machine']} processor with ${env['local logical cores']} cores and ${gib} GiB of memory, running ${env['local OS'].replace('macOS-', 'macOS ').split('-')[0]}, with Python ${A2.python}. Two experiments, the training of the convolutional and Transformer architectures and the fine-tuning of the language model, were run on graphics processors provided by the Kaggle platform: a kernel with two ${env['Kaggle GPU model']} GPUs, Python ${env['Kaggle kernel python and torch'].split(' ')[0]} and PyTorch ${env['Kaggle kernel python and torch'].split(' ')[1]}, without internet access, so that the code, the cached embeddings and the 8M model weights were supplied as a private dataset. The main software packages and their versions are listed in Table ${ref('tab:software')}; the full list of pinned versions is in the file requirements.txt of the project.`));
const sw = [['Package', 'Version', 'Use'],
  ['PyTorch', req.torch, `neural network training ${cit('paszke2019')}`], ['Transformers (Hugging Face)', req.transformers, 'loading and running ESM-2'],
  ['scikit-learn', req['scikit-learn'], `classical models, folds, metrics ${cit('pedregosa2012')}`], ['LightGBM', req.lightgbm, `gradient-boosted trees ${cit('ke2017')}`],
  ['NumPy / pandas / SciPy', `${req.numpy} / ${req.pandas} / ${req.scipy}`, 'numerical work and statistics'], ['Biopython', req.biopython, `pairwise alignment for the identity screen ${cit('cock2009')}`],
  ['RapidFuzz', req.RapidFuzz, 'longest-common-subsequence prefilter'], ['Matplotlib / seaborn', `${req.matplotlib} / ${req.seaborn}`, 'figures']];
add(caption('tab:software', 'Main software packages and versions on the local machine (from requirements.txt). The Kaggle kernels used their pre-installed PyTorch and scikit-learn.'));
add(table(sw, [2400, 2000, 4960]), afterTable());
add(P(`The ESM-2 checkpoints were obtained through the Transformers library ${cit('wolf2020')} from the model hub; each checkpoint was deleted from the local cache after its embeddings had been extracted, because the machine had little free disk space. The experiments were scheduled around the memory limit of the machine: the extraction of the largest checkpoint and the training of the models were not run concurrently after an early attempt showed that the combination exhausted the memory and slowed both.`));


add(H2('B.2 Organisation of the experiments and compute time'));
add(P(`The experiments were organised as a sequence of stages, each writing its results to files on disk and recording a marker, so that an interrupted run could resume without repeating completed work. The first part of the study (stages S1 to S12) covered the data pipeline, the embeddings of the four checkpoints, the baselines, the sweeps of λ and τ, the final models, the statistics, and the tables and figures. The second part added the audit of provenance and overlap (Phase A), the pre-registration, the residue-level embeddings, the six architectures (Phase B), the pooling, fusion and fine-tuning studies (Phase C), the cross-benchmark analysis (Phase D), the corrected statistics, the nested cross-validation (Phase E) and the analysis of the data and of the errors (Phase F). The compute time recorded for each stage is given in Table ${ref('tab:stages')} of Appendix B.`));
add(P(`The cost of training a single model depends strongly on the architecture and on the device. On the central processor, a five-fold cross-validation run of the bidirectional LSTM (B3) took on average ${A2.b_seconds.B3_bilstm.toFixed(0)} seconds and one of the hybrid convolutional and recurrent network (B4) ${A2.b_seconds.B4_cnn_bilstm.toFixed(0)} seconds, whereas on the graphics processor a run of the convolutional network (B2) took ${A2.b_seconds.B2_cnn.toFixed(0)} seconds and one of the Transformer (B5) ${A2.b_seconds.B5_transformer.toFixed(0)} seconds. A fine-tuning run of the 8M language model took on average ${A2.ft_seconds.finetune.toFixed(0)} seconds on the graphics processor, and a run of the frozen-backbone control ${A2.ft_seconds.frozen.toFixed(0)} seconds. Table ${ref('tab:devices')} records on which device each architecture was trained; the λ = 0 model and every λ value of one architecture were always trained on the same type of device.`));
const dev = [['Experiment', 'Device']];
const nm = { B1_mlp: 'B1 MLP (first part of the study)', B2_cnn: 'B2 CNN', B3_bilstm: 'B3 BiLSTM', B4_cnn_bilstm: 'B4 CNN-BiLSTM', B5_transformer: 'B5 Transformer', B6_attnpool: 'B6 attention pooling', C3_finetune: 'C3 fine-tuning and frozen control' };
for (const [k, v] of Object.entries(A2.device_map)) dev.push([nm[k] || k, v.replace(' (Kaggle duplicate ignored)', '')]);
add(caption('tab:devices', 'Device on which each architecture and the fine-tuning experiment were trained (results/v2/device_map.json).'));
add(table(dev, [3300, 6060]), afterTable());


add(H2('B.3 Hyperparameters and search ranges'));
add(P(`The hyperparameters of the neural models were fixed in advance and shared by every configuration (Table ${ref('tab:training')}); only λ and τ were searched, over the grids pre-specified in Section 3.7.3. Within a checkpoint or architecture, λ* was the value of λ > 0 with the highest mean cross-validated MCC over the 25 runs, with ties going to the smaller value, and τ* was then chosen from the temperature grid at λ*, as the value with the highest mean cross-validated MCC. For the architecture comparison τ was fixed at ${F.par['Phase B residue-level models|temperature']}. No hyperparameter of any model was chosen on an independent test set. The selected values are reported with the results in Chapter 4: λ* = ${A2.selected_v2.B2_cnn.lambda_star} for B2 and λ* = ${A2.selected_v2.B3_bilstm.lambda_star} for B3, B4, B5 and B6, and, in the multilayer perceptron at the four checkpoints, λ* = ${A2.selected_v1['esm2_t6_8M_lam2_tau0.1'].lambda} (8M, τ* = ${A2.selected_v1['esm2_t6_8M_lam2_tau0.1'].tau}), ${A2.selected_v1['esm2_t12_35M_lam0.5_tau0.07'].lambda} (35M), ${A2.selected_v1['esm2_t30_150M_lam2_tau0.07'].lambda} (150M) and ${A2.selected_v1['esm2_t33_650M_lam1_tau0.05'].lambda} (650M, τ* = ${A2.selected_v1['esm2_t33_650M_lam1_tau0.05'].tau}).`));
add(P(`The classical baselines were tuned inside the training fold. The support vector machine used a grid over C (${F.par['baselines|SVM grid C'].replace(/[\[\]]/g, '')}) and the kernel width (${F.par['baselines|SVM grid gamma'].replace(/[\[\]]/g, '')}) with three-fold cross-validated AUROC; the random forest used ${F.par['baselines|RandomForest n_estimators']} trees; LightGBM stopped early on an inner 10% hold-out of the training fold; and the logistic regression chose its regularisation strength by inner cross-validation. The residue-level models used a ${F.par['Phase B residue-level models|per-residue adapter width']}-dimensional per-residue adapter, a hidden size of 64 per direction in the recurrent layers, and gradient clipping at a maximum norm of ${F.par['Phase B residue-level models|clip']}.`));



add(H2('B.5 Reproducibility'));
add(P(`Excluding the special tokens and the padding is a point at which implementations commonly err, so the extraction code asserts, with an absolute tolerance of 1e-4, that a sequence yields the same vector whether it is embedded alone or in a padded batch. Each of the ${n(F.n_unique_embedded)} unique sequences across the three datasets was embedded once and the vectors were cached, so that every model reads identical features. For the sequence models of Section 3.6 the same checkpoints were used to cache the residue-level vectors themselves (${n(F.residue_vectors)} residue vectors in total), together with the <i>cls</i> vector. The 8M cache was stored in single precision and the 650M cache in half precision; mean pooling of the cached residue vectors was compared with the pooled embedding computed directly for every one of the ${n(F.n_unique_embedded)} sequences (results/v2/half_precision_check.csv): the largest absolute difference was ${F.half.esm2_t33_650M.max_abs.toExponential(1)} for the half-precision 650M cache (${F.half.esm2_t33_650M.rel.toExponential(1)} of the largest embedding value) and ${F.half.esm2_t6_8M.max_abs.toExponential(1)} for the single-precision 8M cache.`));
add(P(`Every stage reads and writes files at fixed locations, every random seed is set explicitly, and the software versions are pinned. The cleaned training collection and the three evaluation regimes are stored as files; the embeddings of every checkpoint are cached, computed once from the unique sequences of the three datasets; and the cross-validation folds come from a deterministic function of the seed. All results are written to files before they are tabulated, so every number in this thesis can be traced to a results file, apart from figures quoted from the literature. The code, pinned requirements, generated tables and figures and results files are in a version-controlled repository whose history records the order the experiments ran in, public at https://github.com/mohammad-sayem-uddin/aip-supcon (visibility checked on 2026-11-26). The downloaded AIPpred, PreAIP and AntiInflam datasets are not redistributed; their addresses and SHA-256 digests are recorded so they can be retrieved and checked. <todo>a permanent archive identifier (for example a Zenodo DOI for the submitted commit) has not been created; this needs the author's own account</todo>`));
add(P(`Two limits on exact reproducibility should be stated. The convolutional and Transformer architectures and the fine-tuning ran on graphics processors, whose floating-point reductions are not bit-identical to those of the central processor, so that repeating those runs reproduces the results to within seed-level variation, not bit by bit. The extraction time of the 650M checkpoint was not recorded reliably, and the time-consuming parts of Phase B on the local machine were run in slices that were not timed as a whole.`));


add(H2('B.6 Deviations from the plan'));
add(P(`The following departures from the original plan are recorded so that the reader can judge their effect. The residue-level architectures use a ${F.par['Phase B residue-level models|per-residue adapter width']}-dimensional learned adapter and 64 hidden units per direction, instead of 128, because unadapted inputs made a single fold impractical on the available processor; this choice was made before any Phase B result was seen. The temperature was fixed at ${F.par['Phase B residue-level models|temperature']} for Phase B, and the temperature sweep was not repeated for the new architectures. Phase B was split across devices as shown in Table ${ref('tab:devices')}. Because the machine had little memory and disk space, the 650M embeddings were extracted once and the checkpoint was deleted afterwards, which is why its extraction could not be timed again. A resume routine in the experiment runner initially mis-matched saved runs and re-ran 22 cross-validation runs of the hybrid network; the duplicates were removed, the original rows were kept and the routine was corrected. Finally, three planned elements were only partly completed: the independent sets of AIPStack could not be obtained; the comparison with other protein language models was completed for ProtT5-XL (encoder) but not for ProtBERT, whose kernel produced only downloaded weights rather than computed embeddings (Section 4.6.4); and the transfer of the method to other peptide families was not attempted (Chapter 4, Section 4.10).`));




  add(H2('B.7 Tables cited from Chapter 3'));

  console.log('  Appendix B takes', relocatedInto('B', B), 'relocated tables');
  // each model: the description Chapter 3 refers to, then its layers
  const ARCH = JSON.parse(fs.readFileSync(`${ROOT}/results/thesis/architectures.json`, 'utf8'));
  add(H2('B.4 The six architectures'));
  for (const [key, title, text] of ARCH) {
    const short = key.split('_')[0];
    add(B.H3(title));
    add(P(text));
    add(caption(`tab:layers_${short.toLowerCase()}`, `Layers of model ${short}. Dropout and normalisation as described above. Source: results/v2/architecture_layers.csv.`));
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
