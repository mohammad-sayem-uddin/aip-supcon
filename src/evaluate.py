"""Metrics, bootstrap CIs, DeLong and McNemar tests, threshold tuning, results tables."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import average_precision_score, roc_auc_score

from src.utils import ROOT

RESULTS = ROOT / "results"
PRED_DIR = RESULTS / "predictions"
METRIC_NAMES = ["accuracy", "sensitivity", "specificity", "precision", "f1", "mcc", "auroc", "auprc"]


def _confusion(y_true, y_pred):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    return tp, tn, fp, fn


def mcc_from_counts(tp, tn, fp, fn) -> float:
    den = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return float((tp * tn - fp * fn) / den) if den > 0 else 0.0


def compute_metrics(y_true, y_pred, y_prob) -> dict:
    """Accuracy, sensitivity, specificity, precision, F1, MCC, AUROC, AUPRC (degenerate cases -> 0 / NaN)."""
    y_true = np.asarray(y_true).astype(int)
    tp, tn, fp, fn = _confusion(y_true, y_pred)
    n = tp + tn + fp + fn
    sens = tp / (tp + fn) if (tp + fn) else 0.0
    spec = tn / (tn + fp) if (tn + fp) else 0.0
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    f1 = 2 * prec * sens / (prec + sens) if (prec + sens) else 0.0
    one_class = len(np.unique(y_true)) < 2
    return {
        "accuracy": (tp + tn) / n if n else float("nan"),
        "sensitivity": sens,
        "specificity": spec,
        "precision": prec,
        "f1": f1,
        "mcc": mcc_from_counts(tp, tn, fp, fn),
        "auroc": float("nan") if one_class else float(roc_auc_score(y_true, y_prob)),
        "auprc": float("nan") if one_class else float(average_precision_score(y_true, y_prob)),
    }


def find_optimal_threshold(y_true, y_prob, metric: str = "mcc") -> float:
    """Threshold maximising `metric` (MCC only) on the given (validation) data; ties -> closest to 0.5."""
    if metric != "mcc":
        raise ValueError("only mcc supported")
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.asarray(y_prob)
    grid = np.linspace(0.02, 0.98, 97)
    best, best_t = -2.0, 0.5
    for t in grid:
        m = mcc_from_counts(*_confusion(y_true, (y_prob >= t).astype(int)))
        if m > best + 1e-12 or (abs(m - best) <= 1e-12 and abs(t - 0.5) < abs(best_t - 0.5)):
            best, best_t = m, float(t)
    return best_t


def _stratified_indices(y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    return np.concatenate([rng.choice(pos, len(pos)), rng.choice(neg, len(neg))])


def bootstrap_ci(y_true, y_prob, metric_fn, n: int = 2000, alpha: float = 0.05, seed: int = 0):
    """Stratified bootstrap CI for metric_fn(y_true, y_prob)."""
    y = np.asarray(y_true).astype(int)
    p = np.asarray(y_prob)
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n):
        idx = _stratified_indices(y, rng)
        vals.append(metric_fn(y[idx], p[idx]))
    vals = np.asarray(vals, dtype=float)
    return float(np.nanquantile(vals, alpha / 2)), float(np.nanquantile(vals, 1 - alpha / 2))


def bootstrap_diff_ci(y_true, prob_a, prob_b, metric_fn, n: int = 2000, alpha: float = 0.05, seed: int = 0):
    """Paired stratified bootstrap CI for metric(a) - metric(b), plus the point estimate."""
    y = np.asarray(y_true).astype(int)
    pa, pb = np.asarray(prob_a), np.asarray(prob_b)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n):
        idx = _stratified_indices(y, rng)
        diffs.append(metric_fn(y[idx], pa[idx]) - metric_fn(y[idx], pb[idx]))
    diffs = np.asarray(diffs, dtype=float)
    point = metric_fn(y, pa) - metric_fn(y, pb)
    return float(point), float(np.nanquantile(diffs, alpha / 2)), float(np.nanquantile(diffs, 1 - alpha / 2))


def _midrank(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x)
    z = x[order]
    n = len(x)
    out = np.zeros(n)
    i = 0
    while i < n:
        j = i
        while j < n and z[j] == z[i]:
            j += 1
        out[i:j] = 0.5 * (i + j - 1)
        i = j
    res = np.empty(n)
    res[order] = out + 1
    return res


def delong_test(y_true, prob_a, prob_b) -> tuple[float, float]:
    """DeLong's test for two correlated ROC curves (midrank / structural-components covariance).

    Returns (z, two-sided p). Follows DeLong, DeLong & Clarke-Pearson (1988) and Sun & Xu (2014).
    """
    y = np.asarray(y_true).astype(int)
    scores = np.vstack([np.asarray(prob_a, float), np.asarray(prob_b, float)])
    pos, neg = scores[:, y == 1], scores[:, y == 0]
    m, n = pos.shape[1], neg.shape[1]
    tx = np.vstack([_midrank(pos[r]) for r in range(2)])
    ty = np.vstack([_midrank(neg[r]) for r in range(2)])
    tz = np.vstack([_midrank(np.concatenate([pos[r], neg[r]])) for r in range(2)])
    aucs = tz[:, :m].sum(axis=1) / (m * n) - (m + 1.0) / (2.0 * n)
    v01 = (tz[:, :m] - tx) / n
    v10 = 1.0 - (tz[:, m:] - ty) / m
    s = np.cov(v01) / m + np.cov(v10) / n
    var = s[0, 0] + s[1, 1] - 2 * s[0, 1]
    if var <= 1e-18:
        return 0.0, 1.0
    z = (aucs[0] - aucs[1]) / np.sqrt(var)
    return float(z), float(2 * stats.norm.sf(abs(z)))


def mcnemar_test(y_true, pred_a, pred_b) -> tuple[float, float]:
    """McNemar on paired correctness; exact binomial if discordant < 25, else chi-square (continuity-corrected)."""
    y = np.asarray(y_true).astype(int)
    ca = np.asarray(pred_a).astype(int) == y
    cb = np.asarray(pred_b).astype(int) == y
    b = int((ca & ~cb).sum())
    c = int((~ca & cb).sum())
    if b + c == 0:
        return 0.0, 1.0
    if b + c < 25:
        return float(min(b, c)), float(stats.binomtest(min(b, c), b + c, 0.5).pvalue)
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    return float(chi2), float(stats.chi2.sf(chi2, 1))


def build_results_table(results_csv: str | Path, groupby: list[str], metrics: list[str] = METRIC_NAMES) -> pd.DataFrame:
    """Aggregate to 'mean ± std' strings (4 dp) per group."""
    df = pd.read_csv(results_csv)
    rows = []
    for key, g in df.groupby(groupby, sort=False):
        key = key if isinstance(key, tuple) else (key,)
        row = dict(zip(groupby, key))
        row["n_runs"] = len(g)
        for m in metrics:
            if m in g:
                row[m] = f"{g[m].mean():.4f} ± {g[m].std(ddof=1):.4f}"
        rows.append(row)
    return pd.DataFrame(rows)


def load_predictions(model: str, test_set: str, regime: str) -> pd.DataFrame:
    return pd.read_csv(PRED_DIR / f"{model}_{test_set}_{regime}.csv")


def compare_models(model_a: str, model_b: str, test_set: str, regime: str = "B", n_boot: int = 2000) -> dict:
    """DeLong (AUROC), McNemar (accuracy at the stored y_pred) and paired bootstrap CIs, model_a minus model_b."""
    a = load_predictions(model_a, test_set, regime)
    b = load_predictions(model_b, test_set, regime)
    m = a.merge(b, on="sequence", suffixes=("_a", "_b"))
    assert len(m) == len(a) == len(b), "prediction files are not on identical sequences"
    assert (m["y_true_a"] == m["y_true_b"]).all()
    y = m["y_true_a"].to_numpy()
    pa, pb = m["y_prob_a"].to_numpy(), m["y_prob_b"].to_numpy()
    ya, yb = m["y_pred_a"].to_numpy(), m["y_pred_b"].to_numpy()
    z, p_delong = delong_test(y, pa, pb)
    stat, p_mcn = mcnemar_test(y, ya, yb)
    mcc_fn_a = lambda yt, yp: mcc_from_counts(*_confusion(yt, (yp >= 0.5).astype(int)))
    auc_fn = lambda yt, yp: float(roc_auc_score(yt, yp))
    # MCC difference at each model's own stored predictions (paired bootstrap on index)
    rng = np.random.default_rng(0)
    d_mcc = []
    for _ in range(n_boot):
        idx = _stratified_indices(y, rng)
        d_mcc.append(mcc_from_counts(*_confusion(y[idx], ya[idx])) - mcc_from_counts(*_confusion(y[idx], yb[idx])))
    mcc_point = mcc_from_counts(*_confusion(y, ya)) - mcc_from_counts(*_confusion(y, yb))
    auc_point, auc_lo, auc_hi = bootstrap_diff_ci(y, pa, pb, auc_fn, n=n_boot)
    return {
        "model_a": model_a, "model_b": model_b, "test_set": test_set, "regime": regime, "n": len(m),
        "auroc_a": auc_fn(y, pa), "auroc_b": auc_fn(y, pb),
        "auroc_diff": auc_point, "auroc_diff_lo": auc_lo, "auroc_diff_hi": auc_hi,
        "delong_z": z, "delong_p": p_delong,
        "mcc_a": mcc_from_counts(*_confusion(y, ya)), "mcc_b": mcc_from_counts(*_confusion(y, yb)),
        "mcc_diff": mcc_point,
        "mcc_diff_lo": float(np.quantile(d_mcc, 0.025)), "mcc_diff_hi": float(np.quantile(d_mcc, 0.975)),
        "mcnemar_stat": stat, "mcnemar_p": p_mcn,
        "acc_a": float((ya == y).mean()), "acc_b": float((yb == y).mean()),
    }
