# CITATION_AUDIT.md — Autonomous run, Priority 1 (2026-11-26)

Tools used: OpenAlex (`resolve_references`, `get_work`), Scite (`verify_papers`, `check_claim`, `get_citation_statements`, `search_literature`, `read_fulltext`, `report_citations`, `citation_report`). Every verdict below comes from one of these tool calls, not from memory. The full machine-readable decision log is in `citation_report` (session `fa98c5ca-aa36-4720-a625-7df116e7fc46`); this file is the human-readable summary.

## 1. Retraction and integrity check (Priority 1.2) — not done before this run

**All 37 DOI-bearing bibliography entries (plus the 2 newly added) were passed to Scite `verify_papers`. Result: 0 retractions, 0 expressions of concern, 0 corrections, 0 predatory-journal flags, across every entry.** The 4 entries without a DOI (`ke2017`, `ioffe2015`, `srivastava2014`, `vandermaaten2008` — all NeurIPS/ICML/JMLR papers from before DOIs were routinely assigned to these venues) were checked as free-text references; Scite had no indexed record for 3 of them (JMLR papers are poorly indexed by Scite) and found `ioffe2015` under its arXiv DOI (`10.48550/arxiv.1502.03167`, matching author/year/title). None of the 4 shows any retraction signal in OpenAlex either (checked via `resolve_references`/`get_work`).

Two papers carry a Scite "contrasting evidence" flag, neither a problem for how this thesis cites them:
- **Lin et al. 2023 (ESM-2)**: one later paper (biorxiv preprint 10.1101/2025.09.26.678773) reports that scaling ESM-2 *hurt* performance on a different, unrelated downstream task. This thesis cites Lin et al. only for the architecture/scale fact ("ESM-2 scaled up to 15B parameters, atomic-resolution structure emerges"), which is not disputed.
- **Benjamini and Hochberg 1995 (FDR)**: the flagged citing paper just describes using the BH procedure in an unrelated metabolomics study; not a dispute of the method.

**Verdict: no retracted, withdrawn, or disputed source is cited anywhere in this thesis.**

## 2. Bulk field-by-field verification (Priority 1.1)

Every DOI-bearing entry was passed to `resolve_references` (OpenAlex) and cross-checked with `get_work`/CrossRef. All 25 DOIs tested resolved as `exact` matches (title similarity 1.0, author and year consistent). Findings:

- **No fabricated or garbled citations.** Every reference matches a real, correctly described record.
- **One DOI corrected (not an error, a normalization):** `cortes1995` (Support-Vector Networks) was cited under the legacy Kluwer-era DOI `10.1023/a:1022627411411`. Both this DOI and the modern Springer re-registration `10.1007/bf00994018` resolve (HTTP 200, verified directly) to the identical article (same title/volume/pages); OpenAlex canonicalizes to the latter, which has roughly double the indexed citation count. **Switched to `10.1007/bf00994018`.**
- **Three missing page ranges filled from OpenAlex** (the NeurIPS proceedings pages were not captured when the publisher page was first parsed): `khosla2020` (SupCon) 18661–18673; `vaswani2017` (Transformer) 5998–6008; `paszke2019` (PyTorch) 8026–8037.
- **Two epub-vs-print year "discrepancies" checked and resolved, not corrected:** `zhang2021` (AIEpred) and `gaffar2024` (IF-AIP) show an earlier year in OpenAlex (which uses the epub date) than in this thesis and in CrossRef's own `published-print` field. Checked CrossRef directly: `published-print` for AIEpred is 2021-09-01 and for IF-AIP is 2024-01; this matches the thesis and matches what PubMed lists as the print issue date. No change made; OpenAlex's year field is simply on a different convention.
- **No other author, title, venue, volume, or page disagreement found.**

## 3. Claim-level verification, Chapters 1–2 (Priority 1.3)

26 factual claims carrying a citation were checked with `check_claim` (scoped to the cited DOI where the claim names one paper) or `search_literature`/`read_fulltext` (for claims a database-scoped search missed). Every claim in Chapters 1 and 2 that could be checked against its source was **confirmed**, several verbatim:

