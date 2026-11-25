"""Frozen ESM-2 feature extraction with mean pooling over real residues only."""
from __future__ import annotations

import argparse
import json
import resource
import shutil
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import ROOT, Timer, get_device, mark_stage, setup_logging

log = setup_logging("embed")

EMB_DIR = ROOT / "embeddings"
RESULTS = ROOT / "results"

CHECKPOINTS = {
    "esm2_t6_8M": ("facebook/esm2_t6_8M_UR50D", 320),
    "esm2_t12_35M": ("facebook/esm2_t12_35M_UR50D", 480),
    "esm2_t30_150M": ("facebook/esm2_t30_150M_UR50D", 640),
    "esm2_t33_650M": ("facebook/esm2_t33_650M_UR50D", 1280),
}
# approximate size of the safetensors weights in MB (used for the disk-space preflight)
WEIGHT_MB = {"esm2_t6_8M": 35, "esm2_t12_35M": 140, "esm2_t30_150M": 600, "esm2_t33_650M": 2600}


def _resolve(checkpoint: str) -> tuple[str, str]:
    """Accept a short name ('esm2_t6_8M'), a long name ('esm2_t6_8M_UR50D') or a HF id."""
    for short, (hf, _) in CHECKPOINTS.items():
        if checkpoint in (short, hf, hf.split("/")[-1]):
            return short, hf
    raise ValueError(f"unknown checkpoint {checkpoint}")


def _pool(hidden, attention_mask):
    """Mean over real residues: drop <cls> (pos 0), <eos> (last real pos) and padding."""
    import torch

    mask = attention_mask.clone().float()
    mask[:, 0] = 0.0
    last = attention_mask.sum(dim=1) - 1
    mask[torch.arange(mask.shape[0]), last] = 0.0
    summed = (hidden * mask.unsqueeze(-1)).sum(dim=1)
    return summed / mask.sum(dim=1, keepdim=True)


def _load(hf_id: str, device: str):
    import torch
    from transformers import EsmModel, EsmTokenizer

    tok = EsmTokenizer.from_pretrained(hf_id)
    model = EsmModel.from_pretrained(hf_id, add_pooling_layer=False)
    model.eval().to(device)
    for p in model.parameters():
        p.requires_grad_(False)
    return tok, model


def _embed_batch(tok, model, seqs: list[str], device: str):
    import torch

    enc = tok(seqs, return_tensors="pt", padding=True)
    enc = {k: v.to(device) for k, v in enc.items()}
    with torch.no_grad():
        hidden = model(**enc).last_hidden_state
    return _pool(hidden, enc["attention_mask"]).float().cpu().numpy()


def _check_padding_invariance(tok, model, device: str) -> None:
    short, long_ = "ACDEFGHIK", "ACDEFGHIKLMNPQRSTVWYACDEFGHIKL"
    alone = _embed_batch(tok, model, [short], device)[0]
    padded = _embed_batch(tok, model, [short, long_], device)[0]
    assert np.allclose(alone, padded, atol=1e-4), (
        "pooling differs between padded and unpadded batch: "
        f"max abs diff {np.abs(alone - padded).max():.2e}"
    )
    log.info("padding-invariance assertion passed (max diff %.2e)", np.abs(alone - padded).max())


def embed_sequences(sequences: list[str], checkpoint: str, device: str | None = None,
                    batch_size: int = 32) -> np.ndarray:
    """Return float32 (n_sequences, dim) mean-pooled frozen ESM-2 embeddings."""
    from tqdm import tqdm

    device = device or get_device()
    _, hf = _resolve(checkpoint)
    tok, model = _load(hf, device)
    _check_padding_invariance(tok, model, device)
    order = np.argsort([len(s) for s in sequences], kind="stable")
    out = np.zeros((len(sequences), model.config.hidden_size), dtype=np.float32)
    for i in tqdm(range(0, len(order), batch_size), desc=checkpoint, mininterval=30):
        idx = order[i : i + batch_size]
        out[idx] = _embed_batch(tok, model, [sequences[j] for j in idx], device)
    return out


def all_sequences() -> dict[str, list[str]]:
    from src.data import FASTAS, parse_fasta

    names = {"Benchmark": "benchmark", "Ind_425": "ind425", "Ind_1049": "ind1049"}
    return {names[k]: list(dict.fromkeys(parse_fasta(p)["sequence"])) for k, p in FASTAS.items()}


def _cache_paths(short: str, dataset: str):
    return EMB_DIR / f"{short}_{dataset}.npy", EMB_DIR / f"{short}_{dataset}.json"


def load_cached(short: str, dataset: str = "all"):
    npy, js = _cache_paths(short, dataset)
    if npy.exists() and js.exists():
        return np.load(npy), json.loads(js.read_text())
    return None


