"""Residue-level frozen ESM-2 embeddings (plus <cls>) cached for Phase B/C.

Storage (embeddings/v2/, gitignored): {short}_res.npy (total_residues, d), {short}_cls.npy (n, d),
{short}_index.json (sequences in the v1 union order, offsets, lengths). <cls>/<eos>/padding are excluded
from the residue matrix. Usage: python -m src.v2.embed_res --checkpoint esm2_t6_8M [--purge-model]
"""
from __future__ import annotations

import argparse
import json
import resource
import shutil
import time
from pathlib import Path

import numpy as np

from src.embed import CHECKPOINTS, WEIGHT_MB, _check_padding_invariance, _load, _resolve, all_sequences
from src.utils import ROOT, Timer, setup_logging
from src.v2.common import R, block, mark

log = setup_logging("embed_res")
OUT = ROOT / "embeddings" / "v2"


def union_sequences() -> list[str]:
    per = all_sequences()
    return list(dict.fromkeys(s for seqs in per.values() for s in seqs))


def load_residue_cache(short: str):
    idx = json.loads((OUT / f"{short}_index.json").read_text())
    res = np.load(OUT / f"{short}_res.npy", mmap_mode="r")
    cls = np.load(OUT / f"{short}_cls.npy")
    return idx, res, cls


def run(checkpoint: str, purge: bool = False, batch_size: int = 32) -> None:
    import torch

    t_all = Timer()
    short, hf = _resolve(checkpoint)
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / f"{short}_res.npy").exists():
        log.info("%s residue cache exists, nothing to do", short)
        return
    need = 1.3 * WEIGHT_MB[short] + 600
    free = shutil.disk_usage(ROOT).free / 1e6
    if free < need:
        block(f"Residue embeddings {short}: not enough disk", f"free {free:.0f} MB < needed {need:.0f} MB")
        mark(f"V2_embed_{short}", "failed", t_all.elapsed(), "insufficient disk")
        return
    hub = Path.home() / ".cache" / "huggingface" / "hub" / ("models--" + hf.replace("/", "--"))
    existed = hub.exists()
    from huggingface_hub import snapshot_download
    snapshot_download(hf, allow_patterns=["*.json", "*.txt", "model.safetensors"])
    device = "cpu"
    tok, model = _load(hf, device)
    _check_padding_invariance(tok, model, device)
    seqs = union_sequences()
    order = np.argsort([len(s) for s in seqs], kind="stable")
    d = model.config.hidden_size
    store: list[np.ndarray | None] = [None] * len(seqs)
    cls = np.zeros((len(seqs), d), dtype=np.float32)
    dtype = np.float32 if CHECKPOINTS[short][1] <= 640 and short == "esm2_t6_8M" else np.float16
    t0 = time.time()
    for bi in range(0, len(order), batch_size):
        idx = order[bi : bi + batch_size]
        enc = tok([seqs[j] for j in idx], return_tensors="pt", padding=True)
        with torch.no_grad():
            h = model(**enc).last_hidden_state
        for k, j in enumerate(idx):
            L = len(seqs[j])
            store[j] = h[k, 1 : 1 + L].numpy().astype(dtype)
            cls[j] = h[k, 0].numpy()
        if (bi // batch_size) % 20 == 0:
            log.info("%s: %d/%d sequences, %.1f min", short, bi, len(seqs), (time.time() - t0) / 60)
    lengths = np.array([len(s) for s in seqs])
    offsets = np.concatenate([[0], np.cumsum(lengths)[:-1]])
    res = np.concatenate(store, axis=0)
    assert res.shape == (lengths.sum(), d) and np.isfinite(res.astype(np.float32)).all()
    np.save(OUT / f"{short}_res.npy", res)
    np.save(OUT / f"{short}_cls.npy", cls)
    (OUT / f"{short}_index.json").write_text(json.dumps({"sequences": seqs, "offsets": offsets.tolist(), "lengths": lengths.tolist(),
                                                           "dtype": str(np.dtype(dtype)), "dim": d}))
    log.info("DONE %s residue cache %s in %.1fs, peak RSS %.0f MB", short, res.shape, time.time() - t0,
             resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6)
    if purge and not existed and hub.exists():
        shutil.rmtree(hub)
    mark(f"V2_embed_{short}", "complete", t_all.elapsed(), f"{res.shape}, {np.dtype(dtype)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--purge-model", action="store_true")
    a = ap.parse_args()
    run(a.checkpoint, a.purge_model)
