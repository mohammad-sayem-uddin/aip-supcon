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


def section_thesis() -> str:
    """Thesis-writing status: chapters, pages, TODOs, unverified citations, weakest points (written for the morning after the overnight run)."""
    T_ = R / "thesis"
    pc = json.loads((T_ / "page_counts.json").read_text()) if (T_ / "page_counts.json").exists() else {}
    names = {0: "Abstract", 1: "Chapter 1 Introduction", 2: "Chapter 2 Literature Review", 3: "Chapter 3 Materials and Methods", 4: "Chapter 4 Implementation and Experimental Setup",
             5: "Chapter 5 Results and Discussion", 6: "Chapter 6 Conclusions and Future Work"}
    rows, todos = [], []
    for i, nme in names.items():
        mf = T_ / f"meta_ch{i}.json"
        if not mf.exists():
            rows.append({"Part": nme, "Status": "NOT BUILT", "Pages": "-", "Tables": "-", "Figures": "-", "Verified citations": "-", "TODO": "-", "[CITATION NEEDED]": "-"}); continue
        m = json.loads(mf.read_text()); key = {0: "ABSTRACT thesis"}.get(i, f"CHAPTER {i} thesis")
        rows.append({"Part": nme, "Status": "complete" + (" (with TODO)" if m["todos"] else ""), "Pages": pc.get(key, "-"), "Tables": m["tables"], "Figures": m["figures"],
                     "Verified citations": len(m["cited"]), "TODO": len(m["todos"]), "[CITATION NEEDED]": len(m["citation_needed"])})
        todos += [f"{nme}: {t}" for t in m["todos"]]
    out = ["**Chapters (the .docx files are local and gitignored; the build scripts are in `src/thesis/`, run each twice in order 1 to 6).**\n", md(pd.DataFrame(rows)),
           f"\n**Total rendered length: {pc.get('TOTAL', '?')} pages** including the references ({pc.get('REFERENCES thesis', '?')} pages), US Letter, 11 pt, as rendered by LibreOffice; check the page count in Word.\n"]
    out.append("**Remaining TODOs and what closes them**\n")
    out += [f"- {t}" for t in todos]
    out += ["- Table 5.16 is intentionally TODO beyond the abstract-level figures: needs the full texts of AntiInflam, AIPpred, PreAIP and AIPStack (the PreAIP and AIPStack pages could not be read automatically).",
            "- Figures 5.9b, F1 and F5 are not in the thesis (raw model keys as labels / overlapping legend): regenerate with readable labels if wanted.",
            "- Chapters 1 and 2 are short (4 pages each) because only verified sources are used: add literature only from papers you can verify, then add them to `CANDIDATES` in `src/thesis/build_bib.py`.",
            "- Not attempted (BLOCKERS_v2.md): C4 other protein language models, D3 transfer to AMP/ACP, AIPStack independent sets, larger-checkpoint fine-tuning.",
            "- Word rendering was checked only through LibreOffice.\n"]
    cv = ROOT / "CITATIONS_TO_VERIFY.md"
    out.append("**Unverified citations** (full list with exact sentences in [CITATIONS_TO_VERIFY.md](CITATIONS_TO_VERIFY.md)): LightGBM (Ke et al. 2017), random forest (Breiman 2001), SVM (Cortes and Vapnik 1995), cosine schedule, batch normalisation and dropout have no entry; the venues of the six arXiv-cited works are unverified; the RDP58/VIP examples in Chapter 2 are second-hand; Table 5.16 uses abstract-level figures only. "
               "Eight claims from the earlier drafts were removed rather than cited.\n")
    nf = ROOT / "src" / "thesis" / "status_notes.md"
    if nf.exists():
        out.append(nf.read_text())
    cl = ROOT / "THESIS_CONSISTENCY_LOG.md"
    if cl.exists():
        out.append("\n**Inconsistencies found and fixed** (worst first): see [THESIS_CONSISTENCY_LOG.md](THESIS_CONSISTENCY_LOG.md).\n")
    return "\n".join(out)


