# HANDOFF_REPORT — full thesis assembly

Rebuilt 2026-11-26 at the end of the assembly run. Supersedes the previous handoff report, which described the six-chapter draft.

## What you have now

| File | What it is |
|---|---|
| `AIP THESIS - Mohammad Sayem Uddin.docx` | **the complete thesis**: front matter, Chapters 1–5, references, Appendices A and B |
| `AIP THESIS - Mohammad Sayem Uddin.pdf` | the same, rendered, 142 pages |
| `CHAPTER 1…5 thesis.docx`, `FRONT MATTER`, `REFERENCES`, `APPENDIX A`, `APPENDIX B`, `ABSTRACT` | the same content exported chapter by chapter, for your supervisor |
| `DIU_SPEC.md` | every formatting rule, with the page of the Guidelines or template it came from |
| `DIU_COMPLIANCE.md` | 24 rules measured against the built file; 21 pass |
| `WORD_BUDGET.md` | the word-count measurement and the decision waiting on you |
| `CITATION_STYLE.md` | why APA, and how it is applied |
| `NUMBERS_CHANGED.md` | every wording change the restructure forced, with the reason |

All eleven `.docx` files pass Office XML schema validation.

## 1. The chapter remap, and confirmation that nothing was lost

| Was | Now |
|---|---|
| Ch 1 Introduction | Chapter 1 Introduction |
| Ch 2 Literature Review | Chapter 2 Literature Review |
| Ch 3 Materials and Methods | Chapter 3 Methodology, §3.1–3.9 |
| Ch 4 Implementation and Experimental Setup | Chapter 3 Methodology, §3.10–3.16 |
| Ch 5 Results and Discussion | Chapter 4 Results and Discussion |
| Ch 6 Conclusions and Future Work | Chapter 5 Conclusion |

There is no Chapter 6. Every section, table, figure, equation and cross-reference was renumbered in one pass, and both build passes report **zero unresolved references**.

**Nothing was lost.** A sentence-level diff of the rendered text before and after the merge (1,012 → 1,026 sentences over 40 characters) left 19 differences, each of which is the renumbering itself, one of the five new Summary sections, or one of six wording changes the merge forced — all six listed in `NUMBERS_CHANGED.md` §6. Word count rose by exactly the length of the new summaries.

Each chapter now ends with a Summary (1.10, 2.8, 3.17, 4.11, 5.6).

## 2. Word counts, before and after

Measured by the build itself, which counts and categorises every word as it emits it.

| | before Part 2 | now |
|---|---:|---:|
| Chapter 1 | 3,906 | 3,906 |
| Chapter 2 | 4,168 | 4,168 |
| Chapter 3 | 11,134 | 10,297 |
| Chapter 4 | 12,965 | 11,049 |
| Chapter 5 | 1,793 | 1,793 |
| **body, definition (b)** | **33,966** | **31,213** |

Final split:

| | pages | words |
|---|---:|---:|
| front matter (i–xvii) | 17 | 261 (the abstract; the rest is placeholders) |
| body, Chapters 1–5 | printed 1–110 | 31,213 — of which prose 25,485, tables and captions 5,728 |
| references | 111–117 | 2,131 |
| appendices A and B | 118–125 | 2,819 |
| **total** | **142** | **36,424** |

### Every cut made

**Moved to appendices** (nothing deleted; each is still cited from the chapter it left): the per-model result tables for Ind_425 and Ind_1049, the paired comparisons of the representation study, the temperature sweep → Appendix A; the layer-by-layer definitions of models B1–B6 and the per-stage compute table → Appendix B. −2,640 words.

**Removed as duplication** (never a table and a figure for the same data): four figures whose tables carry the numbers and the confidence intervals (leakage gap, six architectures, pooling, fine-tuning), and two tables whose figures read better (cross-benchmark heat map, λ sweep curve). −435 words.

**Compressed narration**: one worked paragraph in §4.4.3. This lever was measured rather than assumed, and it is worth far less than expected — see below.

## 3. The decision waiting on you

The target was 22,000–23,000 on definition (b). The thesis is at **31,213**.

Everything that could be cut without touching what you protected has been cut. Lever 3 — compressing prose that narrates table values — was expected to yield most of the slack; measuring it on the worst offender (a 538-word paragraph reciting 28 values) removed **five values and sixteen words**, because a number costs one word wherever it sits. Across Chapter 4 the whole lever is worth roughly 1,300 words, and levers 4 and 5 perhaps 650 more. Best reachable without protected material: about **28,900**.

