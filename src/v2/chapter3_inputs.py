"""Generate the traceable inputs that Chapter 3 quotes but that were not yet in results/.

Writes (all under results/v2/):
  methods_parameters.csv        every design parameter, read from the code objects that were actually used
  architecture_layers.csv       layer/component tables and parameter counts for B1-B6 (+ the fine-tuned 8M model)
  lineage_shared_training.csv   AIPpred benchmark x AntiInflam training: shared sequences and label agreement
  regime_composition.csv        size and class composition of every evaluation regime file
  null_control_identity.csv     shuffled-composition null control for the identity screen
  supcon_floor.csv              analytic floor of the SupCon loss for the batch size and class balance used
  mde_summary.csv               minimum detectable effects by test set and regime (from T5.11)
Run: python -m src.v2.chapter3_inputs
"""
from __future__ import annotations

import inspect
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from src.utils import ROOT
from src.v2.common import R, TABLES, V2

PROC = ROOT / "data" / "processed"


def build_parameters() -> pd.DataFrame:
    from src.data import _aligner
    from src.embed import CHECKPOINTS
    from src.train import Config
    from src.v2 import finetune, models, phaseB, stats
    from src.v2.train import V2Cfg
    import src.pipeline as pipe

    rows = []

    def add(group, name, value, source):
        rows.append({"group": group, "parameter": name, "value": value, "source": source})

    c = Config()
    for k in ("hidden_dims", "dropout", "proj_dim", "lr", "weight_decay", "batch_size", "max_epochs", "patience"):
        add("v1 AIPNet / training loop", k, getattr(c, k), "src/train.py Config defaults")
    add("v1 AIPNet / training loop", "optimizer", "AdamW", "src/train.py")
    add("v1 AIPNet / training loop", "lr_schedule", "CosineAnnealingLR(T_max=max_epochs)", "src/train.py")
    add("v1 AIPNet / training loop", "temperature_default", c.temperature, "src/train.py Config defaults")
    add("v1 AIPNet / training loop", "lambda_grid", list(pipe.LAMBDAS), "src/pipeline.py")
    add("v1 AIPNet / training loop", "temperature_grid", list(pipe.TAUS), "src/pipeline.py")
    add("v1 AIPNet / training loop", "seeds", list(pipe.SEEDS), "src/pipeline.py")
    v = V2Cfg()
    for k in ("lr", "weight_decay", "batch_size", "max_epochs", "patience", "clip", "temperature"):
        add("Phase B residue-level models", k, getattr(v, k), "src/v2/train.py V2Cfg defaults")
    add("Phase B residue-level models", "per-residue adapter width", models.ADAPT, "src/v2/models.py")
    add("Phase B residue-level models", "maximum peptide length (padding)", models.MAXLEN, "src/v2/models.py")
    add("Phase B residue-level models", "lambda_grid", list(phaseB.LAMS), "src/v2/phaseB.py")
    add("Phase B residue-level models", "seeds", list(phaseB.SEEDS), "src/v2/phaseB.py")
    ft = inspect.signature(finetune.fit).parameters
    for k in ("max_epochs", "patience", "bs", "lr_bb", "lr_head"):
        add("C3 fine-tuning", k, ft[k].default, "src/v2/finetune.py fit() defaults")
    add("C3 fine-tuning", "weight_decay", 1e-4, "src/v2/finetune.py (AdamW call)")
    add("C3 fine-tuning", "gradient clipping (max norm)", 1.0, "src/v2/finetune.py")
    add("C3 fine-tuning", "CV seeds", [0, 1, 2], "kernel aip-c3-finetune-gpu command line")
    add("C3 fine-tuning", "final-model seeds", [0, 1, 2, 3, 4], "kernel aip-c3-finetune-gpu command line")
    al = _aligner()
    add("identity screen", "alignment mode", al.mode, "src/data.py")
    add("identity screen", "substitution matrix", "BLOSUM62", "src/data.py")
    add("identity screen", "gap open score", al.open_gap_score, "src/data.py")
    add("identity screen", "gap extend score", al.extend_gap_score, "src/data.py")
    add("identity screen", "LCS prefilter floor", inspect.signature(__import__("src.data", fromlist=["x"]).max_identity_to_train).parameters["floor"].default,
        "src/data.py")
    cc = inspect.signature(stats.compare_arrays).parameters
    add("statistics", "bootstrap resamples", cc["n_boot"].default, "src/v2/stats.py")
    add("statistics", "two-sided alpha", 0.05, "src/v2/stats.py (Z_ALPHA = 1.959964)")
    add("statistics", "power for minimum detectable effect", 0.80, "src/v2/stats.py (Z_POWER = 0.841621)")
    add("statistics", "BH false-discovery rate q", 0.05, "src/v2/phaseE.py")
    add("statistics", "McNemar exact-test cut-off (discordant pairs)", 25, "src/evaluate.py")
    for short, (hf, dim) in CHECKPOINTS.items():
        add("ESM-2", short, f"{hf}; embedding dimension {dim}", "src/embed.py CHECKPOINTS")
    for k, v_ in (("n_estimators", 500), ("class_weight", "balanced")):
        add("baselines", f"RandomForest {k}", v_, "src/baselines.py")
    add("baselines", "SVM grid C", [1, 10, 100], "src/baselines.py")
    add("baselines", "SVM grid gamma", [0.003, 0.01, 0.03, 0.1], "src/baselines.py")
    add("baselines", "LightGBM", "n_estimators=2000, learning_rate=0.05, num_leaves=15, early stopping 50 rounds on an inner 10% hold-out", "src/baselines.py")
    return pd.DataFrame(rows)


