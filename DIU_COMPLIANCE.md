# DIU_COMPLIANCE

Every rule below was measured from the generated files - `AIP THESIS - Mohammad Sayem Uddin.docx` and its rendered PDF (142 pages) - not asserted. Regenerate with `python3 src/thesis/compliance.py <docx> <pdf>`.

**21 of 24 checks pass.**

| Rule | Result | Evidence, as measured |
|---|---|---|
| Word count within the author's 22,000-23,000 target, definition (b) | **FAIL** | (a) body prose 25,485 ; (b) + tables and captions 31,213 ; (c) everything 36,424 |
| Word count within DIU's 30,000 limit for a Bachelor thesis | **FAIL** | definition (b) is 31,213; definition (a) is 25,485, which is inside the limit |
| Margins: left 4.0 cm, right 2.5 cm, top 2.5 cm | PASS | narrowest measured over 142 pages - left 4.00 cm, right 2.47 cm, top 2.50 cm; 0 page(s) outside |
| Page size A4 (210 x 297 mm) | PASS | Page size:       595.304 x 841.89 pts (A4) |
| Body font Times New Roman 12 pt (smaller sizes only inside tables) | PASS | only font in the document: Times New Roman (3541 runs); outside tables every run is 24 half-points (12 pt); inside tables [7.0, 7.5, 8.0, 8.5, 9.0] pt is used, which the Guidelines permit |
| Double spacing for body text, single for tables, captions and references | PASS | 311 double-spaced and 3616 single-spaced paragraphs; 0 other line values [] |
| Preliminaries in lower-case Roman, body and references in Arabic | PASS | pages 2-18 carry ii..xviii; pages 19-142 carry 1..124 |
| Title page is (i) and its number is not typed | PASS | page 1 has the copyright footer but no page number |
| Every page after the title page carries a number | PASS | unnumbered pages: [1] |
| Footer on every page except the title page, whose number must not be typed | PASS | present on all 141 pages; page 1 (the title page) carries neither footer nor number, as the template sets it |
| Page number 1 cm from the bottom edge | PASS | measured 1.02-1.02 cm on 141 pages |
| Table captions above the table | PASS | 42 tables in the body; 0 not immediately preceded by a caption paragraph - all are |
| Figure captions below the figure | PASS | 10 images in the body; 0 not immediately followed by a caption paragraph - all are |
| No vertical rules in tables | PASS | 42 data tables carry 0 vertical border(s); the declaration box in the front matter is ruled on all four sides by design, as the template draws it |
| No skipped table or figure numbers | PASS | 42 tables and 10 figures number consecutively within every chapter and appendix |
| Every table and figure is cited in the text | PASS | all 52 tables and figures are referenced by ref() |
| Citation style consistent (APA author-date) | PASS | {'Name and Name, Year': 19, 'Name et al., Year': 129, 'Name, Year': 6, 'narrative year': 79}; 0 outside APA shapes |
| No footnotes | PASS | 0 user footnote(s) (separator entries ignored) |
| No raw LaTeX in the text | PASS | 0 LaTeX-looking token(s) |
| No unmarked placeholders | **FAIL** | 2 TODO marker(s) still in the document; 7 deliberate bracketed placeholder(s) in the front matter: ['[ACADEMIC SESSION]', '[DATE OF BIRTH]', '[STUDENT ID]', '[SUBMISSION MONTH YEAR]', '[SUPERVISOR FULL NAME]', '[SUPERVISOR POSITION]', '[THESIS TITLE]'] |
| Front matter present and in the template's order | PASS | Declaration iii -> Supervisor'S iv -> Student'S v -> Title vi -> Acknowledgements vii -> Dedication viii -> Abstract ix -> Table x -> List xiii -> List xv -> List xvi -> List xvii -> List xviii |
| Figure subparts labelled A and B, not (A) and (B) | PASS | t-SNE panels are labelled A, B, C |
| Continued tables repeat their column headings | PASS | column headings are marked as repeating header rows (tableHeader), so Word and LibreOffice repeat them on every continuation page; see the note below about the 'Continued' label |
| A new paragraph keeps at least 2 lines on a page | PASS | widow/orphan control set on 254 paragraph(s), covering all 194 indented body paragraphs |

## What still needs your decision

Three checks fail. None of them can be closed without you.

1. **Word count against your 22,000-23,000 target.** The thesis is at 31,213 on definition (b) and 25,485 on definition (a). Everything that could be cut without touching the material you protected has been cut; `WORD_BUDGET.md` sets out the four ways forward and what each costs. Until you choose one, this check stays red.
2. **Word count against DIU's own 30,000 limit.** Met on definition (a), exceeded on (b). Which definition the department counts decides whether this is a real problem or not, and the Guidelines do not say. Worth one question to your supervisor.
3. **Two TODO markers remain in the text.** Both are flagged in yellow rather than hidden: a permanent archive identifier (a Zenodo DOI for the submitted commit), which needs your own account, and the fine-tuning results at 150M and 650M, which need the Kaggle kernels to finish (`BLOCKERS_v2.md`). Neither is something this run can supply.

Placeholders in the front matter are deliberate and marked: thesis title, student ID, academic session, submission month and year, supervisor name and position, date of birth, the acknowledgements, the dedication and the AI-disclosure wording.

## Judgement calls and deviations, stated plainly

- **Figure numbering.** The brief asked for Figure 3.3 to be the architecture and 3.4 the evaluation regimes. Figure numbers must follow the order figures appear in, and the regimes belong to Section 3.4 while the architecture belongs to Section 3.6, so the two are swapped: 3.3 is the regimes, 3.4 the architecture. All five diagrams carry the content asked for.
- **'Table N Continued'.** The Guidelines ask a table continued on a later page to repeat its column headings under a 'Continued' heading. The column headings do repeat - every table's header row is marked as a repeating header row, which Word and LibreOffice honour - but the word 'Continued' cannot be added automatically, because the generator does not know where the page break will fall. Adding it is a manual pass in Word on whichever tables break.
- **Vector figures.** The five diagrams are written as vector PDF as well as the 400 dpi PNG the document embeds, because a PNG is what embeds reliably in .docx across Word and LibreOffice. The PDFs are in `figures/` if you would rather place the vector versions by hand.
- **Greyscale legibility** was checked by converting each figure to greyscale and reading it, not by a numerical test. Two figures failed that reading and were re-exported (the lambda sweep and the t-SNE panels); two heat maps were moved to a sequential grey ramp so that shading agrees with the printed value.
- **Equation numbering** has no automatic gap check here: the 19 equations are numbered by a counter in `ch3.js` that throws if they are emitted out of order, which is a stronger guarantee than a scan of the output would give.
