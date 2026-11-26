# CITATION_STYLE — the style chosen, and why

Assembly run, Part 6. One style, applied everywhere.

## The choice: APA (7th edition), author–date

The Guidelines leave the choice open but demand consistency: "DIU does not impose any restriction on the citation styles for your thesis. However, you are required to follow strictly to the style that you have chosen" (Appendix A), and they give Harvard examples. Separately, the Guidelines' "Writing Style" page names **APA** as a style accepted by DIU.

APA was chosen on three grounds, in order of weight:

1. **The department's own template is written in APA 7.** `SWE_Thesis_Template_2024.pdf` cites in text as "(Crooks & Alibali, 2014)" and lists its references as "Alexandrov, N., & Alexandrov, V. (2015). Computational science research methods for science education at PG level. *Procedia Computer Science*, 51(1), 1685–1693. https://doi.org/10.1016/j.procs.2015.05.305". Matching the template the department issues is the strongest evidence of what it expects.
2. **The Guidelines name APA explicitly** as an accepted style.
3. **The bibliography was already verified in APA form.** All 63 entries were checked against CrossRef, arXiv, OpenAlex and Scite in earlier work (`CITATION_AUDIT.md`: zero retractions, zero misattributions). Choosing APA meant reformatting presentation only, with no risk of corrupting a verified record.

## How it is applied

**In text.** Author–date throughout: `(Gupta et al., 2017)` parenthetically, `Gupta et al. (2017)` narratively, multiple sources separated by semicolons inside one pair of brackets. Measured over the five body chapters: 153 parenthetical and 16 narrative citations, every one of them in one of the three APA shapes (`Name, Year`, `Name and Name, Year`, `Name et al., Year`). No other shape occurs.

**Reference list.** `Family, I., Family, I., & Family, I. (Year). Title. *Journal*, volume(issue), pages. https://doi.org/...`, single-spaced with a hanging indent, alphabetical by first author's family name. Preprints without a journal are given as `arXiv preprint arXiv:NNNN.NNNNN` with the abstract URL. Conference papers carry the proceedings volume and page range.

**Sentence case.** APA puts article titles in sentence case. Publishers supply titles in their own capitalisation, and 26 of the 63 records arrived in Title Case. Rather than edit the verified records, the conversion is done at render time in `src/thesis/references.js`: a word is lowercased only when it is plainly an ordinary word, so anything with an internal capital (`BiTCNs`, `PyTorch`, `t-SNE`, `ProtTrans`), anything containing a digit (`ESM-2`, `RDP58`), the word after a colon, the first word of the title, and a short keep-list (`Python`, `Global Burden of Disease`, …) are left as the publisher wrote them. `results/thesis/references.json` still holds each record exactly as it was retrieved, so the audit trail is intact.

## Quotations

The thesis quotes no source at length; there are no block quotations, and nothing needed one. Two places had borrowed wording in quotation marks without a page reference, which APA would require:

- Table 2.1 quoted a predictor's own phrase, "Great superiority", from a paper whose only available text is an unpaginated abstract. Since no page reference exists, the quotation was replaced with a paraphrase — "Reported as a superiority over the compared AIP and AMP predictors, with no magnitude given in the available text" — which keeps the point that the claim is unquantified.
- Section 2.4 used the quoted term "midnight zone". It is a named concept rather than borrowed prose, so the quotation marks were removed and the term is carried by the citation to Heinzinger et al. (2022) in the same sentence.

Two other quoted strings remain and are not borrowed material: `"λ contrasts in Phase B"` is the thesis's own name for one of its families of tests, and `"No effect of the contrastive objective was found"` is the thesis quoting its own earlier sentence in order to qualify it.

## Method descriptions

Every method description in Chapter 3 is written from what the code does — the layer tables, loss definitions, folds, metrics and statistical procedure are all generated from or checked against the project's own result files — not from how a source paper described its own method. Where a published method is reported, the thesis says so and names the source and the table it was read from (`results/tables/T5_7_published_reported.csv`).

No attempt has been made to game a similarity checker. Matching reference entries, standard technical phrasing, dataset names and metric definitions are expected to match other work, and were left as they are.