def build_layers() -> pd.DataFrame:
    import torch
    from src.model import AIPNet
    from src.v2.models import ADAPT, ARCHS, build

    def group(model, mapping):
        counts = {}
        for n, p in model.named_parameters():
            for prefix, label in mapping:
                if n.startswith(prefix):
                    counts[label] = counts.get(label, 0) + p.numel()
                    break
            else:
                counts[n] = p.numel()
        return counts

    rows = []

    def add(arch, order, comp, desc, params):
        rows.append({"architecture": arch, "order": order, "component": comp, "description": desc, "parameters": int(params)})

    d = 320
    heads_map = [("heads.encoder.0", "enc1"), ("heads.encoder.1", "enc1"), ("heads.encoder.4", "enc2"), ("heads.encoder.5", "enc2"),
                 ("heads.projection", "proj"), ("heads.classifier", "clf")]
    # B1: AIPNet
    m = AIPNet(d)
    g = group(m, [("encoder.0", "b1"), ("encoder.1", "b1"), ("encoder.4", "b2"), ("encoder.5", "b2"), ("projection", "proj"), ("classifier", "clf")])
    add("B1_mlp", 1, "Input", "mean-pooled ESM-2 vector, 320-d, standardised on the training fold", 0)
    add("B1_mlp", 2, "Encoder block 1", "Linear 320 to 512; BatchNorm1d; ReLU; Dropout 0.3", g["b1"])
    add("B1_mlp", 3, "Encoder block 2", "Linear 512 to 256; BatchNorm1d; ReLU; Dropout 0.3", g["b2"])
    add("B1_mlp", 4, "Projection head", "Linear 256 to 128; L2 normalisation (feeds SupCon)", g["proj"])
    add("B1_mlp", 5, "Classifier head", "Linear 256 to 1; raw logit (feeds BCE)", g["clf"])

    heads_common = lambda arch, start, in_dim, g: [
        add(arch, start, "Encoder block", f"Linear {in_dim} to 256; BatchNorm1d; ReLU; Dropout 0.3", g["enc1"]),
        add(arch, start + 1, "Projection head", "Linear 256 to 128; L2 normalisation (feeds SupCon)", g["proj"]),
        add(arch, start + 2, "Classifier head", "Linear 256 to 1; raw logit (feeds BCE)", g["clf"])]

    # B2 CNN
    m = build("B2_cnn", d)
    g = group(m, [("ad.", "ad"), ("convs.0", "c3"), ("convs.1", "c5"), ("convs.2", "c7")] + heads_map)
    add("B2_cnn", 1, "Input", "padded residue embeddings (L x 320), standardised per feature on the training fold", 0)
    add("B2_cnn", 2, "Per-residue adapter", f"Linear 320 to {ADAPT}; ReLU; Dropout 0.2", g["ad"])
    add("B2_cnn", 3, "Convolution branch k=3", f"Conv1d {ADAPT} to 64, kernel 3, padding 1; ReLU; masked global max pool", g["c3"])
    add("B2_cnn", 4, "Convolution branch k=5", f"Conv1d {ADAPT} to 64, kernel 5, padding 2; ReLU; masked global max pool", g["c5"])
    add("B2_cnn", 5, "Convolution branch k=7", f"Conv1d {ADAPT} to 64, kernel 7, padding 3; ReLU; masked global max pool", g["c7"])
    heads_common("B2_cnn", 6, 192, g)
    # B3 BiLSTM
    m = build("B3_bilstm", d)
    g = group(m, [("ad.", "ad"), ("lstm.", "lstm")] + heads_map)
    add("B3_bilstm", 1, "Input", "padded residue embeddings (L x 320), standardised per feature on the training fold", 0)
    add("B3_bilstm", 2, "Per-residue adapter", f"Linear 320 to {ADAPT}; ReLU; Dropout 0.2", g["ad"])
    add("B3_bilstm", 3, "Bidirectional LSTM", "2 layers, 64 hidden units per direction, inter-layer dropout 0.3, packed sequences; final forward and backward states of the top layer concatenated (128-d)", g["lstm"])
    heads_common("B3_bilstm", 4, 128, g)
    # B4 CNN-BiLSTM
    m = build("B4_cnn_bilstm", d)
    g = group(m, [("ad.", "ad"), ("conv.", "conv"), ("lstm.", "lstm")] + heads_map)
    add("B4_cnn_bilstm", 1, "Input", "padded residue embeddings (L x 320), standardised per feature on the training fold", 0)
    add("B4_cnn_bilstm", 2, "Per-residue adapter", f"Linear 320 to {ADAPT}; ReLU; Dropout 0.2", g["ad"])
    add("B4_cnn_bilstm", 3, "Convolution", f"Conv1d {ADAPT} to 64, kernel 5, padding 2; ReLU; Dropout 0.3", g["conv"])
    add("B4_cnn_bilstm", 4, "Bidirectional LSTM", "1 layer, 64 hidden units per direction, packed sequences; outputs masked max-pooled over residues (128-d)", g["lstm"])
    heads_common("B4_cnn_bilstm", 5, 128, g)
    # B5 Transformer
    m = build("B5_transformer", d)
    g = group(m, [("inp.0", "ad"), ("inp.1", "lin"), ("pos", "pos"), ("enc.", "enc")] + heads_map)
    add("B5_transformer", 1, "Input", "padded residue embeddings (L x 320), standardised per feature on the training fold", 0)
    add("B5_transformer", 2, "Per-residue adapter", f"Linear 320 to {ADAPT}; ReLU; Dropout 0.2; then Linear {ADAPT} to 128", g["ad"] + g["lin"])
    add("B5_transformer", 3, "Learned positional embedding", "30 x 128, added to the residue vectors", g["pos"])
    add("B5_transformer", 4, "Transformer encoder", "2 layers, 4 attention heads, feed-forward width 256, dropout 0.1, key-padding mask; masked mean pool (128-d)", g["enc"])
    heads_common("B5_transformer", 5, 128, g)
    # B6 attention pooling
    m = build("B6_attnpool", d)
    g = group(m, [("att.", "att"), ("heads.encoder.0", "b1"), ("heads.encoder.1", "b1"), ("heads.encoder.4", "b2"), ("heads.encoder.5", "b2"),
                  ("heads.projection", "proj"), ("heads.classifier", "clf")])
    add("B6_attnpool", 1, "Input", "padded residue embeddings (L x 320), standardised per feature on the training fold", 0)
    add("B6_attnpool", 2, "Attention pooling", "Linear 320 to 128; tanh; Linear 128 to 1; masked softmax over residues; weighted sum of the residue vectors (320-d)", g["att"])
    add("B6_attnpool", 3, "Encoder block 1", "Linear 320 to 512; BatchNorm1d; ReLU; Dropout 0.3 (as B1)", g["b1"])
    add("B6_attnpool", 4, "Encoder block 2", "Linear 512 to 256; BatchNorm1d; ReLU; Dropout 0.3 (as B1)", g["b2"])
    add("B6_attnpool", 5, "Projection head", "Linear 256 to 128; L2 normalisation (feeds SupCon)", g["proj"])
    add("B6_attnpool", 6, "Classifier head", "Linear 256 to 1; raw logit (feeds BCE)", g["clf"])
    # C3 fine-tuned model
    cfgp = ROOT / "data" / "external" / "kaggle_dataset" / "esm2_t6_8M_UR50D"
    try:
        from transformers import EsmModel
        bb = EsmModel.from_pretrained(str(cfgp), add_pooling_layer=False)
        nb = sum(p.numel() for p in bb.parameters())
        cfg = bb.config
        add("C3_finetune", 1, "ESM-2 8M backbone", f"{cfg.num_hidden_layers} Transformer layers, hidden size {cfg.hidden_size}, {cfg.num_attention_heads} attention heads; masked mean pool over residues", nb)
    except Exception as e:  # weights not on disk: leave an explicit marker rather than a number
        add("C3_finetune", 1, "ESM-2 8M backbone", f"TODO: parameter count unavailable ({type(e).__name__})", 0)
    add("C3_finetune", 2, "Head", "Linear 320 to 256; BatchNorm1d; ReLU; Dropout 0.3; Linear 256 to 1", 320 * 256 + 256 + 2 * 256 + 256 + 1)
    df = pd.DataFrame(rows)
    tot = df.groupby("architecture")["parameters"].transform("sum")
    df["architecture_total_parameters"] = tot
    return df


