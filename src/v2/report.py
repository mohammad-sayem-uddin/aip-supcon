"""Rebuild HANDOFF_REPORT.md for the v1 + v2 study (9 sections + the plan's deliverables table). Safe to run at any time."""
from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd

from src import report as v1
from src.utils import ROOT
from src.v2.common import R, TABLES, V2

STAGES_V2 = [
    ("A", "Phase A: provenance, overlap verification (gate), cross-benchmark audit"),
    ("E1", "E1: PREREGISTRATION.md committed before modelling"),
    ("V2_embed_esm2_t6_8M", "Residue-level embeddings 8M"),
    ("V2_embed_esm2_t33_650M", "Residue-level embeddings 650M"),
    ("B_cv", "Phase B: 5 architectures x 6 lambdas x 5 seeds x 5 folds (CV)"),
    ("B_final", "Phase B: final models, Regimes A/B/C"),
    ("C1_pooling", "C1: pooling ablation on frozen 650M"),
    ("C1_attention", "C1: attention pooling at 650M"),
    ("C2_fusion", "C2: feature fusion (RF, LightGBM, MLP)"),
    ("C3_finetune", "C3: fine-tune 8M vs frozen control"),
    ("D_cross", "D1-D2: cross-benchmark generalisation"),
    ("E5_nested", "E5: nested CV for the headline comparison"),
    ("E_stats", "E2-E4, E6: BH correction, MDE, seed-vs-sample variance"),
    ("F_analysis", "Phase F: why AAC wins, motifs, errors, length"),
    ("V2_tables", "v2 tables and figures"),
]
DELIVERABLES = [
    ("LEAKAGE_FINDING.md", "The Phase A result, stated precisely"), ("PREREGISTRATION.md", "Primary hypothesis, committed before Phase B"),
    ("POWER_ANALYSIS.md", "Detectable effect size at each n"), ("results/tables/T3.5_cross_benchmark_leakage.csv", "T3.5 cross-benchmark leakage matrix"),
    ("results/tables/T5.8_architecture_comparison.csv", "T5.8 architecture comparison"), ("results/tables/T5.9_representation_comparison.csv", "T5.9 representation comparison"),
    ("results/tables/T5.10_cross_benchmark.csv", "T5.10 cross-benchmark generalisation"), ("results/tables/T5.11_corrected_significance.csv", "T5.11 FDR-corrected significance"),
    ("figures/fig5_8_architecture_lambda.png", "F5.8 architectures x lambda"), ("figures/fig5_9_pooling_ablation.png", "F5.9 pooling ablation"),
    ("figures/fig5_10_cross_benchmark_heatmap.png", "F5.10 generalisation heatmap"), ("figures/figF1_negative_resemblance.png", "F5.11/F analysis figures (several)"),
    ("INTERPRETATION_v2.md", "Honest reading of everything"), ("HANDOFF_REPORT.md", "This report, rebuilt after every stage"),
    ("results/provenance.csv", "A1 provenance"), ("results/overlap_sequences.csv", "A2 every overlapping sequence with labels"),
]


def md(df):
    return v1.md(df)


def stage_v2() -> str:
    rows = []
    for k, desc in STAGES_V2:
        f = R / ".stages" / f"{k}.json"
        if k == "E1":
            ok = (ROOT / "PREREG_COMMIT.txt").exists()
            rows.append({"Stage": k, "What": desc, "Status": "complete" if ok else "skipped", "Compute wall-clock": "-",
                         "Notes": (ROOT / "PREREG_COMMIT.txt").read_text().strip()[:140] if ok else ""})
            continue
        if f.exists():
            d = json.loads(f.read_text())
            rows.append({"Stage": k, "What": desc, "Status": d["status"], "Compute wall-clock": v1._fmt_secs(d["wall_seconds"]) if d["wall_seconds"] else "n/a (sliced/remote; see notes)", "Notes": d.get("notes", "")})
        else:
            rows.append({"Stage": k, "What": desc, "Status": "skipped", "Compute wall-clock": "-", "Notes": "not reached or not run"})
    return md(pd.DataFrame(rows))


def deliverables() -> str:
    return md(pd.DataFrame([{"Deliverable": p, "Contents": d, "Present": (ROOT / p).exists()} for p, d in DELIVERABLES]))


