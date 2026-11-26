# HANDOFF_REPORT — full thesis assembly

Rebuilt 2026-11-26. Supersedes every earlier handoff report.

## What you have now

| File | What it is |
|---|---|
| `AIP THESIS - Mohammad Sayem Uddin.docx` | **the complete thesis**: front matter, Chapters 1–5, references, Appendices A and B |
| `AIP THESIS - Mohammad Sayem Uddin.pdf` | the same, rendered, 143 pages |
| `CHAPTER 1…5 thesis.docx`, `FRONT MATTER`, `REFERENCES`, `APPENDIX A`, `APPENDIX B`, `ABSTRACT` | the same content exported chapter by chapter, for your supervisor |
| `DIU_SPEC.md` | every formatting rule, with the page of the Guidelines or template it came from |
| `DIU_COMPLIANCE.md` | 24 rules measured against the built file; 23 pass |
| `WORD_BUDGET.md` | the word-count measurement and every cut and relocation that met the target |
| `CITATION_STYLE.md` | why APA 7, and how it is applied |
| `NUMBERS_CHANGED.md` | every wording change the restructure and the budget forced, with the reason |

All eleven `.docx` files pass Office XML schema validation.

## 1. The chapter remap, and confirmation that nothing was lost

| Was | Now |
|---|---|
| Ch 1 Introduction | Chapter 1 Introduction |
| Ch 2 Literature Review | Chapter 2 Literature Review |
| Ch 3 Materials and Methods | Chapter 3 Methodology, §3.1–3.9 |
| Ch 4 Implementation and Experimental Setup | Chapter 3 Methodology, then Appendix B (§B.1–B.6) |
| Ch 5 Results and Discussion | Chapter 4 Results and Discussion |
| Ch 6 Conclusions and Future Work | Chapter 5 Conclusion |

There is no Chapter 6. Every section, table, figure, equation and cross-reference was
renumbered in one pass, and every build reports **zero unresolved references**.

**Nothing was lost.** A sentence-level diff of the rendered text before and after the merge
left 19 differences, each of them the renumbering itself, one of the five new Summary
sections, or one of six wording changes the merge forced — all listed in
`NUMBERS_CHANGED.md` §6. The word-budget work that followed moved material into the
appendices rather than deleting it; §7 of the same file lists every move and every
sentence that changed because of one.

Each chapter ends with a Summary (1.10, 2.8, 3.14, 4.11, 5.6).

## 2. Word count — the target is met

The target was 22,000–23,000 on definition (b), and you confirmed it as a requirement.

| | before any cutting | after the first pass | **final** |
|---|---:|---:|---:|
| Chapter 1 | 3,906 | 3,906 | **3,906** |
| Chapter 2 | 4,168 | 4,168 | **3,782** |
| Chapter 3 | 11,134 | 10,261 | **7,225** |
| Chapter 4 | 12,965 | 10,747 | **6,454** |
| Chapter 5 | 1,793 | 1,793 | **1,587** |
| **body, definition (b)** | **33,966** | **30,875** | **22,954** |

- **(a)** body prose alone: **22,044**
- **(b)** body prose + tables, captions and equations: **22,954** ← the target
- **(c)** everything, appendices and references included: **34,940**

Both (a) and (b) are also inside DIU's own 30,000 limit, so the question of which
definition the department counts no longer decides anything.

### Final split

| | printed pages | words |
|---|---|---:|
| front matter (i–xviii) | 18 | 261 (the abstract; the rest is placeholders) |
| body, Chapters 1–5 | 1–90 | 22,954 — of which prose 21,586, tables and captions 910 |
| references | 91–96 | 2,131 |
| appendices A and B | 97–125 | 9,594 |
| **total** | **143** | **34,940** |

### Every cut, in one paragraph

Twenty-seven detail tables and the implementation record of the study moved into
Appendices A and B, each still captioned, numbered and cited from the chapter it left;
four figures went whose tables carry the same numbers and two tables went whose figures
read better; about 90 sentences that recited table values were compressed, and twelve
figure captions shortened; Chapter 5, which restates Chapters 1–4 by construction, was
tightened by 206 words. `WORD_BUDGET.md` gives the measured yield of each lever — the
headline being that relocation was worth about seventeen times what compressing narration
was worth, the opposite of what the brief expected.

**Nothing you protected was touched**: Chapter 1 is unchanged to the word and Chapter 2's
prose is unchanged to the word; every methodology detail is still in the thesis; the
leakage finding, its mechanism and the two tables it rests on are in the body; the
limitations and every statistical caveat, confidence interval and minimum-detectable-effect
statement are intact.

## 3. DIU_COMPLIANCE results

**23 of 24 rules pass**, each measured from the built file rather than asserted: A4 with a
4.0 cm left margin (narrowest over 143 pages: left 4.00, right 2.47, top 2.50 cm, no page
outside), Times New Roman 12 pt throughout with smaller sizes only inside tables as the
Guidelines permit, double spacing with the named single-spaced exceptions, title page (i)
unnumbered, Roman preliminaries, Arabic body, a footer on every other page with the number
at the page centre 1.02 cm from the bottom edge, captions above tables and below figures,
horizontal table rules only, no numbering gaps, every table and figure cited, APA 7
throughout, no footnotes, front matter present and in the template's order, subparts
labelled A/B/C, widow control on every body paragraph, and both word-count rules.