def lineage_shared() -> pd.DataFrame:
    from src.v2.phaseA import load_sources, lab_map
    S = load_sources()
    la, lt = lab_map(S["AIPpred_benchmark"]), lab_map(S["AntiInflam_training"])
    shared = set(la) & set(lt)
    dis = {s for s in shared if la[s] != lt[s]}
    B = S["local_Benchmark"]
    lb = lab_map(B)
    only_ai = set(lt) - set(la)
    rows = [
        {"quantity": "sequences shared by the AIPpred benchmark and the AntiInflam training set", "value": len(shared)},
        {"quantity": "of which carry the same label in both", "value": len(shared) - len(dis)},
        {"quantity": "of which carry opposite labels", "value": len(dis)},
        {"quantity": "local Benchmark sequences carrying both labels", "value": sum(1 for s, l in lb.items() if len(l) > 1)},
        {"quantity": "opposite-label shared sequences that equal the local Benchmark's label-conflicted sequences", "value": len(dis & {s for s, l in lb.items() if len(l) > 1})},
        {"quantity": "AntiInflam training sequences not in the AIPpred benchmark", "value": len(only_ai)},
        {"quantity": "of those, present in the local Benchmark", "value": len(only_ai & set(lb))},
        {"quantity": "of those, absent from the local Benchmark", "value": len(only_ai - set(lb))},
        {"quantity": "sequences within the AIPpred benchmark carrying both labels", "value": len({s for s, l in la.items() if len(l) > 1})},
        {"quantity": "sequences within the AntiInflam training set carrying both labels", "value": len({s for s, l in lt.items() if len(l) > 1})},
    ]
    return pd.DataFrame(rows)