def get_embeddings(short: str, sequences: list[str]) -> np.ndarray:
    """Look up cached embeddings (from the union cache) for the given sequences."""
    cached = load_cached(short, "all")
    if cached is None:
        raise FileNotFoundError(f"no embedding cache for {short}; run python -m src.embed --checkpoint {short}")
    mat, seqs = cached
    idx = {s: i for i, s in enumerate(seqs)}
    return mat[[idx[s] for s in sequences]]


def run(checkpoint: str, device: str | None, batch_size: int, purge: bool, force: bool) -> None:
    t_all = Timer()
    short, hf = _resolve(checkpoint)
    device = device or get_device()
    per_ds = all_sequences()
    union = list(dict.fromkeys(s for seqs in per_ds.values() for s in seqs))
    log.info("%s: %d unique sequences across %d datasets, device=%s", short, len(union), len(per_ds), device)

    cached = None if force else load_cached(short, "all")
    if cached is not None and set(union) <= set(cached[1]):
        log.info("cache covers all requested sequences; nothing to compute")
        mark_stage(f"S3_{short}", "complete", 0.0, "cached")
        return

    EMB_DIR.mkdir(exist_ok=True)
    hub = Path.home() / ".cache" / "huggingface" / "hub" / ("models--" + hf.replace("/", "--"))
    existed = hub.exists()
    need_mb = 1.3 * WEIGHT_MB[short] + 200
    free_mb = shutil.disk_usage(ROOT).free / 1e6
    if free_mb < need_mb:
        from src.utils import append_note
        append_note("BLOCKERS.md", f"S3 {short}: not enough free disk",
                    f"Free disk {free_mb:.0f} MB < {need_mb:.0f} MB needed (weights ~{WEIGHT_MB[short]} MB). "
                    f"Not attempted to avoid filling the disk.\n\nTo run elsewhere (e.g. Kaggle GPU or a machine with space):\n"
                    f"`python -m src.embed --checkpoint {short} --purge-model` then copy "
                    f"`embeddings/{short}_*.npy/.json` and `results/embedding_timings.csv` rows back.")
        log.error("%s skipped: free %.0f MB < needed %.0f MB", short, free_mb, need_mb)
        mark_stage(f"S3_{short}", "failed", t_all.elapsed(), "insufficient disk")
        return
    t_dl = time.time()
    from huggingface_hub import snapshot_download
    snapshot_download(hf, allow_patterns=["*.json", "*.txt", "model.safetensors"])
    dl_seconds = time.time() - t_dl
    log.info("checkpoint ready (download/verify %.1fs)", dl_seconds)

    t0 = time.time()
    mat = embed_sequences(union, short, device, batch_size)
    wall = time.time() - t0
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6  # bytes on macOS
    assert mat.shape == (len(union), CHECKPOINTS[short][1]) and np.isfinite(mat).all()

    np.save(EMB_DIR / f"{short}_all.npy", mat)
    (EMB_DIR / f"{short}_all.json").write_text(json.dumps(union))
    lookup = {s: i for i, s in enumerate(union)}
    for ds, seqs in per_ds.items():
        npy, js = _cache_paths(short, ds)
        np.save(npy, mat[[lookup[s] for s in seqs]])
        js.write_text(json.dumps(seqs))

    gpu = None
    if device == "cuda":
        import torch
        gpu = torch.cuda.get_device_name(0)
    row = {
        "checkpoint": short, "hf_id": hf, "device": device, "gpu": gpu, "dim": mat.shape[1],
        "n_sequences": len(union), "batch_size": batch_size, "embed_seconds": round(wall, 2),
        "download_seconds": round(dl_seconds, 2), "peak_rss_mb": round(peak_mb, 1),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    f = RESULTS / "embedding_timings.csv"
    pd.concat([pd.read_csv(f), pd.DataFrame([row])]).to_csv(f, index=False) if f.exists() else \
        pd.DataFrame([row]).to_csv(f, index=False)
    log.info("DONE %s: %.1fs embed, peak RSS %.0f MB", short, wall, peak_mb)
    if purge and not existed and hub.exists():
        shutil.rmtree(hub)
        log.info("purged downloaded checkpoint cache %s to save disk", hub)
    mark_stage(f"S3_{short}", "complete", t_all.elapsed(), f"device={device}, embed {wall:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="esm2_t6_8M")
    ap.add_argument("--datasets", default="all")
    ap.add_argument("--device", default=None)
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--purge-model", action="store_true", help="delete the downloaded checkpoint after embedding")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    run(a.checkpoint, a.device, a.batch_size, a.purge_model, a.force)
