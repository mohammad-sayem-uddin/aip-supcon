"""Shared helpers: seeding, device selection, run logging, stage markers."""
from __future__ import annotations

import json
import logging
import os
import random
import time
from datetime import datetime
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = ROOT / "logs"
STAGE_DIR = ROOT / "results" / ".stages"


def set_seed(seed: int) -> None:
    import torch

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def get_device(prefer: str | None = None) -> str:
    import torch

    if prefer:
        return prefer
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def run_id() -> str:
    """One run id shared by every process of a run (stored in logs/.run_id)."""
    LOG_DIR.mkdir(exist_ok=True)
    f = LOG_DIR / ".run_id"
    if os.environ.get("AIP_RUN_ID"):
        return os.environ["AIP_RUN_ID"]
    if f.exists():
        return f.read_text().strip()
    rid = datetime.now().strftime("%Y%m%d_%H%M%S")
    f.write_text(rid)
    return rid


def setup_logging(name: str) -> logging.Logger:
    LOG_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")
    fh = logging.FileHandler(LOG_DIR / f"run_{run_id()}.log")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    return logger


def stage_done(stage: str) -> bool:
    f = STAGE_DIR / f"{stage}.json"
    return f.exists() and json.loads(f.read_text()).get("status") == "complete"


def mark_stage(stage: str, status: str, wall_seconds: float, notes: str = "") -> None:
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    prev = {}
    f = STAGE_DIR / f"{stage}.json"
    if f.exists():
        prev = json.loads(f.read_text())
    total = float(prev.get("wall_seconds", 0.0)) + wall_seconds
    f.write_text(
        json.dumps(
            {
                "stage": stage,
                "status": status,
                "wall_seconds": total,
                "notes": notes,
                "finished_at": datetime.now().isoformat(timespec="seconds"),
            },
            indent=2,
        )
    )


class Timer:
    def __init__(self) -> None:
        self.t0 = time.time()

    def elapsed(self) -> float:
        return time.time() - self.t0


def append_note(fname: str, heading: str, body: str) -> None:
    """Append an entry to DECISIONS.md or BLOCKERS.md."""
    p = ROOT / fname
    if not p.exists():
        p.write_text(f"# {fname.replace('.md', '')}\n\n")
    with open(p, "a") as fh:
        fh.write(f"## {heading}\n_{datetime.now().isoformat(timespec='seconds')}_\n\n{body.strip()}\n\n")


class ProgressLogger:
    """Logs a progress line at most every `every` seconds (used for stages > 30 min)."""

    def __init__(self, total: int, name: str, logger: logging.Logger, every: float = 300.0) -> None:
        self.total, self.name, self.logger, self.every = total, name, logger, every
        self.done, self.t0, self.last = 0, time.time(), time.time()

    def step(self, n: int = 1) -> None:
        self.done += n
        if time.time() - self.last >= self.every:
            self.last = time.time()
            self.logger.info("PROGRESS %s: %d/%d (%.0f%%) after %.1f min", self.name, self.done, self.total,
                             100 * self.done / self.total, (time.time() - self.t0) / 60)
