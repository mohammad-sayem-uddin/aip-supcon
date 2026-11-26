# DIU_SPEC — the formatting rules this thesis is built to

Extracted on 2026-11-26 by reading the three reference PDFs in full (Part 0 of the assembly run). This file is the single source of truth for the build code in `src/thesis/`; it exists so that no later step has to re-read the PDFs or guess. Where a rule is quoted, it is quoted from the named document.

Precedence, as instructed: **`DIU_Thesis Guidelines.pdf` wins on every formatting question.** `SWE_Thesis Template_2024.pdf` governs the front matter and the visual conventions the Guidelines delegate to it (the Guidelines' page 8, "Layout and Arrangement of Content", contains nothing but a link to the template). `demo.pdf` is used **only** for footer layout and for how the logo and signature blocks sit on the declaration pages.

## 1. Page and type (Guidelines, "Thesis Format Bulletins")

| Rule | Value | Source |
|---|---|---|
| Paper | A4, 210 × 297 mm, white, printed one side only | Guidelines p.10 |
| Margin top | 2.5 cm | Guidelines p.12 |
| Margin bottom | 2.5 cm | Guidelines p.12 |
| Margin right | 2.5 cm | Guidelines p.12 |
| Margin left | **4.0 cm** | Guidelines p.12 |
| Body font | Times New Roman 12 pt (Arial 11 pt is the permitted alternative; Times New Roman chosen) | Guidelines p.11 |
| Body spacing | **Double** | Guidelines p.11 |
| Single spacing | long tables, table titles, long quotations, notes, footnotes, multiline captions, reference entries | Guidelines p.11 |
| Orphan rule | "A new paragraph must have at least 2 full lines on a page. Otherwise, begin on the next page." | Guidelines p.12 |
| Body alignment | Justified, first line indented (template body pages) | Template p.18 |
| Length | Bachelor thesis **must not exceed 30,000 words**; this thesis targets 22,000–23,000 | Guidelines p.10 |

## 2. Pagination (Guidelines, "Pagination")

- Title page is page (i); **the number is not typed**.
- Preliminaries in **lower-case Roman** numerals; all text and reference pages in **Arabic**.
- "Place the page number 1 cm from the bottom Centre of a page."
- "All page numbers are without punctuation."
- "All pages including those with diagrams, tables, etc. must have a page number."
- Appendices labelled with a letter (Appendix A), with or without page numbering.

### Footer conflict, and how it is resolved

The Guidelines put the page number at the **bottom centre**. The approved `demo.pdf` instead puts `©Daffodil International University` at the bottom **left** and the page number at the bottom **right**, on the same line, on every page including the body.

Resolution: the build exposes one configuration flag, `PAGE_NUMBER_POSITION`, in `src/thesis/lib.js`.
- `'centre'` — Guidelines-compliant: `©Daffodil International University` left, page number centred. **This is the default**, because the Guidelines are authoritative.
- `'right'` — demo-compliant: `©Daffodil International University` left, page number right.

Switching the flag changes every page in the document and nothing else.

## 3. Headings (Template p.18, p.30–33)

- `CHAPTER N` — centred, bold, at the top of the page.
- Chapter title (e.g. `INTRODUCTION`) — centred, bold, below it, separated by a blank line.
- Subdivisions start from the **left margin** (Guidelines p.13) and are numbered `1.1`, `1.1.1`, `1.1.1(a)` (Guidelines p.13). The template renders them as number, tab, then title in bold title case.
- The template numbers to level 4 (`2.2.1.1`); a fifth level is unnumbered.
- **Every chapter ends with a `Summary` section** (template Chapter 1 ends `1.3 Summary`).

## 4. Tables (Guidelines p.13–14; Template p.18)

- Caption **above** the table, formatted `Table 1.1<tab>Title` — **no colon**, not bold, single-spaced.
- Numbered per chapter in Arabic numerals; the number must correspond with the text; placed near the related discussion.
- Centred within the margins; **single-spaced**; decimals aligned within a column.
- **Horizontal rules only** — the template's tables have a top rule, a rule under the bold header row, and a bottom rule, and no vertical rules.
- Continued tables: heading reads `Table 1.1 Continued` (**do not repeat the table title**), and column and row headings must be repeated.
- Notes belong in the **bottom row** of the table and must wrap as paragraph text, not be listed one per line.
- A source line, where needed, sits below the table (template's "Citation for Table" style).

## 5. Figures (Guidelines p.14)

- Caption **below** the figure, formatted `Figure 1.1<tab>Title` — no colon.
- "Put only 1 blank line space between the figure and figure heading."
- Numbered per chapter; cited in the text before the figure appears.
- "Line diagrams should be drawn with the aid of a computer ... using black permanent ink or equivalent on white paper."
- "Unless necessary, the use of color in graphs and figures is discouraged."
- "Minimize clutter. Label subparts of figures as A and B, not (A) and (B)."
- A figure spanning pages carries its full heading at the bottom of the first page only.

## 6. Equations

- "For formula, use an equation editor including subscripts and superscripts" (Guidelines p.12).
- Numbered per chapter. The template prints the number **bare and right-aligned** (`2.1`), and refers to it in text as "Equation 2.1" — **not** `(2.1)`.

## 7. Footnotes

- "The use of footnotes is not encouraged for the Sciences, Engineering, Medical, and Business and should be kept to a minimum" (Guidelines p.13). This thesis uses **none**; table notes go in the table's bottom row.

## 8. Citation style — APA, and why

The Guidelines impose no single style ("DIU does not impose any restriction on the citation styles for your thesis. However, you are required to follow strictly to the style that you have chosen", Appendix A) and give Harvard examples, while the Guidelines' own "Writing Style" page names **APA** as a style "accepted by DIU".

**APA is chosen**, on three grounds:
1. The official `SWE_Thesis Template_2024.pdf` writes its own reference list in APA 7 — e.g. "Alexandrov, N., & Alexandrov, V. (2015). Computational science research methods for science education at PG level. *Procedia Computer Science*, 51(1), 1685–1693. https://doi.org/10.1016/j.procs.2015.05.305" — and cites in text as "(Crooks & Alibali, 2014)". Matching the department's own template is the strongest available evidence of what it expects.
2. The Guidelines' "Writing Style" page lists APA explicitly as accepted.
3. The thesis's 63-entry bibliography is already verified in APA form (`CITATION_AUDIT.md`), so choosing APA means reformatting nothing and risking no corruption of verified records.

In-text form is author–date: `(Gupta et al., 2017)` parenthetical, `Gupta et al. (2017)` narrative. Reference entries are single-spaced with a hanging indent.

## 9. Front matter order (Template; confirmed against its own Table of Content)

1. Title page (short) — page (i), number not printed
2. Declaration of Thesis and Copyright — CONFIDENTIAL / RESTRICTED / OPEN ACCESS checkboxes, inside a ruled box, with student and supervisor signature blocks
3. Supervisor's Declaration — DIU logo centred above the heading (demo.pdf)
4. Student's Declaration — DIU logo centred above the heading (demo.pdf)
5. Title page (full) — "Thesis submitted in fulfillment of the requirements for the award of the degree of", Bachelor of Science, Department of Software Engineering, DAFFODIL INTERNATIONAL UNIVERSITY, month and year
6. Acknowledgements
7. Dedication
8. Abstract (with a Keywords line)
9. Table of Content — the template's spelling is **"TABLE OF CONTENT"**, singular
10. List of Tables
11. List of Figures
12. List of Symbols
13. List of Abbreviations
14. List of Appendices

The lists use the same `Table 1.1<tab>Title<tab>page` form as the captions, with no colon.

## 10. Chapter structure (Template Table of Content)

Five chapters: `1 INTRODUCTION`, `2 LITERATURE REVIEW`, `3 METHODOLOGY`, `4 RESULTS AND DISCUSSION`, `5 CONCLUSION`, then `REFERENCES`, then `APPENDICES`. (The template's own Chapter 2 is "STYLES" because the template is a worked example of itself; the slot is the literature review in a real thesis, and the template notes "a thesis will usually have between five and seven chapters".)

## 11. Assets

`figures/assets/diu_logo.png` (225 × 225) was extracted from `demo.pdf` page 2 with `pdfimages`. It is the institutional mark used on the two declaration pages. The Guidelines' discouragement of colour applies to "graphs and figures"; the approved demo prints this logo in colour, so it is kept in colour.

## 12. Not implementable from the documents

- **Cover, spine and CD label** (gold lettering, buckram binding, 18 pt capitals) are physical print-shop instructions, not document content; they are not produced by this build.
- The Guidelines' pages 4, 5 and 9 are process infographics (submission steps, defence slide format) with no extractable formatting rule for the thesis body.
- `Slide Template (PPTX) File for Final_Defense.pdf` covers the defence presentation, not the thesis, and is out of scope for this build.