The remaining ~5,900 could only come from Chapter 3's reproducibility detail, Chapters 1–2, or the limitations and statistical caveats. Rule 2.3 says stop, so I stopped and touched none of them.

One thing worth settling first: **DIU's own limit is 30,000**, and the thesis meets it on definition (a) — 25,485 — but not on (b). Which definition the department counts decides whether this is a real problem. That is one question to your supervisor, and it may dissolve the issue. `WORD_BUDGET.md` sets out four costed ways forward.

## 4. DIU_COMPLIANCE results

**21 of 24 rules pass**, each measured from the built file rather than asserted: A4 with a 4.0 cm left margin (narrowest measured over 142 pages: left 4.00, right 2.47, top 2.50 cm, no page outside), Times New Roman 12 pt throughout with the smaller font only inside tables as the Guidelines permit, double spacing with the named single-spaced exceptions, title page (i) unnumbered, Roman preliminaries, Arabic body, footer on every other page with the number at the page centre 1.02 cm from the bottom edge, captions above tables and below figures, horizontal table rules only, no numbering gaps, every table and figure cited, APA throughout, no footnotes, no raw LaTeX, front matter present and ordered, subparts labelled A/B/C, widow control on every body paragraph.

The three failures are the two word-count rules above, and two TODO markers that are flagged in yellow rather than hidden.

## 5. What I need from you

**Placeholder values** — all marked in the document:

- `[THESIS TITLE]` (appears on three pages)
- `[STUDENT ID]`
- `[ACADEMIC SESSION]`
- `[SUBMISSION MONTH YEAR]`
- `[SUPERVISOR FULL NAME]` and `[SUPERVISOR POSITION]`
- `[DATE OF BIRTH]`
- the acknowledgements and the dedication, both personal to you
- the **AI-disclosure wording**, left blank as you asked while you confirm DIU's policy

**Decisions:**

1. Which word-count definition applies, and which option in `WORD_BUDGET.md` you want.
2. Whether the page number should sit at the page centre (Guidelines, the current setting) or at the right with the copyright notice on the left (as `demo.pdf` does). One flag, `PAGE_NUMBER_POSITION` in `src/thesis/lib.js`, switches every page.
3. Which classification box to tick on the declaration page — CONFIDENTIAL, RESTRICTED or OPEN ACCESS.

**Two TODOs that only you can close:**

- a permanent archive identifier (a Zenodo DOI for the submitted commit) — needs your account;
- the fine-tuning results at 150M and 650M — the Kaggle kernels errored and one is still running (`BLOCKERS_v2.md`). Section 4.6.4 is written to populate itself if those results arrive.

## 6. What I could not implement, and why

- **"Table N Continued".** The Guidelines want a table continued on a later page to repeat its column headings under a "Continued" heading. The headings *do* repeat — every table's header row is marked as a repeating header row — but the word "Continued" cannot be inserted automatically, because the generator cannot know where the page break will fall. It is a manual pass in Word on whichever tables break.
- **Figure 3.3 / 3.4 are swapped** against your list. Figure numbers must follow the order the figures appear in, and the regimes belong to §3.4 while the architecture belongs to §3.6. All five diagrams carry the content you asked for.
- **Vector figures in the .docx.** The five diagrams are written as vector PDF as well as the 400 dpi PNG the document embeds, because PNG is what embeds reliably across Word and LibreOffice. The PDFs are in `figures/` if you would rather place them by hand. Each is drawn at exactly the text-block width and embedded 1:1, so every label prints at the size it was drawn — nothing below 10 pt.
- **Cover, spine and CD label** (gold lettering, buckram, 18 pt capitals) are print-shop instructions, not document content, and are not produced by this build.

## 7. How to rebuild

```
cd src/thesis
for f in abstract ch1 ch2 ch3 ch4 ch5 appendices references; do node $f.js; done   # twice
node gen_toc.js && node build_thesis.js
python3 paginate.py "../../AIP THESIS - Mohammad Sayem Uddin.pdf" && node build_thesis.js
python3 compliance.py "../../AIP THESIS - Mohammad Sayem Uddin.docx" "../../AIP THESIS - Mohammad Sayem Uddin.pdf"
```

Build each chapter twice so cross-references resolve; render, run `paginate.py`, and rebuild once more so the Table of Content carries real page numbers. The page map is a fixed point — re-running it changes nothing.
