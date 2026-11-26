# PROOFREAD_REPORT

Full read-through of all six chapters (plus Abstract and References), autonomous run Priority 4.3, 2026-11-26. Per the instruction for this task, substantive arguments and conclusions were not silently rewritten; everything changed below is either a grammar/formatting bug or a factual update made necessary by new data that arrived during this same run (Priority 4.2's Kaggle fetch), and each is logged here and in `DECISIONS_v2.md` (V2-D23).

## Method

- Automated checks across the rendered text of all eight `.docx` files: unresolved cross-references (`??`), stray `[CITATION NEEDED]`/`[TODO]` markers, duplicate consecutive words, `undefined`/`NaN` artifacts.
- Cross-chapter numerical consistency checks (the same figure quoted in the Abstract, Chapter 1, Chapter 5 and Chapter 6, e.g. the leakage-inflation range, the nested cross-validation estimate) — all matched to three decimal places or were explicitly rounded versions of the more precise figure.
- Full read of Chapters 1, 2, 4 and 6 in rendered plain text; a targeted read of Chapter 3's narrative paragraphs (Sections 3.1, 3.5, 3.7-3.9) and of Chapter 5's new Table 5.17/5.18 and its surrounding prose; the remainder of Chapter 5's dense result tables were spot-checked rather than read line by line, since they are machine-generated from `results/v2/*.csv` and the automated consistency checks cover them.

## Bugs found and fixed

1. **Grammar: missing parentheses around a citation** (`src/thesis/ch2.js`, Section 2.4). "Supervised contrastive learning Khosla et al. (2020) extends this self-supervised..." read as a run-on because `citN()` (narrative form) was used where `cit()` (parenthetical form) was needed. Fixed to `cit('khosla2020')`, giving "Supervised contrastive learning (Khosla et al., 2020) extends...". No change to the claim.

2. **Formatting bug in the reference list** (`src/thesis/references.js`). The in-proceedings formatter added a closing parenthesis after the page range unconditionally, even for NeurIPS entries whose `(Vol. N)` had already been closed earlier in the same string. This produced a stray trailing `)` for every NeurIPS citation with a page range: "In Advances in Neural Information Processing Systems (Vol. 33), pp. 18661-18673)." (Khosla et al. 2020, Vaswani et al. 2017, Paszke et al. 2019 — the three entries to which page ranges were added in a prior session's completion run). Fixed by tracking whether a parenthesis is actually open before closing it; verified the PMLR-venue entries (Ilse et al. 2018, which uses the other branch of the same function) still render correctly. All three NeurIPS entries now read correctly, e.g. "(Vol. 33, pp. 18661-18673)."

## Factual updates made necessary by new data (not argument rewrites)

3. **Table 5.16 → Table 5.19 (`tab:published`), IF-AIP and AIEpred cells.** Per Priority 4.1, these were retried through Scite's `read_fulltext`/`get_pdf_link` and SciSpace's `search`/`extract_data` and confirmed not publicly available (closed access, no absolute figures recoverable beyond IF-AIP's relative-improvement percentages already in the main text). Changed from `TODO` to `n/a` with that explanation, in the table caption, the surrounding prose, and the limitation in Section 5.10, per the explicit instruction not to leave these as open tasks once retried and confirmed unavailable.

4. **Stale "not attempted" claims about other protein language models.** A background Kaggle fetch (Priority 4.2) returned ProtT5-XL (encoder) embeddings and statistics (`results/tables/T5.14*`), which Section 5.6.4's existing populate-on-arrival code rendered automatically into two new tables. This made three existing sentences false as written, and all three were corrected to state what actually happened:
   - `src/thesis/ch4.js`, Section 4.7: "a comparison with other protein language models was not attempted" → now states it was completed for ProtT5-XL but not for ProtBERT, and why.
   - `src/thesis/ch6.js`, Future Work item 5: "were planned and not carried out" → now reports the ProtT5 result (no improvement over AAC + RF, consistent with the ESM-2 finding) and explains that only the ProtBERT half is still outstanding.
   - `src/thesis/ch5.js`, Section 5.6.4: added one sentence noting that the ProtBERT kernel (`aip-c4bert-cpu`) reported complete on Kaggle but produced only downloaded model weights, not computed embeddings, so it does not appear in Table 5.17.
   These are reports of what the new data showed, not re-interpretations of the thesis's existing findings; the three findings stated in the Abstract, Chapter 1 and Chapter 6 (leakage inflation, the null contrastive result, frozen embeddings underperforming composition) are untouched.

## Read and found consistent (no change)

- The Khosla et al. 2020 / Loshchilov and Hutter 2017 (AdamW) / Loshchilov and Hutter 2016 (SGDR) citations in Chapter 3: two different papers by the same two authors in different years is a legitimate citation pattern, confirmed against each paper's own year in `references.json`, not a duplication error.
- All numeric cross-chapter consistency checks (Section "Method" above) passed.
- Chapter 3's mathematical notation (`TP, TN, FP, FN undefined`, `AUROC/AUPRC undefined for a single class`) uses "undefined" in its correct mathematical sense, not a code artifact leaking into the text.
- Chapter 6, Section 6.3 ("nothing is known about other benchmarks or other peptide families") remains true even after the ProtT5 addition, since that addition is a different backbone on the same AIP benchmarks, not a different benchmark or peptide family; no change needed.

## Not reviewed line-by-line

Chapter 5's per-row table values (cross-validation and independent-set result tables, the λ-sweep tables, the pooling/fusion/fine-tuning tables) were not individually re-derived by hand; they are generated directly from `results/v2/*.csv` by the same code that produced them in prior sessions, and the automated consistency checks (same number quoted in two places) found no discrepancy anywhere a number is repeated across chapters. A full independent recomputation of every table was out of scope for a proofread.
