"""Finish the Kaggle-dependent parts of the completion run (tasks 2.2 and 3.1). Foreground, resumable; run it as often as you like.

    PYTHONPATH=. .venv/bin/python -m src.v2.finish_completion status     # state of every kernel
    PYTHONPATH=. .venv/bin/python -m src.v2.finish_completion fetch      # download outputs of finished kernels, push s650b when a GPU slot is free
    PYTHONPATH=. .venv/bin/python -m src.v2.finish_completion analyse    # scale-axis statistics (T5.13*, fig 5.11) and C4 (T5.14*) from what has arrived

Kernels: aip-ft-s150-gpu (150M, all runs), aip-ft-s650a-gpu (650M, CV seeds 0 and 1), aip-ft-s650b-gpu (650M, CV seed 2 + 5 final seeds; pushed by `fetch`
once s150 or s650a has finished), aip-c4bert-cpu and aip-c4t5-cpu (frozen ProtBERT / ProtT5 embeddings, weights gated on the official sha256).
"""
from __future__ import annotations
import glob, shutil, subprocess, sys
from pathlib import Path
from src.utils import ROOT

EXT = ROOT / "data/external"; V2 = ROOT / "results/v2"; SC = V2 / "scale"; C4 = V2 / "c4"; USER = "yeasinarafatshihab"
KERNELS = {"aip-ft-s150-gpu": ("scale", "kaggle_kernel_s150"), "aip-ft-s650a-gpu": ("scale", "kaggle_kernel_s650a"), "aip-ft-s650b-gpu": ("scale", "kaggle_kernel_s650b"),
           "aip-c4bert-cpu": ("c4", "kaggle_kernel_c4bert"), "aip-c4t5-cpu": ("c4", "kaggle_kernel_c4t5")}

def kaggle(*a):
    return subprocess.run(["kaggle", *a], capture_output=True, text=True).stdout.strip()

def status(k):
    out = kaggle("kernels", "status", f"{USER}/{k}")
    if "has status" not in out: return "NOT PUSHED" if "404" in out or "Not Found" in out or not out else out[-60:]
    return out.split("has status")[1].strip().strip('"').replace("KernelWorkerStatus.", "")

def fetch():
    st = {k: status(k) for k in KERNELS}; print(st)
    for k, (kind, d) in KERNELS.items():
        if st[k] != "COMPLETE": continue
        out = EXT / f"kaggle_out_{k}"
        if (out / ".fetched").exists(): continue
        out.mkdir(exist_ok=True); print(kaggle("kernels", "output", f"{USER}/{k}", "-p", str(out))[-120:])
        if kind == "scale":
            SC.mkdir(parents=True, exist_ok=True); (SC / "predictions").mkdir(exist_ok=True)
            for f in glob.glob(str(out / "finetune_scale_*.csv")): shutil.copy(f, SC / f"{Path(f).stem}__{k}.csv")
            for f in glob.glob(str(out / "predictions" / "*.csv")): shutil.copy(f, SC / "predictions" / Path(f).name)
        else:
            C4.mkdir(parents=True, exist_ok=True)
            for f in glob.glob(str(out / "*.npz")): shutil.copy(f, C4 / Path(f).name)
        (out / ".fetched").write_text("ok"); print("fetched", k)
    free_gpu = sum(1 for k in ("aip-ft-s150-gpu", "aip-ft-s650a-gpu") if st[k] in ("COMPLETE", "ERROR"))
    if st.get("aip-ft-s650b-gpu") in ("NOT PUSHED", "") and free_gpu:
        print(kaggle("kernels", "push", "-p", str(EXT / "kaggle_kernel_s650b")))

def analyse():
    if list(SC.glob("finetune_scale_*.csv")):
        subprocess.run([sys.executable, "-m", "src.v2.phase_scale"], check=False)
    if list(C4.glob("*.npz")):
        for _ in range(1): subprocess.run([sys.executable, "-m", "src.v2.phaseC4", "run", "480"], check=False)
        subprocess.run([sys.executable, "-m", "src.v2.phaseC4", "stats"], check=False)

if __name__ == "__main__":
    {"status": lambda: print({k: status(k) for k in KERNELS}), "fetch": fetch, "analyse": analyse}[sys.argv[1]]()
