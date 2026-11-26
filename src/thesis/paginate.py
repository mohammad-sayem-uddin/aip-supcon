"""Read the rendered thesis and record which printed page each heading, table and
figure lands on, so the Table of Content and the lists carry real page numbers
instead of guessed ones.

    python3 src/thesis/paginate.py <thesis.pdf>

Writes results/thesis/pagemap.json: {key: printed page label}. The printed label is
taken from the footer of the page itself, so Roman preliminaries and Arabic body
pages are both reported exactly as they appear.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
THESIS = ROOT / "results/thesis"
FOOTER = "Daffodil International University"


def page_texts(pdf):
    """(printed label, text) for every page, label read from that page's own footer."""
    n = int(re.search(r"Pages:\s+(\d+)",
                      subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    out = []
    for p in range(1, n + 1):
        txt = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"],
                             capture_output=True, text=True).stdout
        label = None
        for ln in reversed(txt.strip().splitlines()):
            if FOOTER in ln:
                rest = ln.split(FOOTER, 1)[1].strip()
                if rest:
                    label = rest.split()[0]
                break
        out.append((label, txt))
    return out


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def find(pages, needle, start=0):
    """first page (index) whose text contains needle; None if absent"""
    nd = norm(needle)
    for i in range(start, len(pages)):
        if nd and nd in norm(pages[i][1]):
            return i
    return None


def find_nospace(pages, needle, start=0):
    """find, ignoring whitespace entirely: survives a tab the PDF swallowed"""
    nd = re.sub(r"\s+", "", needle).lower()
    for i in range(start, len(pages)):
        if nd and nd in re.sub(r"\s+", "", pages[i][1]).lower():
            return i
    return None


def first_line(txt):
    for ln in txt.strip().splitlines():
        if ln.strip():
            return norm(ln)
    return ""


def main(pdf):
    pages = page_texts(pdf)
    toc = json.loads((THESIS / "toc.json").read_text())
    pagemap, missing = {}, []

    # where the body starts: the first page whose printed label is an Arabic numeral.
    # Everything before it is preliminaries - and the Table of Content and the lists sit
    # there, repeating every title in the thesis, so body searches must skip them.
    body_start = next((i for i, (lab, _) in enumerate(pages) if lab and lab.isdigit()), 0)

    # front matter: each section starts a page, so match the page's own first line.
    # Two pages do not open with their Table-of-Content title and get an explicit probe:
    # the declaration page opens with the university name, and the full title page opens
    # with the thesis title.
    PROBE = {
        "Front:declaration": "declaration of thesis and copyright",
        "Front:title": "thesis submitted in fulfillment of the requirements",
    }
    for e in toc["front"]:
        want = norm(e["title"])
        if e["key"] in PROBE:
            probe = PROBE[e["key"]]
            i = next((k for k in range(body_start) if probe in norm(pages[k][1])), None)
        else:
            i = next((k for k in range(body_start) if first_line(pages[k][1]).startswith(want)), None)
        if i is not None and pages[i][0]:
            pagemap[e["key"]] = pages[i][0]
        else:
            missing.append(e["key"])

    # headings, in document order, searched only in the body
    cur = body_start
    for e in toc["body"]:
        i = find(pages, e["title"], cur) or find(pages, e["title"], body_start)
        if i is not None and pages[i][0]:
            pagemap[e["key"]] = pages[i][0]
            cur = i
        else:
            missing.append(e["key"])

    # tables and figures: match the caption itself - the number AND the opening words of
    # its title - so an in-text mention of "Table 3.1" cannot be mistaken for the caption.
    # The number and the title are separated by a tab, which pdftotext renders as spaces
    # for a one-digit number but swallows entirely for a two-digit one ("Table A.10The
    # fine-tuned ..."), so the second attempt drops whitespace from both sides. There is
    # deliberately no looser fallback: matching on the number alone would find the first
    # in-text citation of the table instead of the table, and record the wrong page.
    for c in toc["captions"]:
        key = f"{c['kind']}:{c['number']}"
        lead = " ".join(c["short"].split()[:5])
        needle = f"{c['kind']} {c['number']} {lead}"
        i = find(pages, needle, body_start)
        if i is None:
            i = find_nospace(pages, needle, body_start)
        if i is not None and pages[i][0]:
            pagemap[key] = pages[i][0]
        else:
            missing.append(key)

    # The appendix itself opens a page with "APPENDIX A" as its first line. Searching the
    # body text for "Appendix A" instead would land on the first chapter that mentions it
    # ("Table A.13 of Appendix A ..."), which is what the List of Appendices used to show.
    for letter in ("A", "B"):
        want = f"appendix {letter.lower()}"
        i = next((k for k in range(body_start, len(pages))
                  if first_line(pages[k][1]) == want), None)
        if i is not None and pages[i][0]:
            pagemap[f"Appendix:{letter}"] = pages[i][0]
        else:
            missing.append(f"Appendix:{letter}")

    (THESIS / "pagemap.json").write_text(json.dumps(pagemap, indent=1))
    print(f"pagemap.json: {len(pagemap)} entries located, {len(missing)} not found")
    for m in missing[:12]:
        print("   not found:", m)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "AIP THESIS - Mohammad Sayem Uddin.pdf"))
