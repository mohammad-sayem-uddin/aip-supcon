# aip-supcon

Research question: does adding a supervised contrastive objective (SupCon) to a classifier head on frozen ESM-2 embeddings measurably improve anti-inflammatory peptide (AIP) prediction over the identical architecture trained with BCE alone (lambda = 0), when evaluated on leakage-free independent test sets?

Pipeline (see `src/`): data audit and regimes A/B/C (`data.py`) -> ESM-2 embeddings (`embed.py`) -> AIPNet + SupCon (`model.py`, `losses.py`, `train.py`) -> baselines (`features.py`, `baselines.py`) -> statistics (`evaluate.py`) -> tables/figures (`tables.py`, `visualize.py`) -> `python -m src.report`. Orchestration: `src/pipeline.py`, `run_tail.sh`. Results: `results/`, `HANDOFF_REPORT.md`, `INTERPRETATION.md`, `DECISIONS.md`, `BLOCKERS.md`.

Experiments: AAC+SVM, AAC+RF, AAC+DPC+CTD+LightGBM, ESM-2+LogReg, ESM-2+MLP (lambda=0), ESM-2+SupCon (lambda>0); lambda in {0, 0.1, 0.25, 0.5, 1, 2}, tau in {0.05, 0.07, 0.1, 0.5}, 5 seeds x 5 folds, four ESM-2 checkpoints.
