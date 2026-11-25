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
