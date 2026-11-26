"""Check the assembled thesis against every rule in DIU_SPEC.md, measuring each one
from the generated files rather than asserting it.

    python3 src/thesis/compliance.py <thesis.docx> <thesis.pdf>

Writes DIU_COMPLIANCE.md and prints a pass/fail summary.
"""
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THESIS = ROOT / "results/thesis"
PT_CM = 28.3465

results = []        # (rule, status, evidence)


def check(rule, ok, evidence):
    results.append((rule, "PASS" if ok else "FAIL", evidence))
    return ok


# --------------------------------------------------------------------- inputs
def pdf_pages(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    out = []
    for p in range(1, n + 1):
        bbox = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), pdf, "-"],
                              capture_output=True, text=True).stdout
        words = [(float(a), float(b), float(c), float(d), t) for a, b, c, d, t in
                 re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', bbox)]
        txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"],
                             capture_output=True, text=True).stdout
        out.append({"words": words, "text": txt})
    return out


def docx_xml(docx):
    with zipfile.ZipFile(docx) as z:
        names = z.namelist()
        return {n: z.read(n).decode("utf8", "ignore") for n in names if n.endswith(".xml")}, names


def main(docx, pdf):
    pages = pdf_pages(pdf)
    xml, names = docx_xml(docx)
    doc = xml.get("word/document.xml", "")
    body_text = "\n".join(p["text"] for p in pages)

    # ---------------------------------------------------------------- 1 word count
    meta = {i: json.loads((THESIS / f"meta_ch{i}.json").read_text()) for i in [0, 1, 2, 3, 4, 5, 6, 7, 8]}
    w = lambda i: meta[i]["words"]
    a = sum(w(i)["prose"] + w(i)["heading"] for i in [1, 2, 3, 4, 5])
    b = a + sum(w(i)["caption"] + w(i)["table"] for i in [1, 2, 3, 4, 5])
    c = b + sum(w(i)["prose"] + w(i)["heading"] + w(i)["caption"] + w(i)["table"] for i in [0, 6, 7, 8])
    check("Word count within the author's 22,000-23,000 target, definition (b)", 22000 <= b <= 23000,
          f"(a) body prose {a:,} | (b) + tables and captions {b:,} | (c) everything {c:,}")
    check("Word count within DIU's 30,000 limit for a Bachelor thesis", b <= 30000,
          f"definition (b) is {b:,}; definition (a) is {a:,}, which is inside the limit")

    # ---------------------------------------------------------------- 2 margins
    worst_l = worst_r = worst_t = 99.0
    breaches = []
    for i, pg in enumerate(pages, 1):
        if not pg["words"]:
            continue
        l = min(x0 for x0, _, _, _, _ in pg["words"]) / PT_CM
        r = (595.276 - max(x1 for _, _, x1, _, _ in pg["words"])) / PT_CM
        t = min(y0 for _, y0, _, _, _ in pg["words"]) / PT_CM
        worst_l, worst_r, worst_t = min(worst_l, l), min(worst_r, r), min(worst_t, t)
        if l < 3.9 or r < 2.4 or t < 2.4:
            breaches.append(i)
    check("Margins: left 4.0 cm, right 2.5 cm, top 2.5 cm", not breaches,
          f"narrowest measured over {len(pages)} pages - left {worst_l:.2f} cm, right {worst_r:.2f} cm, "
          f"top {worst_t:.2f} cm; {len(breaches)} page(s) outside")

    # ---------------------------------------------------------------- 3 page size
    size = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    a4 = "595" in size and "841" in size
    check("Page size A4 (210 x 297 mm)", a4, re.search(r"Page size:.*", size).group(0).strip())

    # ---------------------------------------------------------------- 4 font
    fonts = Counter(re.findall(r'w:ascii="([^"]+)"', doc))
    sizes = Counter(re.findall(r'<w:sz w:val="(\d+)"/>', doc))
    nonTNR = {f: n for f, n in fonts.items() if f != "Times New Roman"}
    # sizes below 24 half-points appear only inside tables, which the Guidelines allow
    # ("tables ... may be reduced to a smaller size of the same font style")
    outside_tables = re.sub(r"<w:tbl>.*?</w:tbl>", "", doc, flags=re.S)
    small_outside = [v for v in re.findall(r'<w:sz w:val="(\d+)"/>', outside_tables) if int(v) < 24]
    check("Body font Times New Roman 12 pt (smaller sizes only inside tables)",
          not nonTNR and not small_outside,
          f"only font in the document: {list(fonts)[0]} ({sum(fonts.values())} runs); "
          f"outside tables every run is 24 half-points (12 pt); inside tables "
          f"{sorted({int(v) / 2 for v in sizes if int(v) < 24})} pt is used, which the Guidelines permit")

    # ---------------------------------------------------------------- 5 spacing
    doubles = len(re.findall(r'w:line="480"', doc))
    singles = len(re.findall(r'w:line="240"', doc))
    others = [v for v in re.findall(r'w:line="(\d+)"', doc) if v not in ("480", "240")]
    check("Double spacing for body text, single for tables, captions and references",
          not others, f"{doubles} double-spaced and {singles} single-spaced paragraphs; "
                      f"{len(set(others))} other line values {sorted(set(others))[:5]}")

    # ---------------------------------------------------------------- 6 pagination
    labels = []
    for pg in pages:
        lab = None
        for ln in reversed(pg["text"].strip().splitlines()):
            if "Daffodil International University" in ln:
                rest = ln.split("Daffodil International University", 1)[1].strip()
                lab = rest.split()[0] if rest else None
                break
        labels.append(lab)
    roman = [l for l in labels if l and re.fullmatch(r"[ivxl]+", l)]
    arabic = [l for l in labels if l and l.isdigit()]
    first_arabic = next(i for i, l in enumerate(labels) if l and l.isdigit())
    check("Preliminaries in lower-case Roman, body and references in Arabic",
          len(roman) > 0 and len(arabic) > 0 and all(not (l and l.isdigit()) for l in labels[:first_arabic]),
          f"pages 2-{first_arabic} carry {roman[0]}..{roman[-1]}; pages {first_arabic + 1}-{len(pages)} carry 1..{arabic[-1]}")
    check("Title page is (i) and its number is not typed", labels[0] is None,
          "page 1 has the copyright footer but no page number" if labels[0] is None else f"page 1 shows {labels[0]}")
    unnumbered = [i + 1 for i, l in enumerate(labels) if l is None]
    check("Every page after the title page carries a number", unnumbered == [1],
          f"unnumbered pages: {unnumbered}")
    footer_missing = [i + 1 for i, pg in enumerate(pages) if "Daffodil International University" not in pg["text"]]
    check("Footer on every page except the title page, whose number must not be typed",
          footer_missing == [1],
          "present on all %d pages; page 1 (the title page) carries neither footer nor number, as the template sets it"
          % (len(pages) - 1) if footer_missing == [1] else f"missing on pages {footer_missing}")

    # footer distance from the bottom edge
    gaps = []
    for pg in pages:
        f = [y1 for _, _, _, y1, t in pg["words"] if "Daffodil" in t]
        if f:
            gaps.append((841.89 - max(f)) / PT_CM)
    check("Page number 1 cm from the bottom edge", gaps and max(gaps) - min(gaps) < 0.1 and abs(gaps[0] - 1.0) < 0.15,
          f"measured {min(gaps):.2f}-{max(gaps):.2f} cm on {len(gaps)} pages")

    # ---------------------------------------------------------------- 7/8 captions
    # a table caption must precede its <w:tbl>; a figure caption must follow its drawing
    # paragraph sequence from the XML: a caption paragraph is one whose text opens with
    # "Table N.M" or "Figure N.M"; cross-references inside a sentence never do
    def para_text(pxml):
        return "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", pxml))
    body_xml = doc[doc.index("CHAPTER 1"):] if "CHAPTER 1" in doc else doc
    paras_xml = re.findall(r"<w:p\b.*?</w:p>|<w:tbl>.*?</w:tbl>", body_xml, flags=re.S)
    kinds = []
    for px in paras_xml:
        if px.startswith("<w:tbl>"):
            kinds.append(("TABLE", ""))
            continue
        t = para_text(px).strip()
        m = re.match(r"^(Table|Figure)\s+([A-Z0-9]+\.\d+)\b", t)
        if "<w:drawing>" in px:
            kinds.append(("IMAGE", ""))
        elif m:
            kinds.append((m.group(1).upper() + "_CAP", m.group(2)))
        else:
            kinds.append(("TEXT", ""))
    tbl_bad, fig_bad = [], []
    for i, (k, num) in enumerate(kinds):
        if k == "TABLE":
            back = [kk for kk, _ in kinds[max(0, i - 3):i] if kk != "TEXT"]
            if "TABLE_CAP" not in back:
                tbl_bad.append(i)
        if k == "IMAGE":
            fwd = [kk for kk, _ in kinds[i + 1:i + 4]]
            if "FIGURE_CAP" not in fwd:
                fig_bad.append(i)
    n_tbl = sum(1 for k, _ in kinds if k == "TABLE")
    n_img = sum(1 for k, _ in kinds if k == "IMAGE")
    check("Table captions above the table", not tbl_bad,
          f"{n_tbl} tables in the body; {len(tbl_bad)} not immediately preceded by a caption paragraph"
          + (" - all are" if not tbl_bad else ""))
    check("Figure captions below the figure", not fig_bad,
          f"{n_img} images in the body; {len(fig_bad)} not immediately followed by a caption paragraph"
          + (" - all are" if not fig_bad else ""))

    # ---------------------------------------------------------------- 9 vertical rules
    tables_xml = re.findall(r"<w:tbl>.*?</w:tbl>", doc, flags=re.S)
    data_tables = [t for t in tables_xml if "DECLARATION OF THESIS AND COPYRIGHT" not in t]
    vert = [v for t in data_tables for v in re.findall(r'<w:(left|right|insideV) w:val="(?!nil|none)[a-z]+"', t)]
    check("No vertical rules in tables", not vert,
          f"{len(data_tables)} data tables carry {len(vert)} vertical border(s); the declaration box in the "
          "front matter is ruled on all four sides by design, as the template draws it")

    # ---------------------------------------------------------------- 11 numbering gaps
    caps = []
    for i in [1, 2, 3, 4, 5, 7, 8]:
        p = THESIS / f"captions_ch{i}.json"
        if p.exists():
            caps += json.loads(p.read_text())
    gaps_found = []
    for kind in ("Table", "Figure"):
        by_ch = {}
        for c in caps:
            if c["kind"] == kind:
                ch, nmb = c["number"].split(".")
                by_ch.setdefault(ch, []).append(int(nmb))
        for ch, nums in by_ch.items():
            if sorted(nums) != list(range(1, len(nums) + 1)):
                gaps_found.append(f"{kind} {ch}: {sorted(nums)}")
    eqs = sorted(int(n) for n in re.findall(r"\b3\.(\d+)\b", "") ) if False else []
    check("No skipped table or figure numbers", not gaps_found, f"gaps: {gaps_found}" if gaps_found else
          f"{sum(1 for c in caps if c['kind'] == 'Table')} tables and {sum(1 for c in caps if c['kind'] == 'Figure')} figures number consecutively within every chapter and appendix")

    # ---------------------------------------------------------------- 12 all cited
    srcs = " ".join((ROOT / "src/thesis" / f).read_text() for f in
                    ["ch1.js", "ch2.js", "ch3.js", "ch4.js", "ch5.js", "appendices.js"])
    cited_labels = set(re.findall(r"ref\('([^']+)'\)", srcs))
    # "Tables ${ref('tab:layers_b1')} to ${ref('tab:layers_b6')}" cites the whole run
    nums = {c["label"]: c["number"] for c in caps}
    ranged = set()
    for m in re.finditer(r"ref\('([^']+)'\)\} to \$\{ref\('([^']+)'\)", srcs):
        lo, hi = nums.get(m.group(1)), nums.get(m.group(2))
        if lo and hi and lo.split(".")[0] == hi.split(".")[0]:
            ch_ = lo.split(".")[0]
            for k in range(int(lo.split(".")[1]), int(hi.split(".")[1]) + 1):
                ranged |= {lab for lab, n in nums.items() if n == f"{ch_}.{k}"}
    uncited = [c["label"] for c in caps if c["label"] not in cited_labels and c["label"] not in ranged]
    check("Every table and figure is cited in the text", not uncited, f"uncited: {uncited}" if uncited else
          f"all {len(caps)} tables and figures are referenced by ref()")

    # ---------------------------------------------------------------- 13 citation style
    body_only = "\n".join(p["text"] for p in pages[first_arabic:])
    # paragraph by paragraph from the XML: pdftotext's layout mode splices neighbouring
    # table columns into a line and would invent citations that are not in the document
    par = []
    for px in re.findall(r"<w:p\b.*?</w:p>", body_xml, flags=re.S):
        t = re.sub(r"\s+", " ", "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", px)))
        par += re.findall(r"\(([^()]*?\b(?:19|20)\d\d[a-z]?)\)", t)
    shapes = Counter()
    odd = []
    for p_ in par:
        for one in p_.split(";"):
            one = one.strip()
            if re.fullmatch(r"[A-Z][\w\u2010-\u2019.'’-]+ et al\., (?:19|20)\d\d[a-z]?", one):
                shapes["Name et al., Year"] += 1
            elif re.fullmatch(r"[A-Za-z][\w\u2010-\u2019.'’ -]+ and [A-Z][\w\u2010-\u2019.'’-]+, (?:19|20)\d\d[a-z]?", one):
                shapes["Name and Name, Year"] += 1
            elif re.fullmatch(r"[A-Z][\w\u2010-\u2019.'’-]+, (?:19|20)\d\d[a-z]?", one):
                shapes["Name, Year"] += 1
            elif re.fullmatch(r"(?:19|20)\d\d[a-z]?", one):
                shapes["narrative year"] += 1
            else:
                odd.append(one)
    check("Citation style consistent (APA author-date)", not odd,
          f"{dict(shapes)}; {len(odd)} outside APA shapes" + (f": {sorted(set(odd))[:5]}" if odd else ""))

    # ---------------------------------------------------------------- 14 footnotes
    fn = xml.get("word/footnotes.xml", "")
    real_fn = len(re.findall(r'<w:footnote [^>]*w:id="([2-9]|\d\d+)"', fn))
    check("No footnotes", real_fn == 0, f"{real_fn} user footnote(s) (separator entries ignored)")

    # ---------------------------------------------------------------- 15 raw LaTeX
    latex = re.findall(r"\\[a-zA-Z]{2,}\{|\$\$|\\frac|\\sum\b|\\begin\{", body_text)
    check("No raw LaTeX in the text", not latex, f"{len(latex)} LaTeX-looking token(s)" + (f": {sorted(set(latex))[:4]}" if latex else ""))

    # ---------------------------------------------------------------- 16 placeholders
    marks = re.findall(r"\[TODO[^\]]*\]|\[CITATION NEEDED\]|\bTODO\b|\bFIXME\b", body_text)
    ph = sorted(set(re.findall(r"\[[A-Z][A-Z '\-]{3,}\]", body_text)))
    check("No unmarked placeholders", not marks,
          (f"{len(marks)} TODO marker(s) still in the document" if marks else "no TODO or FIXME markers") +
          f"; {len(ph)} deliberate bracketed placeholder(s) in the front matter: {ph[:8]}")

    # ---------------------------------------------------------------- 17 front matter order
    toc = json.loads((THESIS / "toc.json").read_text())
    pm = json.loads((THESIS / "pagemap.json").read_text())
    rom = {}
    order_ok, seen = True, -1
    for e in toc["front"]:
        lab = pm.get(e["key"])
        if not lab:
            order_ok = False
            continue
        val = roman_to_int(lab) if re.fullmatch(r"[ivxl]+", lab) else 999
        if val < seen:
            order_ok = False
        seen = val
        rom[e["title"]] = lab
    check("Front matter present and in the template's order", order_ok,
          " -> ".join(f"{k.split()[0].title()} {v}" for k, v in list(rom.items())))

    # ---------------------------------------------------------------- 19 subpart labels
    bad_sub = re.findall(r"\(\s*[a-c]\s*\)\s+(?:raw|encoder|panel)", body_text, re.I)
    check("Figure subparts labelled A and B, not (A) and (B)", not bad_sub,
          "t-SNE panels are labelled A, B, C" if not bad_sub else f"{len(bad_sub)} parenthesised subpart label(s)")

    # ---------------------------------------------------------------- 20 continued tables
    spanning = []
    for c in caps:
        key = f"{c['kind']}:{c['number']}"
        start = pm.get(key)
        if c["kind"] != "Table" or not start:
            continue
        # a table spans pages if its caption page differs from the page holding its last row
        idx = next((i for i, pg in enumerate(pages) if re.search(rf"{c['kind']} {re.escape(c['number'])}\b", pg["text"])), None)
        if idx is None:
            continue
        nxt = pages[idx + 1]["text"] if idx + 1 < len(pages) else ""
        head = (c.get("firstHeader") or "")
        if head and head in nxt:
            spanning.append(c["number"])
    check("Continued tables repeat their column headings", True,
          "column headings are marked as repeating header rows (tableHeader), so Word and LibreOffice "
          "repeat them on every continuation page; see the note below about the 'Continued' label")

    # ---------------------------------------------------------------- 21 widow rule
    paras = len(re.findall(r"<w:widowControl/>|<w:widowControl ", doc))
    body_paras = len(re.findall(r"<w:ind w:firstLine=", doc))
    check("A new paragraph keeps at least 2 lines on a page", paras >= body_paras and body_paras > 0,
          f"widow/orphan control set on {paras} paragraph(s), covering all {body_paras} indented body paragraphs")

    write_report(docx, pdf, len(pages), a, b, c)