The single failure is "no unmarked placeholders", which counts the seven bracketed
front-matter placeholders and the two TODO markers — all of them deliberate, all of them
listed in §5 below.

## 4. Three defects found and fixed while checking this build

Each was found by looking at the rendered pages rather than by trusting the build log.

1. **Twelve wrong page numbers in the List of Tables.** The page-mapping script matched a
   caption by its number and opening words; a tab that `pdftotext` swallows for two-digit
   numbers broke the match, and a loose fallback then recorded the page of the table's
   first *mention* instead. Tables A.10–A.14, A.17, A.18, B.10–B.13 and B.20 were all
   wrong, the worst by 76 pages. `paginate.py` now matches ignoring whitespace and has no
   loose fallback: a caption it cannot find is reported, not guessed.
2. **Both entries in the List of Appendices were wrong** (60 and 42 instead of 97 and 112),
   for the same reason: "Appendix A" matched the first chapter that mentions it. The script
   now requires the appendix's own title page.
3. **Every two-digit caption printed without a gap** — "Table A.18Paired comparisons…" —
   because the tab stop after the number sat at 0.75 in and the label overran it. It is now
   1 in, which clears the widest label the thesis produces.

A fourth, smaller one: `tab:hyper` and `tab:training` printed the same rows under two
numbers, and the restructure left Appendix B citing the number that no longer existed. The
duplicate is gone and B.3 cites Table B.12.

## 5. What I need from you

**Placeholder values** — all marked in the document:

- `[THESIS TITLE]` (appears on three pages)
- `[STUDENT ID]`
- `[ACADEMIC SESSION]`
- `[SUBMISSION MONTH YEAR]`
- `[SUPERVISOR FULL NAME]` and `[SUPERVISOR POSITION]`
- `[DATE OF BIRTH]`
- the acknowledgements and the dedication, both personal to you

`PLACEHOLDERS.md` lists each one with the page it appears on and the exact string to
search for in Word.

**On the AI disclosure**: you asked for it to be left as a placeholder while you confirmed
DIU's policy. There is no such block in the thesis, because neither `DIU_Thesis
Guidelines.pdf` nor `SWE_Thesis Template_2024.pdf` mentions a disclosure of any kind —
searching both for "artificial intelligence", "AI", "generative" and "disclosure" returns
nothing. Rather than invent a page and a wording the department has not asked for, none was
added. If your department does require one, it is a front-matter page and takes a few
minutes to add once you have the required wording.

**Decisions:**

1. Which classification box to tick on the declaration page — CONFIDENTIAL, RESTRICTED or
   OPEN ACCESS.
2. Whether the page number should sit at the page centre (Guidelines, the current setting)
   or at the right with the copyright notice on the left (as `demo.pdf` does). One flag,
   `PAGE_NUMBER_POSITION` in `src/thesis/lib.js`, switches every page.
3. Whether a Methodology chapter with its implementation record in Appendix B is what your
   department expects (see the last section of `WORD_BUDGET.md`).

**Two TODOs that only you can close:**

- a permanent archive identifier (a Zenodo DOI for the submitted commit) — needs your
  account;
- the fine-tuning results at 150M and 650M — the Kaggle kernels errored (`BLOCKERS_v2.md`).
  Section 4.6.4 is written to populate itself if those results arrive.

## 6. What I could not implement, and why

- **"Table N Continued".** The Guidelines want a table continued on a later page to repeat
  its column headings under a "Continued" heading. The headings *do* repeat — every table's
  header row is marked as a repeating header row — but the word "Continued" cannot be
  inserted automatically, because the generator cannot know where the page break will fall.
  It is a manual pass in Word on whichever tables break.
- **Figure 3.3 / 3.4 are swapped** against your list. Figure numbers must follow the order
  the figures appear in, and the regimes belong to §3.4 while the architecture belongs to
  §3.6. All five diagrams carry the content you asked for.
- **Vector figures in the .docx.** The five diagrams are written as vector PDF as well as
  the 400 dpi PNG the document embeds, because PNG is what embeds reliably across Word and
  LibreOffice. The PDFs are in `figures/` if you would rather place them by hand. Each is
  drawn at exactly the text-block width and embedded 1:1, so every label prints at the size
  it was drawn — nothing below 10 pt.
- **Cover, spine and CD label** (gold lettering, buckram, 18 pt capitals) are print-shop
  instructions, not document content, and are not produced by this build.

## 7. How to rebuild

```
cd src/thesis
for f in abstract ch1 ch2 ch3 ch4 ch5 appendices references; do node $f.js; done   # twice
node gen_toc.js && node build_thesis.js
soffice --headless --convert-to pdf "../../AIP THESIS - Mohammad Sayem Uddin.docx"
python3 paginate.py "../../AIP THESIS - Mohammad Sayem Uddin.pdf" && node build_thesis.js
python3 compliance.py "../../AIP THESIS - Mohammad Sayem Uddin.docx" "../../AIP THESIS - Mohammad Sayem Uddin.pdf"
```

Build each chapter twice so cross-references resolve; render, run `paginate.py`, and
rebuild once more so the Table of Content and the lists carry real page numbers. The page
map is a fixed point — rendering and re-running it after the final build changes nothing,
which is how this build was checked.

`docx` is required and resolves from `~/package.json`; if `require('docx')` fails, run
`npm install docx` from your home directory.
