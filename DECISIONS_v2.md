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
