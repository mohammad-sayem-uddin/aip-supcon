# BLOCKERS

Everything that failed or could not run, with diagnosis.

## T5.7 needs published numbers
_2026-11-25T08:04:09_

Table 5.7 (comparison with AIPpred, PreAIP, etc.) contains only this study's Regime A results. No verified published figures were available to the run and none were invented; copy them from the original papers into `results/tables/T5_7_comparison_published.csv`.

## Housekeeping: latent vectors were briefly committed
_2026-11-25_

`results/latents/*.npz` (36 MB; they contain copies of raw ESM-2 embeddings) were committed in f2c18a4 before the ignore rule existed, and untracked in ed4fdc8 (and gitignored). The repository has no remote, so nothing was pushed; the files remain in local history. To purge them: `git filter-repo --path results/latents --invert-paths` (rewrites history, so I did not do it unasked).