def regime_composition() -> pd.DataFrame:
    rows = []
    b = pd.read_csv(PROC / "benchmark_clean.csv")
    rows.append({"file": "benchmark_clean", "n": len(b), "positive": int((b.label == 1).sum()), "negative": int((b.label == 0).sum())})
    for ts in ("ind_425", "ind_1049"):
        for rg in ("a", "b", "c"):
            d = pd.read_csv(PROC / f"{ts}_regime_{rg}.csv")
            rows.append({"file": f"{ts}_regime_{rg}", "n": len(d), "positive": int((d.label == 1).sum()), "negative": int((d.label == 0).sum())})
    df = pd.DataFrame(rows)
    df["positive_rate"] = (df.positive / df.n).round(4)
    return df


def null_control(reps: int = 20) -> pd.DataFrame:
    """Shuffle residues within each test sequence (composition and length preserved, order destroyed) and repeat the identity screen."""
    from src.data import max_identity_to_train
    train = pd.read_csv(PROC / "benchmark_clean.csv")["sequence"].tolist()
    rows = []
    for ts, name in (("ind_425", "Ind_425"), ("ind_1049", "Ind_1049")):
        a = pd.read_csv(PROC / f"{ts}_regime_a.csv")["sequence"].tolist()
        real = max_identity_to_train(a, train, floor=0.8)
        for thr in (0.8, 0.9, 1.0):
            rows.append({"test_set": name, "condition": "observed", "replicate": 0, "threshold": thr, "n": len(a),
                         "n_at_or_above": int((real >= thr - 1e-12).sum()), "fraction": float((real >= thr - 1e-12).mean())})
        rng = np.random.default_rng(0)
        for r in range(1, reps + 1):
            sh = ["".join(rng.permutation(list(s))) for s in a]
            mx = max_identity_to_train(sh, train, floor=0.8)
            for thr in (0.8, 0.9, 1.0):
                rows.append({"test_set": name, "condition": "shuffled composition-preserving", "replicate": r, "threshold": thr, "n": len(a),
                             "n_at_or_above": int((mx >= thr - 1e-12).sum()), "fraction": float((mx >= thr - 1e-12).mean())})
    return pd.DataFrame(rows)