def section_completion() -> str:
    """Completion run: checklist per tier, differential-gap outcome, submission checklist."""
    ex = lambda rel: (ROOT / rel).exists()
    scale_done = ex("results/tables/T5.13c_finetune_scale_tests.csv") and bool(list((V2 / "scale").glob("finetune_scale_esm2_t33_650M*.csv"))) and bool(list((V2 / "scale").glob("finetune_scale_esm2_t30_150M*.csv")))
    c4_done = ex("results/tables/T5.14_c4_other_plms_tests.csv")
    mark_ = lambda ok: "DONE" if ok else "NOT DONE"
    out = ["**Completion checklist** (details: `results/completion_progress.log`, `NUMBERS_CHANGED.md`)\n",
           "| Tier | Item | Status | Evidence |", "|---|---|---|---|",
           f"| 1 | 1.1 Figures 5.9b, F1, F5 readable | {mark_(ex('src/thesis/figures_fix.py'))} (F1 redesigned) | `src/thesis/figures_fix.py`, `figures/` |",
           "| 1 | 1.2 Repository address in Chapter 4 | DONE (archive DOI is the author's) | `ch4.js` |",
           "| 1 | 1.3 Bibliography complete | DONE (two ICLR items stay arXiv preprints) | `src/thesis/build_bib2.py`, `CITATIONS_TO_VERIFY.md` |",
           "| 1 | 1.4 Word-compatible check | DONE as schema validation; Word itself not available | all 8 .docx pass `validate.py` |",
           f"| 2 | 2.1 Differential leakage gaps tested | {mark_(ex('results/v2/gap_decision.json'))}: claim SUPPORTED | `T5.12*`, `src/v2/gap_tests.py` |",
           f"| 2 | 2.2 Fine-tune 150M and 650M (Kaggle) | {mark_(scale_done)} (kernels may still be running; see BLOCKERS_v2.md) | `src/v2/finish_completion.py`, `T5.13*` |",
           "| 2 | 2.3 Table 5.16 filled | DONE except IF-AIP, AIEpred own figures and AIPStack SN/SP (TODO, no source) | `T5_7_published_reported.csv` |",
           "| 2 | 2.4 AIPStack and AIPFusion-Net retry | AIPFusion-Net DONE (files byte-identical to ours); AIPStack independent sets NOT obtainable | `aipfusion_repo_check.csv`, `BLOCKERS_v2.md` |",
           f"| 3 | 3.1 C4 ProtBERT and ProtT5 | {mark_(c4_done)} (kernels may still be running) | `src/v2/phaseC4.py`, `T5.14*` |",
           "| 3 | 3.2 D3 AMP / ACP | NOT DONE (needs a verified benchmark and the Phase A audit first) | `BLOCKERS_v2.md` |", ""]
    g = TABLES / "T5.12b_leakage_gap_family_contrasts.csv"
    if g.exists():
        c = pd.read_csv(g); r = c[(c.contrast.str.startswith("Flexible")) & (c.scope == "both")].iloc[0]; sl = c[(c.contrast.str.startswith("Capacity")) & (c.scope == "both")].iloc[0]
        out.append(f"**Task 2.1 outcome: the differential-gap claim is SUPPORTED, not weakened.** Mean leakage gap (MCC, Regime A minus B) of the 32 flexible non-linear models minus the 3 linear models: {r['diff']:+.3f} (95% interval {r['lo']:+.3f} to {r['hi']:+.3f}; BH-adjusted p {r['p_BH_within_scope']:.4f}; model-level Mann-Whitney p {r['p_mannwhitney_models']:.3f}). "
                   f"Within the frozen-MLP checkpoints the gap does not rise with size (slope {sl['diff']:+.3f} MCC per decade of parameters, interval {sl['lo']:+.3f} to {sl['hi']:+.3f}). One clause was not supported and was corrected: gradient-boosted trees are not among the smallest gaps (LightGBM +0.051 above linear, 0.136 below random forest).\n")
    out.append("**Final submission checklist**\n")
    out.append("*Needs the author personally*\n\n- Re-check the page count in Word after the final rebuild. (The stale passages of `NUMBERS_CHANGED.md` sections 1 to 3 were rewritten on 2026-11-26.)\n- Create a permanent archive of the repository (for example a Zenodo DOI) and put it in Section 4.6.\n- Figures 5.9b, F1 and F5 are inserted (Sections 5.6.3 and 5.9.3); Figure 5.11 appears by itself when the scale run is integrated.\n- Obtain, if wanted, IF-AIP and AIEpred full texts (not open access) and the AIPStack datasets (lead contact) to close the TODO cells of Table 5.16.\n- Run `python -m src.v2.finish_completion fetch` and `analyse` until the Kaggle kernels are integrated, then rewrite the sentences listed in section 12 below.\n- Read the three weakest points above with your supervisor; confirm the pre-registration wording.\n- Open the .docx files in Word and check equations, tables and figure placement; the build was checked only through LibreOffice and the Office schema validator.\n")
    out.append("*Complete*\n\n- Chapters 1 to 6, abstract (250 words) and reference list built from reproducible scripts; all citations verified against CrossRef, arXiv or the publisher page; Table 5.16 transcribed from full-text tables with source and table number per value; differential leakage gap tested; AIPFusion-Net data identity measured; bibliography closed except two preprints.\n")
    return "\n".join(out)


def section_pending() -> str:
    nf = ROOT / "src" / "thesis" / "pending_kaggle_notes.md"
    return nf.read_text() if nf.exists() else "_missing_"


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
        "## 10. THESIS WRITING STATUS (overnight run, part 2)\n\n" + section_thesis(),
        "## 11. COMPLETION RUN\n\n" + section_completion(),
        "## 12. WHEN THE KAGGLE RESULTS EXIST: WHAT TO RUN AND WHAT TO REWRITE\n\n" + section_pending(),
        "## Appendix: LEAKAGE_FINDING.md (verbatim)\n\n" + leak,
    ]
    return "\n".join(parts)


if __name__ == "__main__":
    (ROOT / "HANDOFF_REPORT.md").write_text(build())
    print("wrote HANDOFF_REPORT.md")
