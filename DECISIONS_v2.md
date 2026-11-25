# DECISIONS_v2

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
