# PLACEHOLDERS — what to fill in, where, and how

The thesis is finished and ready apart from the items below, which are personal to you or
need your department's values. Every one is deliberate and visibly bracketed, so nothing
can be missed by accident.

**Two ways to do it.** Either edit `AIP THESIS - Mohammad Sayem Uddin.docx` directly in
Word (find-and-replace the exact strings below — fastest, and nothing else can shift), or
put the values into `src/thesis/frontmatter.js` and rebuild, which keeps the build the
single source of truth. If you edit the `.docx` by hand, don't rebuild afterwards: the
build would overwrite your edits.

## 1. Find and replace, exactly as written

Replace the whole bracketed string, square brackets included. Word's Find and Replace
(Ctrl+H / Cmd+H) handles all of them.

| Search for | Replace with | Appears on page |
|---|---|---|
| `[THESIS TITLE]` | your title, same wording on every page | (i), iii, iv, vi |
| `[DATE OF BIRTH]` | e.g. 14 March 2002 | iii |
| `[ACADEMIC SESSION]` | e.g. 2021–2022 | iii |
| `[STUDENT ID]` | your ID number | iii, v |
| `[SUPERVISOR FULL NAME]` | your supervisor's full name | iii, iv |
| `[SUPERVISOR POSITION]` | e.g. Assistant Professor | iv |
| `[SUBMISSION MONTH YEAR]` | e.g. December 2026 | vi |

The title appears four times and must read identically in all four, so replace it with
"Replace All" rather than page by page.

## 2. Two pages to write yourself

Both are a single bracketed paragraph you replace with your own text.

- **Acknowledgements** (page vii) — normally thanks the supervisor, the Department of
  Software Engineering, Daffodil International University, and family.
- **Dedication** (page viii) — one or two lines.

Keep both inside the existing paragraph so the double spacing and margins stay as they are.

## 3. One box to tick

On page iii, the declaration page, tick exactly one of the three classification boxes:

- ☐ CONFIDENTIAL — needs a thesis declaration letter attached
- ☐ RESTRICTED — needs a thesis declaration letter attached
- ☐ OPEN ACCESS — published online, full text

In Word, replace that line's `☐` with `☒`. Most Bachelor theses take OPEN ACCESS; your
supervisor decides.

## 4. Two dates and two signatures

The declaration pages (iii, iv, v) each carry a `Date:` line and a signature rule left
blank on purpose — they are signed by hand on the printed copy.

## 5. Two TODO markers in the body

Both are highlighted in yellow so they cannot be missed in print, and both need something
only you can supply.

| Page | What it needs |
|---|---|
| 76 (§4.6.4) | the fine-tuning results at 150M and 650M — the Kaggle kernels errored; see `BLOCKERS_v2.md`. Section 4.6.4 is written to fill itself in if those results arrive and the chapter is rebuilt |
| 116 (Appendix B.5) | a permanent archive identifier — a Zenodo DOI for the submitted commit, which needs your own account |

If neither is going to happen before you submit, delete the two highlighted sentences in
Word; the surrounding text reads correctly without them.

## 6. Not a placeholder, but worth one decision

The page number sits at the **page centre**, 1 cm from the bottom, which is what the
Guidelines specify. The approved `demo.pdf` instead puts it at the bottom right with the
copyright notice on the left. If your department expects the `demo.pdf` arrangement,
change one line — `PAGE_NUMBER_POSITION` in `src/thesis/lib.js` from `'centre'` to
`'right'` — and rebuild; it switches all 143 pages.

## On the AI disclosure

You asked for the AI-disclosure wording to be left as a placeholder while you confirmed
DIU's policy. **There is no such block in the thesis**, because neither
`DIU_Thesis Guidelines.pdf` nor `SWE_Thesis Template_2024.pdf` mentions a disclosure of any
kind — both were searched for "artificial intelligence", "AI", "generative" and
"disclosure", with no match. Rather than invent a page and a wording your department has
not asked for, none was added. If it turns out one is required, it is a front-matter page
and can be added quickly once you have the required wording.

## When you are done

`DIU_COMPLIANCE.md` lists one failing rule, "no unmarked placeholders", and it counts
exactly the items above. Fill them in and all 24 rules pass. To re-check after a rebuild:

```bash
cd src/thesis && python3 compliance.py "../../AIP THESIS - Mohammad Sayem Uddin.docx" "../../AIP THESIS - Mohammad Sayem Uddin.pdf"
```
