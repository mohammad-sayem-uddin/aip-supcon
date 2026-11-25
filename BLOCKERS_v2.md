# BLOCKERS_v2

Everything in the v2 extension that failed or could not be done.

## AIPFusion-Net could not be read
_2026-11-25_

The plan cites AIPFusion-Net (doi 10.3389/fmolb.2026.1952395). The DOI resolves to frontiersin.org, which returned HTTP 503 to automated requests, and web search found no record of the paper. Every statement about what that paper claims or used (training counts, "no overlapping peptide sequences", CD-HIT thresholds, Ind-426) is therefore taken from the plan text and is UNVERIFIED by me. The leakage finding below is stated only as a measurement on the local files and on the original AIPpred / AntiInflam / PreAIP files.

## AIPStack independent sets 2 and 3 not obtainable
_2026-11-25_

The AIPStack paper (PMC9449674) returned a bot-check page, and the Nicole-DH/AIPStack GitHub repository returned 404 (and the GitHub API was rate-limited). Those datasets are therefore not in the cross-benchmark matrix. If you can get the files, drop them into `data/external/aipstack_*/` and re-run `python -m src.v2.phaseA`.