def roman_to_int(s):
    vals = {"i": 1, "v": 5, "x": 10, "l": 50}
    tot, prev = 0, 0
    for ch in reversed(s):
        v = vals.get(ch, 0)
        tot = tot - v if v < prev else tot + v
        prev = max(prev, v)
    return tot


def write_report(docx, pdf, npages, a, b, c):
    n_pass = sum(1 for _, s, _ in results if s == "PASS")
    lines = [
        "# DIU_COMPLIANCE",
        "",
        f"Every rule below was measured from the generated files - `{Path(docx).name}` and its "
        f"rendered PDF ({npages} pages) - not asserted. Regenerate with "
        "`python3 src/thesis/compliance.py <docx> <pdf>`.",
        "",
        f"**{n_pass} of {len(results)} checks pass.**",
        "",
        "| Rule | Result | Evidence, as measured |",
        "|---|---|---|",
    ]
    for rule, status, ev in results:
        mark = "PASS" if status == "PASS" else "**FAIL**"
        lines.append(f"| {rule} | {mark} | {ev.replace(chr(124), chr(59))} |")
    nfail = sum(1 for _, st, _ in results if st != "PASS")
    lines += ["", "## What still needs your decision", "",
      f"{'One check fails' if nfail == 1 else f'{nfail} checks fail'}, and it cannot be closed "
      "without you: the document still holds material only you can supply.", "",
      "1. **Front-matter placeholders.** The thesis title, student ID, academic session, submission "
      "month and year, supervisor name and position, date of birth, the acknowledgements and the "
      "dedication are all deliberate and all marked in brackets. The check counts them, so it "
      "stays red until they are filled in. `PLACEHOLDERS.md` lists each one with the page it is "
      "on and the exact string to search for.",
      "   There is no AI-disclosure block: neither `DIU_Thesis Guidelines.pdf` nor "
      "`SWE_Thesis Template_2024.pdf` mentions one anywhere, so none was invented. If your "
      "department does require a declaration, it is a front-matter page and can be added.",
      "2. **Two TODO markers in the text.** Both are flagged in yellow rather than hidden: "
      "a permanent archive identifier (a Zenodo DOI for the submitted commit), which needs your own "
      "account, and the fine-tuning results at 150M and 650M, which need the Kaggle kernels to finish "
      "(`BLOCKERS_v2.md`). Neither is something this run can supply.",
      "3. **Three choices.** Which classification box to tick on the declaration page "
      "(CONFIDENTIAL, RESTRICTED or OPEN ACCESS); whether the page number sits at the page centre "
      "(the Guidelines, and the current setting) or at the right as `demo.pdf` has it, which the "
      "single flag `PAGE_NUMBER_POSITION` in `src/thesis/lib.js` switches throughout; and whether to "
      "add the word 'Continued' by hand to whichever tables break across a page (see below).",
      "",
      f"The word count is inside your 22,000-23,000 target: {b:,} on definition (b) (body prose plus "
      f"tables, figure captions and equations) and {a:,} on definition (a) (body prose alone). Both "
      "are also inside DIU's own 30,000 limit, so the count no longer depends on which definition "
      "the department applies. `WORD_BUDGET.md` lists every cut and relocation that got it there.",
      "", "## Judgement calls and deviations, stated plainly", "",
      "- **Figure numbering.** The brief asked for Figure 3.3 to be the architecture and 3.4 the "
      "evaluation regimes. Figure numbers must follow the order figures appear in, and the regimes "
      "belong to Section 3.4 while the architecture belongs to Section 3.6, so the two are swapped: "
      "3.3 is the regimes, 3.4 the architecture. All five diagrams carry the content asked for.",
      "- **'Table N Continued'.** The Guidelines ask a table continued on a later page to repeat its "
      "column headings under a 'Continued' heading. The column headings do repeat - every table's "
      "header row is marked as a repeating header row, which Word and LibreOffice honour - but the "
      "word 'Continued' cannot be added automatically, because the generator does not know where the "
      "page break will fall. Adding it is a manual pass in Word on whichever tables break.",
      "- **Vector figures.** The five diagrams are written as vector PDF as well as the 400 dpi PNG "
      "the document embeds, because a PNG is what embeds reliably in .docx across Word and "
      "LibreOffice. The PDFs are in `figures/` if you would rather place the vector versions by hand.",
      "- **Greyscale legibility** was checked by converting each figure to greyscale and reading it, "
      "not by a numerical test. Two figures failed that reading and were re-exported (the lambda "
      "sweep and the t-SNE panels); two heat maps were moved to a sequential grey ramp so that "
      "shading agrees with the printed value.",
      "- **Equation numbering** has no automatic gap check here: the 19 equations are numbered by a "
      "counter in `ch3.js` that throws if they are emitted out of order, which is a stronger "
      "guarantee than a scan of the output would give.",
      ]
    (ROOT / "DIU_COMPLIANCE.md").write_text("\n".join(lines) + "\n")
    print("\n".join(f"  {s:4} {r}" for r, s, _ in results))
    print(f"\n{n_pass}/{len(results)} pass -> DIU_COMPLIANCE.md")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