def supcon_floor() -> pd.DataFrame:
    b = pd.read_csv(PROC / "benchmark_clean.csv")
    p = float((b.label == 1).mean())
    B = 128
    rows = []
    for name, frac in (("positive anchor", p), ("negative anchor", 1 - p)):
        npos = (B - 1) * frac
        rows.append({"anchor": name, "class_fraction_benchmark_clean": round(frac, 4), "batch_size": B,
                     "expected_positives_per_anchor": round(npos, 2), "floor_log_P": round(math.log(npos), 3)})
    return pd.DataFrame(rows)


def mde_summary() -> pd.DataFrame:
    t = pd.read_csv(TABLES / "T5.11_corrected_significance.csv")
    sub = t[t["comparison"].str.contains("vs 0|lambda=2,tau")].copy()
    g = sub.groupby(["test_set", "regime"]).agg(n=("n", "first"), comparisons=("n", "size"), mde_mcc_median=("mcc_mde80", "median"),
                                               mde_mcc_min=("mcc_mde80", "min"), mde_mcc_max=("mcc_mde80", "max"),
                                               mde_auroc_median=("auroc_mde80", "median")).reset_index()
    return g.round(4)


def main() -> None:
    V2.mkdir(parents=True, exist_ok=True)
    build_parameters().to_csv(V2 / "methods_parameters.csv", index=False)
    build_layers().to_csv(V2 / "architecture_layers.csv", index=False)
    lineage_shared().to_csv(V2 / "lineage_shared_training.csv", index=False)
    regime_composition().to_csv(V2 / "regime_composition.csv", index=False)
    supcon_floor().to_csv(V2 / "supcon_floor.csv", index=False)
    mde_summary().to_csv(V2 / "mde_summary.csv", index=False)
    null_control().to_csv(V2 / "null_control_identity.csv", index=False)
    print("written to", V2)