def section_headline_v2() -> str:
    out = ["**Primary hypothesis H1 (preregistered; outcome known from v1, see PREREGISTRATION.md section 0):** "
           "not supported. v1 numbers and the full v1 results are kept in the original sections below.\n"]
    f = TABLES / "T5.11_corrected_significance.csv"
    if f.exists():
        t = pd.read_csv(f)
        b = t[(t.regime == "B")]
        h1 = b[b.family == "H1 primary (v1)"]
        if len(h1):
            out.append("**H1, Regime B (recomputed with the v2 comparison code):**\n\n" + md(h1[["test_set", "n", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi", "auroc_diff", "delong_p", "mcnemar_p", "mcc_mde80", "auroc_mde80"]].round(4)))
        h2 = b[b.family == "H2 architectures (Regime B)"]
        if len(h2):
            out.append("**H2: lambda* vs lambda=0 for each architecture (Regime B; raw and BH-adjusted p side by side):**\n\n" +
                       md(h2[["comparison", "test_set", "n", "mcc_diff", "mcc_diff_lo", "mcc_diff_hi", "delong_p", "p_delong_bh_family", "mcnemar_p", "p_mcnemar_bh_family", "supports_claim_rule"]].round(4)))
            k = int(h2["supports_claim_rule"].sum())
            out.append(f"Comparisons meeting the preregistered support rule (BH-adjusted DeLong p < 0.05 and MCC-difference CI above 0): **{k} of {len(h2)}**.\n")
    out.append("Full reading: [INTERPRETATION_v2.md](INTERPRETATION_v2.md). v1 reading: [INTERPRETATION.md](INTERPRETATION.md).\n")
    return "\n".join(out)


def build() -> str:
    leak = (ROOT / "LEAKAGE_FINDING.md").read_text() if (ROOT / "LEAKAGE_FINDING.md").exists() else "_Phase A has not run._"
    gate = json.loads((V2 / "phaseA_summary.json").read_text()) if (V2 / "phaseA_summary.json").exists() else {}
    a_line = ("**Phase A gate: PASSED** (overlap reproduces: 211 and 298). " if gate.get("overlap_reproduces_211_298") else "**Phase A gate: NOT PASSED.** ") + \
        "Details: [LEAKAGE_FINDING.md](LEAKAGE_FINDING.md).\n"
    blockers = "\n".join(p.read_text().split("\n", 1)[1] for p in (ROOT / "BLOCKERS_v2.md", ROOT / "BLOCKERS.md") if p.exists())
    decisions = "\n".join(p.read_text().split("\n", 1)[1] for p in (ROOT / "DECISIONS_v2.md", ROOT / "DECISIONS.md") if p.exists())
    files = [{"File": str(p.relative_to(ROOT)), "Rows": len(pd.read_csv(p)) if p.suffix == ".csv" else "-"}
             for p in sorted(list(R.glob("v2/*.csv")) + list(TABLES.glob("T5.8*.csv")) + list(TABLES.glob("T5.9*.csv")) + list(TABLES.glob("T5.1[01]*.csv"))
                             + list(TABLES.glob("T3.5*.csv")) + list(TABLES.glob("TF*.csv")))]
    figs = sorted(p.name for p in (ROOT / "figures").glob("*.png"))
    nxt = (R / "report_notes" / "next_actions_v2.md").read_text() if (R / "report_notes" / "next_actions_v2.md").exists() else "_To be written at the end of the run._\n"
    parts = [
        f"# HANDOFF REPORT (v1 + v2 extension)\n\n_Generated {datetime.now().isoformat(timespec='seconds')} by `python -m src.v2.report`; rebuilt after every stage._\n",
        "## Deliverables (EXECUTION_PLAN_v2.md)\n\n" + deliverables(),
        "## 1. STATUS\n\n**v2 extension phases**\n\n" + stage_v2() + "\n**v1 stages S1-S12 (complete; not re-run)**\n\n" + v1.section_status(),
        "## 2. S1 / PHASE A VERIFICATION\n\n" + a_line + "\n**S1 hard gate (v1):**\n\n" + v1.section_s1(),
        "## 3. HEADLINE RESULT\n\n" + section_headline_v2() + "\n**v1 detail:**\n\n" + v1.section_headline(),
        "## 4. LEAKAGE IMPACT\n\n" + v1.section_leakage(),
        "## 5. FULL RESULTS\n\n" + md(pd.DataFrame(files)) + "\nv1 files:\n\n" + v1.section_files(),
        "## 6. FIGURES\n\n" + ", ".join(figs) + "\n\nv1 figure status:\n\n" + v1.section_figures(),
        "## 7. BLOCKERS\n\n" + blockers,
        "## 8. DECISIONS\n\n" + decisions,
        "## 9. NEXT ACTIONS\n\n" + nxt,
        "## Appendix: LEAKAGE_FINDING.md (verbatim)\n\n" + leak,
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    (ROOT / "HANDOFF_REPORT.md").write_text(build())
    print("wrote HANDOFF_REPORT.md")
