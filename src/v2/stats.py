"""Paired comparison statistics for v2: DeLong, McNemar, paired bootstrap CIs, minimum detectable effect, BH-FDR."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

from src.evaluate import _confusion, _stratified_indices, delong_test, mcc_from_counts, mcnemar_test

Z_ALPHA, Z_POWER = 1.959964, 0.841621  # two-sided alpha 0.05, power 0.80


def _mcc(y, pred) -> float:
    return mcc_from_counts(*_confusion(y, pred))


def compare_arrays(y, pa, pb, ya=None, yb=None, n_boot: int = 2000, seed: int = 0) -> dict:
    """a minus b on the same samples. Predictions default to threshold 0.5. Returns effects, CIs, p-values, MDE."""
    y = np.asarray(y).astype(int)
    pa, pb = np.asarray(pa, float), np.asarray(pb, float)
    ya = (pa >= 0.5).astype(int) if ya is None else np.asarray(ya).astype(int)
    yb = (pb >= 0.5).astype(int) if yb is None else np.asarray(yb).astype(int)
    z, p_dl = delong_test(y, pa, pb)
    stat, p_mc = mcnemar_test(y, ya, yb)
    rng = np.random.default_rng(seed)
    d_mcc, d_auc = [], []
    for _ in range(n_boot):
        i = _stratified_indices(y, rng)
        d_mcc.append(_mcc(y[i], ya[i]) - _mcc(y[i], yb[i]))
        d_auc.append(roc_auc_score(y[i], pa[i]) - roc_auc_score(y[i], pb[i]))
    d_mcc, d_auc = np.array(d_mcc), np.array(d_auc)
    mcc_diff = _mcc(y, ya) - _mcc(y, yb)
    auc_diff = roc_auc_score(y, pa) - roc_auc_score(y, pb)
    return {
        "n": len(y), "mcc_a": _mcc(y, ya), "mcc_b": _mcc(y, yb), "mcc_diff": mcc_diff,
        "mcc_diff_lo": float(np.quantile(d_mcc, 0.025)), "mcc_diff_hi": float(np.quantile(d_mcc, 0.975)),
        "mcc_diff_se": float(d_mcc.std(ddof=1)), "mcc_mde80": float((Z_ALPHA + Z_POWER) * d_mcc.std(ddof=1)),
        "auroc_a": float(roc_auc_score(y, pa)), "auroc_b": float(roc_auc_score(y, pb)), "auroc_diff": float(auc_diff),
        "auroc_diff_lo": float(np.quantile(d_auc, 0.025)), "auroc_diff_hi": float(np.quantile(d_auc, 0.975)),
        "auroc_diff_se": float(d_auc.std(ddof=1)), "auroc_mde80": float((Z_ALPHA + Z_POWER) * d_auc.std(ddof=1)),
        "delong_z": z, "delong_p": p_dl, "mcnemar_stat": stat, "mcnemar_p": p_mc,
    }


def compare_files(path_a, path_b, n_boot: int = 2000) -> dict:
    a, b = pd.read_csv(path_a), pd.read_csv(path_b)
    m = a.merge(b, on="sequence", suffixes=("_a", "_b"))
    assert len(m) == len(a) == len(b) and (m["y_true_a"] == m["y_true_b"]).all(), "prediction files not on identical samples"
    return compare_arrays(m["y_true_a"], m["y_prob_a"], m["y_prob_b"], m["y_pred_a"], m["y_pred_b"], n_boot)


def bh_adjust(p: np.ndarray) -> np.ndarray:
    """Benjamini-Hochberg adjusted p-values (monotone), NaN-safe."""
    p = np.asarray(p, float)
    out = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    pv = p[ok]
    n = len(pv)
    if n == 0:
        return out
    order = np.argsort(pv)
    ranked = pv[order] * n / (np.arange(n) + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    res = np.empty(n)
    res[order] = np.minimum(adj, 1.0)
    out[ok] = res
    return out


def cohens_dz(diffs: np.ndarray) -> float:
    d = np.asarray(diffs, float)
    return float(d.mean() / d.std(ddof=1)) if len(d) > 1 and d.std(ddof=1) > 0 else float("nan")
