# BLOCKERS_v2

Everything in the v2 extension that failed or could not be done.

## AIPFusion-Net could not be read
_2026-11-25_

The plan cites AIPFusion-Net (doi 10.3389/fmolb.2026.1952395). The DOI resolves to frontiersin.org, which returned HTTP 503 to automated requests, and web search found no record of the paper. Every statement about what that paper claims or used (training counts, "no overlapping peptide sequences", CD-HIT thresholds, Ind-426) is therefore taken from the plan text and is UNVERIFIED by me. The leakage finding below is stated only as a measurement on the local files and on the original AIPpred / AntiInflam / PreAIP files.

## AIPStack independent sets 2 and 3 not obtainable
_2026-11-25_

The AIPStack paper (PMC9449674) returned a bot-check page, and the Nicole-DH/AIPStack GitHub repository returned 404 (and the GitHub API was rate-limited). Those datasets are therefore not in the cross-benchmark matrix. If you can get the files, drop them into `data/external/aipstack_*/` and re-run `python -m src.v2.phaseA`.

## C4 (ProtBERT / ProtT5) not attempted
_2026-11-25_

C4 is optional in the plan. ProtBERT needs a 1.6 GB and ProtT5-XL (half, encoder) a 2.3 GB download; this Mac had 3.7 GB of free disk (which fluctuates), and the Kaggle kernels have no internet, so the weights would need uploading as a dataset. The question C4 asks (is the weakness ESM-2 specific?) is partly answered by C3: end-to-end adaptation of the same ESM-2 backbone changes the result, so the frozen-embedding setting rather than ESM-2 itself is implicated. To run it: `python -m src.v2.embed_res` generalised to `Rostlab/prot_bert` (sequences need spaces between residues), then `python -m src.v2.phaseC` with the new features.

## D3 (AMP / ACP related-task transfer) not attempted
_2026-11-25_

D3 is optional. It needs antimicrobial or anticancer peptide datasets; no verified download URL was in the plan, and I did not guess one. Phase D2 (cross-dataset generalisation) was run on every AIP dataset that could be obtained (AIPpred, AntiInflam and the local composite).

## Fine-tuning scope and GPU determinism
_2026-11-25_

Only ESM-2 8M was fine-tuned (CV seeds 0-2 x 5 folds, final seeds 0-4). Fine-tuning 150M or 650M was not run. B2, B5 and the fine-tuning ran on Kaggle T4 GPUs, whose floating-point reductions are not bit-identical to the CPU runs used for B3, B4, B6 and v1; each architecture's lambda grid is entirely on one device (results/v2/device_map.json).

## RESOLVED in the completion run: AIPFusion-Net could not be read
_2026-11-26_

The paper is on Europe PMC (PMC13677489) and was read in full; its data repository (github.com/ChenYH7693/AIPFusion-Net) was fetched and its three data files are byte-identical (SHA-256) to the local Benchmark_Dataset, Ind_1049 and Ind_425 (`results/v2/aipfusion_repo_check.csv`). The statements in the earlier entry that were "taken from the plan text" are now checked against the paper: training set 1,451 / 2,339, independent sets Ind-1049 and Ind-426, CD-HIT 0.9 on the training set, "no overlapping sequences retained".

## AIPStack independent sets 2 and 3: still not obtainable (second attempt)
_2026-11-26_

The full text and supplementary tables came from Europe PMC. The repository github.com/Nicole-DH/AIPStack still returns 404; the Wayback Machine holds one snapshot of the repository front page (2024-04-16) but not the `datasets` directory (404 for both requests tried). The supplementary files mmc2/mmc3 contain only performance tables. To close: obtain the datasets from the authors (the paper names a lead contact).

## C4 (ProtBERT / ProtT5) and fine-tuning of 150M / 650M: running on Kaggle at the time of writing
_2026-11-26_

Kernels `aip-ft-s150-gpu`, `aip-ft-s650a-gpu`, `aip-c4bert-cpu`, `aip-c4t5-cpu` were pushed; `aip-ft-s650b-gpu` is pushed by `fetch` when a GPU slot is free. Each kernel checks the sha256 of the weights against the official Hugging Face record and stops on a mismatch (this stopped the first ProtBERT mirror, which was a different checkpoint). Finish with `PYTHONPATH=. .venv/bin/python -m src.v2.finish_completion fetch` and then `analyse` (see the docstring of that script). The first 650M smoke run ran out of GPU memory in AdamW; fixed with `foreach=False`.

## D3 (AMP / ACP transfer): not attempted
_2026-11-26_

Needs a benchmark with a verifiable origin and a documented train/test split, plus the same overlap audit as Phase A before any model is trained. No dataset was fetched because none had been checked against its paper in this run. To do it: pick the benchmark (for example the anticancer-peptide sets of AntiCP 2.0 or the antimicrobial sets of a published AMP predictor), fetch the files and the paper from an open-access record, repeat Phase A (exact and 0.9-identity overlap) and then the pipeline of Chapters 3 and 4 with the lambda grid and the six architectures.
