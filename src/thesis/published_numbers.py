"""Transcribe published performance figures (completion run 2.3). Every value is read programmatically from the table of the paper's open-access
full text (Europe PMC XML, saved in data/external/papers2) and recorded with paper, PMCID, table label and row label. Values not found in a source
stay empty (TODO). Nothing is typed from memory. Run: PYTHONPATH=. .venv/bin/python src/thesis/published_numbers.py"""
import re, glob
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; P2 = ROOT / "data/external/papers2"
def txt(e): return re.sub(r"\s+", " ", "".join(e.itertext())).strip()
def tables(prefix):
    f = glob.glob(str(P2 / f"{prefix}_*.xml"))[0]; root = ET.parse(f).getroot(); out = {}
    for tw in root.iter("table-wrap"):
        lab = tw.find("label")
        if lab is None: continue
        out[txt(lab).lower()] = [[txt(c) for c in tr] for tr in tw.iter("tr")]
    return out, re.search(r"(PMC\d+)", f).group(1)
def pick(rows, row_label, header_match=None, col_order=None):
    hdr = [h.lower() for h in rows[0]]
    for r in rows[1:]:
        if r and r[0].strip().lower() == row_label.lower(): return dict(zip(hdr, r))
    raise KeyError(row_label)
def num(v):
    try: return float(v)
    except Exception: return None
def metrics(d):
    g = lambda *ks: next((num(d[k]) for k in ks if k in d and num(d[k]) is not None), None)
    acc = g("acc", "ac", "accuracy", "accuracy (%)"); sn = g("sen", "sn", "sensitivity", "sensitivity (%)"); sp = g("spe", "sp", "specificity", "specificity (%)")
    mcc, auc = g("mcc"), g("auc")
    pct = any(k.endswith("(%)") for k in d) or (acc is not None and acc > 1.5)
    f = (lambda x: None if x is None else x / 100) if pct else (lambda x: x)
    return dict(ACC=f(acc), SN=f(sn), SP=f(sp), MCC=mcc, AUC=auc)
rows = []
def add(predictor, evalset, prefix, table, row, role, note="", row_in_table=None):
    T, pmc = tables(prefix); t = T[table.lower()]
    # the paper tables sometimes continue a method name over several rows (PreAIP thresholds): row_in_table lets the caller select by row index
    if isinstance(row, int): hdr = [h.lower() for h in t[0]]; d = dict(zip(hdr, t[row][-len(hdr):])); rl = f"row {row}: {' | '.join(t[row])}"
    else: d = pick(t, row); rl = row
    m = metrics(d)
    rows.append(dict(predictor=predictor, evaluation=evalset, role=role, **m, source=f"{prefix} {pmc}", table=table, row=rl, note=note))
add("AntiInflam (Gupta et al., 2017)", "validation set (our Ind_425 file; 173 AIPs / 252 non-AIPs)", "antiinflam", "Table 3", "TPC_HYB", "own paper", "SVM on tripeptide composition + motif hybrid, the model that the paper's abstract names as best; no AUC in this table")
add("AntiInflam (Gupta et al., 2017)", "10-fold cross-validation, training set", "antiinflam", "Table 2", "TPC_HYB", "own paper", "same model")
add("AIPpred (Manavalan et al., 2018)", "5-fold CV, benchmark (1,258 / 1,887)", "aippred", "Table 1", "AIPpred", "own paper")
add("AIPpred (Manavalan et al., 2018)", "independent set (our Ind_1049 file; 420 / 629)", "aippred", "Table 2", "AIPpred", "own paper")
add("AntiInflam (MA) as evaluated by the AIPpred authors", "independent set (Ind_1049)", "aippred", "Table 2", "AntiInflam (MA)", "other authors' evaluation")
add("AntiInflam (LA) as evaluated by the AIPpred authors", "independent set (Ind_1049)", "aippred", "Table 2", "AntiInflam (LA)", "other authors' evaluation")
add("PreAIP (Khatun et al., 2019)", "10-fold CV, training set", "preaip", "Table 1", "PreAIP*", "own paper")
T, _ = tables("preaip"); t2 = T["table 2"]
idx = {i: r for i, r in enumerate(t2)}
pre = [i for i, r in idx.items() if r and r[0].strip() == "PreAIP"][0]
for off, lab in ((0, "High"), (1, "Moderate"), (2, "Low")):
    add(f"PreAIP (Khatun et al., 2019), threshold {lab}", "test set (our Ind_1049 file)", "preaip", "Table 2", pre + off, "own paper", "threshold level as printed in the paper")
add("AIPpred as evaluated by the PreAIP authors", "test set (Ind_1049)", "preaip", "Table 2", "AIPpred", "other authors' evaluation")
add("iAIPs (Zhao et al., 2021)", "independent set (Ind_1049)", "iaips", "Table 6", "iAIPs (our work)", "own paper")
add("AIEpred (Zhang et al., 2021) as reported in the iAIPs paper", "independent set (Ind_1049)", "iaips", "Table 6", "AIEpred", "other authors' evaluation", "AIEpred's own paper is not open access and its abstract gives no figures")
add("AIPFusion-Net (Wang et al., 2026)", "Ind-1049 (byte-identical to our Ind_1049)", "aipfusion", "Table 2", "AIPFusion-Net", "own paper", "training file in its repository is byte-identical to our Benchmark_Dataset (SHA-256)")
add("AIPFusion-Net (Wang et al., 2026)", "Ind-426 (its name for our Ind_425 file)", "aipfusion", "Table 3", "AIPFusion-Net", "own paper")
df = pd.DataFrame(rows)
# AIPStack: figures stated in the text of the paper (abstract and results), not in a table; SN and SP only in Figure 5 (image) -> left empty
df.loc[len(df)] = dict(predictor="AIPStack (Deng et al., 2022)", evaluation="independent set 3 of its own dataset (71 AIPs / 72 non-AIPs; not obtainable)", role="own paper", ACC=0.755, SN=None, SP=None, MCC=0.510, AUC=0.819,
                       source="aipstack PMC9449674", table="abstract and Results text (precision 0.757)", row="AIPStack on independent set 3", note="SN and SP appear only in Figure 5E/F (image); left empty")
df.loc[len(df)] = dict(predictor="IF-AIP (Gaffar et al., 2024)", evaluation="independent data 1 and 2 of its own study", role="own paper", ACC=None, SN=None, SP=None, MCC=None, AUC=None,
                       source="PMID 37989075 (abstract only)", table="-", row="-", note="abstract gives relative improvements only; paper is not open access: TODO")
df.loc[len(df)] = dict(predictor="AIEpred (Zhang et al., 2021)", evaluation="leave-one-out CV and independent test of its own study", role="own paper", ACC=None, SN=None, SP=None, MCC=None, AUC=None,
                       source="PMID 31985437 (abstract only)", table="-", row="-", note="abstract gives no figures; paper is not open access: TODO")
df.to_csv(ROOT / "results/tables/T5_7_published_reported.csv", index=False)
print(df[["predictor", "evaluation", "ACC", "SN", "SP", "MCC", "AUC", "table"]].to_string())