def sequence_validation() -> pd.DataFrame:
    from src.v2.common import STD
    from src.v2.phaseA import load_sources
    rows = []
    for k, d in load_sources().items():
        bad = int((~d["sequence"].str.fullmatch(f"[{STD}]+")).sum())
        rows.append({"dataset": k, "rows": len(d), "unique_sequences": int(d["sequence"].nunique()), "rows_with_non_standard_residues": bad,
                     "length_min": int(d["sequence"].str.len().min()), "length_max": int(d["sequence"].str.len().max())})
    return pd.DataFrame(rows)


def feature_dimensions() -> pd.DataFrame:
    from src.features import aac, combine, ctd, dpc, length_feat
    s = ["ACDEFGHIKLMNPQRSTVWY"]
    rows = [{"feature": "AAC", "dimension": aac(s).shape[1]}, {"feature": "DPC", "dimension": dpc(s).shape[1]},
            {"feature": "CTD", "dimension": ctd(s).shape[1]}, {"feature": "length", "dimension": length_feat(s).shape[1]},
            {"feature": "AAC+DPC+CTD+length (hand-crafted set)", "dimension": combine(s, ("aac", "dpc", "ctd", "len")).shape[1]},
            {"feature": "AAC+length (AAC baselines)", "dimension": combine(s, ("aac", "len")).shape[1]}]
    return pd.DataFrame(rows)


def pooling_dimensions() -> pd.DataFrame:
    rows = []
    feat = V2 / "features"
    for p in ("mean", "max", "meanmax", "cls", "firstlast"):
        f = feat / f"esm650_{p}" / "bench_X.npy"
        if f.exists():
            rows.append({"variant": p, "dimension": int(np.load(f, mmap_mode="r").shape[1])})
        else:
            rows.append({"variant": p, "dimension": "TODO: feature cache not on disk"})
    return pd.DataFrame(rows)


def environment() -> pd.DataFrame:
    import platform
    import subprocess
    rows = [{"item": "local machine", "value": subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()},
            {"item": "local logical cores", "value": subprocess.run(["sysctl", "-n", "hw.ncpu"], capture_output=True, text=True).stdout.strip()},
            {"item": "local memory (bytes)", "value": subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout.strip()},
            {"item": "local OS", "value": platform.platform()}]
    log = ROOT / "data" / "external" / "kaggle_smoke_out" / "aip-gpu-smoke.log"
    if log.exists():
        txt = log.read_text()
        import re
        try:
            ev = json.loads(txt)
            txt = "".join(e.get("data", "") for e in ev)
        except Exception:
            pass
        for pat, label in ((r"python (\S+) torch (\S+)", "Kaggle kernel python and torch"), (r"(Tesla T4)", "Kaggle GPU model"), (r"GPU 1:", "Kaggle second GPU present")):
            m = re.search(pat, txt)
            rows.append({"item": label, "value": " ".join(m.groups()) if m and m.groups() else ("yes" if m else "TODO: not found in kernel log")})
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        if "==" in line:
            n, v = line.split("==")
            rows.append({"item": f"package {n}", "value": v})
    return pd.DataFrame(rows)


def extra() -> None:
    sequence_validation().to_csv(V2 / "sequence_validation.csv", index=False)
    feature_dimensions().to_csv(V2 / "feature_dimensions.csv", index=False)
    pooling_dimensions().to_csv(V2 / "pooling_dimensions.csv", index=False)
    environment().to_csv(V2 / "environment.csv", index=False)


if __name__ == "__main__":
    main()
    extra()
    print("extra inputs written")