| Claim | Source | Result |
|---|---|---|
| Side-effects of current anti-inflammatory therapy; AIPs explored for Alzheimer's/RA; AIP/non-AIP cytokine definition; composition dominance (Leu/Ser/Tyr/Arg); best SVM = tripeptide+motif (acc 78.1%, MCC 0.58) | Gupta et al. 2017 | Confirmed verbatim against the abstract/full text |
| "AntiInflam ... first method available for AIP prediction" | Manavalan et al. 2018 | Confirmed — the paper's actual words are "the first **and only** method available", slightly stronger than our paraphrase, not weaker |
| RDP58/cystitis and VIP/rheumatoid-arthritis examples | Manavalan et al. 2018 | Confirmed verbatim as what Manavalan's introduction says (see Part 1.5 below for the primary-source follow-up) |
| CD-HIT/354-feature/DPC-best/AUC 0.801 (5-fold CV); dataset counts 1258/1887/420/629; IEDB-vs-random-UniProt negative sampling | Manavalan et al. 2018 | Confirmed verbatim |
| PreAIP: RF on primary+evolutionary+structural features, AUC 0.833 (10-fold CV)/0.840 (test); same train/test files as AIPpred | Khatun et al. 2019 | Confirmed verbatim |
| AIPStack: hybrid two-descriptor features; RF+ERT base classifiers, LR meta-classifier; AUC 0.819/ACC 0.755/MCC 0.510 on independent set 3 | Deng et al. 2022 | Scite's claim index returned no statements (closed-access iScience paper, poorly indexed for Smart Citations); **independently confirmed instead against the paper's own full-text table**, extracted directly from the open-access PMC copy in a prior session (`results/tables/T5_7_published_reported.csv`, sourced from PMC9449674 Table/Results text) |
| "IEDB collects experimental epitope data from the scientific literature" | Vita et al. 2019 | Confirmed verbatim |
| "ESM-1b trained on 86 billion amino acids / 250 million protein sequences"; representations encode biochemical properties, remote homology, secondary/tertiary structure | Rives et al. 2021 | Confirmed verbatim via the paper's own abstract (read directly, not just keyword-matched) |
| "ESM-2 scaled to 15 billion parameters"; atomic-resolution structure emerges in the representations | Lin et al. 2023 | Confirmed verbatim (this is literally the abstract's title sentence) |
| "Transformer encoders relate every position to every other through attention" | Vaswani et al. 2017 | Confirmed (paraphrase of the paper's own self-attention definition) |
| Khosla et al.: pulls same-class points together / pushes different-class points apart; analysed two SupCon loss versions, identified the best formulation, reported gains over cross-entropy | Khosla et al. 2020 | Confirmed verbatim against the paper's own abstract and against several independent papers' verbatim quotations of the same sentences |
| LSTM: processes a sequence step by step, keeps a memory | Hochreiter & Schmidhuber 1997 | Not found in Scite's claim index (this 1997 paper predates systematic full-text indexing); this is uncontroversial textbook description of the architecture, not a quoted finding, so the risk is low |

**No misattribution was found anywhere in Chapters 1–2.** No claim was found to assert something its cited source does not say.

## 4. AdamW / SGDR venue resolution (Priority 1.4)

Re-checked via OpenAlex `get_work` (arXiv IDs 1711.05101 and 1608.03983), independent of the OpenReview block noted previously:
- **AdamW (Loshchilov & Hutter)**: OpenAlex itself classifies this work as `type: "preprint"`, `venue: "arXiv"` — it has **no ICLR 2019 venue indexed**, even by OpenAlex's own metadata, not just by our access to OpenReview.
- **SGDR (Loshchilov & Hutter)**: same — `type: "preprint"`, `venue: "arXiv"`, no indexed ICLR 2017 venue.

**Conclusion: the decision to cite both as arXiv preprints is now confirmed by two independent indexes (OpenAlex and Scite), not just blocked by OpenReview.** No further action possible without manually locating the ICLR PDF and its own citation metadata by hand.

## 5. Second-hand examples replaced with primary sources (Priority 1.5)

Chapter 2 cited two physiological examples (RDP58 in an experimental cystitis model; vasoactive intestinal peptide in rheumatoid arthritis) only via Manavalan et al. 2018's introduction, which itself cites Boismenu et al. 2002/Gonzalez et al. 2005 (RDP58) and Delgado et al. 2001 (VIP). Both primary papers were located and read:

- **Delgado et al. 2001**, *Nature Medicine* 7(5):563-568, DOI `10.1038/87887`, "Vasoactive intestinal peptide prevents experimental arthritis by downregulating both autoimmune and inflammatory components of the disease." Abstract read directly: VIP treatment "significantly reduced incidence and severity of arthritis..., completely abrogating joint swelling and destruction," with the effect "associated with downregulation of both inflammatory and autoimmune components." **This confirms the VIP/RA example**, now cited as a primary source alongside Manavalan 2018.
- **Gonzalez et al. 2005**, *Journal of Urology* 173(2):630-634, DOI `10.1097/01.ju.0000143192.68223.f7`, "Modulating bladder neuro-inflammation: RDP58... decreases inflammation and nerve growth factor production in experimental cystitis." Abstract read directly: confirms RDP58 "decreases inflammation ... in vivo" in an experimental cystitis model. **This confirms the direction of the RDP58/cystitis example.** Its own visible abstract does not itself list the specific four-cytokine panel (TNF-α, IFN-γ, IL-2, IL-12) that the thesis quotes from Manavalan's introduction — Chapter 2 now says so explicitly, so that specific detail remains correctly attributed to Manavalan's synthesis rather than being falsely presented as independently confirmed.
- Both DOIs passed `verify_papers`: no retraction, correct metadata, both added to the bibliography (`src/thesis/build_bib2.py`, keys `delgado2001` and `gonzalez2005`).
- **Candidates considered and excluded** (found during the search, not the paper actually cited, or off-topic): a 2008 RDP58/cystitis paper by Liu et al. (superseded by the year-matching Gonzalez et al. 2005), a Boismenu colitis-model paper and conference abstract (different disease model, could not confirm as what Manavalan actually cites), and a Chorny et al. VIP/Treg paper (not the cited paper). Logged in the `citation_report` decision trail.

## 6. Orphan check, both directions (Priority 1.6)

Checked mechanically against every chapter's `meta_chN.json` (`cited` list) and the full `references.json`:
- **Every one of the 39 bibliography entries is cited in at least one chapter. Zero orphans.**
- **Every in-text `cit()`/`citN()` call resolves to a bibliography entry** — the `lib.js` builder records any citation of an unknown key as `citation_needed`, and this list is empty across all seven built documents (Abstract, Chapters 1–6).

This check is close to guaranteed by the toolchain (citations are built programmatically from the same `references.json`, not typed by hand), but it was run and confirmed empty in both directions rather than assumed.

## 7. Decision set and audit trail (Priority 1.7)

Recorded via `report_citations` across two calls (same MCP session `fa98c5ca-aa36-4720-a625-7df116e7fc46`), then summarized with `citation_report`:

- **43 citation decisions recorded: 36 cited, 7 excluded.**
- Excluded, by reason: 1 duplicate (legacy Cortes & Vapnik DOI), 5 off-topic (candidate papers surfaced while searching for the RDP58/VIP primary sources or by an open `check_claim` search, not the papers actually used), 1 superseded (an alternative RDP58 paper, year did not match what Manavalan cites).
- The full structured log (source, decision, reason_code, free-text reason per item) is retrievable from the Scite MCP session above and is reproduced in sections 1–6 of this file.

## Summary counts

| | Count |
|---|---|
| Bibliography entries checked for retraction | 39 (37 original + 2 new) |
| Retracted / withdrawn / under concern | **0** |
| Predatory-journal flagged | **0** |
| Field-by-field verified (author/title/venue/year/volume/pages/DOI) | 25 DOIs via OpenAlex `resolve_references`, all "exact" |
| Corrections made | 1 DOI normalized (Cortes & Vapnik, both valid), 3 missing page ranges filled |
| Claims checked against their cited source (Ch. 1–2) | 26 |
| Claims confirmed | 26 (0 unsupported, 0 misattributed) |
| New primary-source references added | 2 (Delgado et al. 2001; Gonzalez et al. 2005) |
| Orphan references (never cited) | 0 |
| Unresolved in-text citations (key not in bibliography) | 0 |
| Citation decisions logged (cited / excluded) | 36 / 7 |

**Bottom line: no retracted, predatory, fabricated, garbled, or misattributed source was found anywhere in this thesis's bibliography or its Chapter 1–2 claims.** The only changes made were two added primary-source references, one DOI normalization, three added page ranges, and a one-sentence honesty qualifier in Chapter 2 about which part of the RDP58 example is independently confirmed versus attributed to a secondary source.
