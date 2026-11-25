"""Shared helpers for the v2 extension. Never writes to v1 result files, DECISIONS.md or BLOCKERS.md."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from src.utils import ROOT

R = ROOT / "results"
V2 = R / "v2"
TABLES = R / "tables"
EXT = ROOT / "data" / "external"
STD = "ACDEFGHIKLMNPQRSTVWY"


def note(fname: str, heading: str, body: str) -> None:
    """Append to DECISIONS_v2.md / BLOCKERS_v2.md (HANDOFF_REPORT.md embeds both)."""
    p = ROOT / fname
    if not p.exists():
        p.write_text(f"# {fname.replace('.md', '')}\n\n")
    with open(p, "a") as fh:
        fh.write(f"## {heading}\n_{datetime.now().isoformat(timespec='seconds')}_\n\n{body.strip()}\n\n")


def decide(heading: str, body: str) -> None:
    note("DECISIONS_v2.md", heading, body)


def block(heading: str, body: str) -> None:
    note("BLOCKERS_v2.md", heading, body)


def norm_seq(s: str) -> str:
    return re.sub(r"\s+", "", s).upper()


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def mark(stage: str, status: str, secs: float, notes: str = "") -> None:
    from src.utils import mark_stage
    mark_stage(stage, status, secs, notes)


def greedy_cluster(seqs: list[str], thr: float) -> tuple[list[str], dict[str, str]]:
    """CD-HIT-style greedy incremental clustering (re-implementation, not the CD-HIT binary).

    Sequences are sorted by length (descending); each joins the first existing representative with
    global-alignment identity >= thr (identity = matches / length of the shorter sequence, as CD-HIT
    defines it) or becomes a new representative. Returns (representatives, member -> representative).
    """
    import numpy as np
    from rapidfuzz.distance import LCSseq
    from rapidfuzz.process import cdist

    from src.data import pairwise_identity

    order = sorted(dict.fromkeys(seqs), key=lambda s: (-len(s), s))
    reps: list[str] = []
    assign: dict[str, str] = {}
    for s in order:
        hit = None
        if reps:
            lcs = cdist([s], reps, scorer=LCSseq.similarity, dtype=np.int32)[0]
            bound = lcs / np.minimum(len(s), np.array([len(r) for r in reps]))
            for j in np.nonzero(bound >= thr - 1e-12)[0]:
                if pairwise_identity(s, reps[j]) >= thr - 1e-12:
                    hit = reps[j]
                    break
        if hit is None:
            reps.append(s)
            assign[s] = s
        else:
            assign[s] = hit
    return reps, assign
