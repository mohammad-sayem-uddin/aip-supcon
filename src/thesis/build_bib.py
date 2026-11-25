"""Build references.bib / references.json ONLY from indexed records (CrossRef, DBLP, arXiv).

Each candidate carries a search seed (title words, first-author family name, year). A record is accepted only if the record's own
title is >= 0.90 similar to the seed title, the first author's family name matches and the year matches. Every bibliographic field
written to the .bib comes from the record, never from this file. Anything that fails is reported in CITATIONS_TO_VERIFY.md.
"""
from __future__ import annotations

import difflib
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date

from src.utils import ROOT

UA = {"User-Agent": "thesis-bibliography-check/1.0"}
OUT = ROOT / "results" / "thesis"

# key, title seed, first-author family seed, year seed, preferred index
CANDIDATES = [
    ("gupta2017", "Prediction of anti-inflammatory proteins/peptides: an insilico approach", "Gupta", 2017, "crossref"),
    ("manavalan2018", "AIPpred: Sequence-Based Prediction of Anti-inflammatory Peptides Using Random Forest", "Manavalan", 2018, "crossref"),
    ("khatun2019", "PreAIP: Computational Prediction of Anti-inflammatory Peptides by Integrating Multiple Complementary Features", "Khatun", 2019, "crossref"),
    ("deng2022", "Prediction of anti-inflammatory peptides by a sequence-based stacking ensemble model named AIPStack", "Deng", 2022, "crossref"),
    ("vita2019", "The Immune Epitope Database (IEDB): 2018 update", "Vita", 2019, "crossref"),
    ("lin2023", "Evolutionary-scale prediction of atomic-level protein structure with a language model", "Lin", 2023, "crossref"),
    ("rives2021", "Biological structure and function emerge from scaling unsupervised learning to 250 million protein sequences", "Rives", 2021, "crossref"),
    ("bhasin2004", "Classification of nuclear receptors based on amino acid composition and dipeptide composition", "Bhasin", 2004, "crossref"),
    ("dubchak1995", "Prediction of protein folding class using global description of amino acid sequence", "Dubchak", 1995, "crossref"),
    ("needleman1970", "A general method applicable to the search for similarities in the amino acid sequence of two proteins", "Needleman", 1970, "crossref"),
    ("henikoff1992", "Amino acid substitution matrices from protein blocks", "Henikoff", 1992, "crossref"),
    ("li2006", "Cd-hit: a fast program for clustering and comparing large sets of protein or nucleotide sequences", "Li", 2006, "crossref"),
    ("hochreiter1997", "Long Short-Term Memory", "Hochreiter", 1997, "crossref"),
    ("matthews1975", "Comparison of the predicted and observed secondary structure of T4 phage lysozyme", "Matthews", 1975, "crossref"),
    ("delong1988", "Comparing the areas under two or more correlated receiver operating characteristic curves: a nonparametric approach", "DeLong", 1988, "crossref"),
    ("mcnemar1947", "Note on the sampling error of the difference between correlated proportions or percentages", "McNemar", 1947, "crossref"),
    ("benjamini1995", "Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing", "Benjamini", 1995, "crossref"),
    ("efron1979", "Bootstrap Methods: Another Look at the Jackknife", "Efron", 1979, "crossref"),
    ("wolf2020", "Transformers: State-of-the-Art Natural Language Processing", "Wolf", 2020, "crossref"),
    ("cock2009", "Biopython: freely available Python tools for computational molecular biology and bioinformatics", "Cock", 2009, "crossref"),
]

# arXiv records fetched by identifier and then verified on title, first author and year (identifier is a lookup key, not a claim)
ARXIV = [
    ("khosla2020", "2004.11362", "Supervised Contrastive Learning", "Khosla"),
    ("vaswani2017", "1706.03762", "Attention Is All You Need", "Vaswani"),
    ("ilse2018", "1802.04712", "Attention-based Deep Multiple Instance Learning", "Ilse"),
    ("loshchilov2017", "1711.05101", "Decoupled Weight Decay Regularization", "Loshchilov"),
    ("paszke2019", "1912.01703", "PyTorch: An Imperative Style, High-Performance Deep Learning Library", "Paszke"),
    ("pedregosa2012", "1201.0490", "Scikit-learn: Machine Learning in Python", "Pedregosa"),
]


def get(url: str, retries: int = 3) -> bytes:
    for i in range(retries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
        except Exception as e:  # noqa: BLE001
            time.sleep(2 + 2 * i)
            last = e
    raise last


norm = lambda s: re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()
sim = lambda a, b: difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def crossref(title, fam, year):
    q = urllib.parse.urlencode({"query.bibliographic": f"{title} {fam} {year}", "rows": 6})
    items = json.loads(get(f"https://api.crossref.org/works?{q}"))["message"]["items"]
    out = []
    for it in items:
        t = (it.get("title") or [""])[0]
        au = it.get("author") or []
        y = None
        for k in ("published-print", "issued", "published-online", "published"):
            if it.get(k, {}).get("date-parts", [[None]])[0][0]:
                y = it[k]["date-parts"][0][0]
                break
        out.append({"title": re.sub(r"<[^>]+>", "", t), "authors": [(a.get("family", ""), a.get("given", "")) for a in au], "year": y,
                    "container": (it.get("container-title") or [""])[0], "volume": it.get("volume", ""), "issue": it.get("issue", ""),
                    "pages": it.get("page", ""), "doi": it.get("DOI", ""), "type": it.get("type", ""), "publisher": it.get("publisher", ""),
                    "record": f"https://api.crossref.org/works/{it.get('DOI', '')}", "source": "CrossRef"})
    return out


def dblp(title, fam, year):
    q = urllib.parse.urlencode({"q": f"{title} {fam}", "format": "json", "h": 10})
    hits = json.loads(get(f"https://dblp.org/search/publ/api?{q}"))["result"]["hits"].get("hit", [])
    out = []
    for h in hits:
        i = h["info"]
        au = i.get("authors", {}).get("author", [])
        au = au if isinstance(au, list) else [au]
        names = []
        for a in au:
            nm = re.sub(r"\s\d{4}$", "", a["text"])
            parts = nm.split()
            names.append((parts[-1], " ".join(parts[:-1])))
        out.append({"title": i.get("title", "").rstrip("."), "authors": names, "year": int(i.get("year", 0) or 0), "container": i.get("venue", ""),
                    "volume": i.get("volume", ""), "issue": "", "pages": i.get("pages", ""), "doi": i.get("doi", ""), "type": i.get("type", ""),
                    "publisher": "", "record": i.get("url", ""), "source": "DBLP", "ee": i.get("ee", "")})
    return out


def arxiv_id(title, fam):
    q = urllib.parse.urlencode({"search_query": f'ti:"{title}" AND au:{fam}', "max_results": 3})
    root = ET.fromstring(get(f"http://export.arxiv.org/api/query?{q}"))
    ns = {"a": "http://www.w3.org/2005/Atom"}
    for e in root.findall("a:entry", ns):
        t = " ".join(e.find("a:title", ns).text.split())
        if sim(t, title) >= 0.9:
            return e.find("a:id", ns).text.rsplit("/abs/", 1)[1], t
    return None, None


def arxiv_by_id(aid, title, fam):
    root = ET.fromstring(get(f"https://export.arxiv.org/api/query?id_list={aid}&max_results=1"))
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    e = root.find("a:entry", ns)
    if e is None:
        return None
    t = " ".join(e.find("a:title", ns).text.split())
    au = [" ".join(a.find("a:name", ns).text.split()) for a in e.findall("a:author", ns)]
    names = [(n.split()[-1], " ".join(n.split()[:-1])) for n in au]
    yr = int(e.find("a:published", ns).text[:4])
    jr = e.find("x:journal_ref", ns)
    doi = e.find("x:doi", ns)
    ok = sim(t, title) >= 0.90 and names and norm(fam) in norm(names[0][0])
    if not ok:
        return None
    return {"title": t, "authors": names, "year": yr, "container": "", "volume": "", "issue": "", "pages": "", "doi": doi.text if doi is not None else "",
            "type": "arxiv", "publisher": "", "record": f"https://arxiv.org/abs/{aid}", "source": "arXiv", "arxiv": aid,
            "journal_ref": " ".join(jr.text.split()) if jr is not None and jr.text else ""}


def accept(rec, title, fam, year):
    s = sim(rec["title"], title)
    first = norm(rec["authors"][0][0]) if rec["authors"] else ""
    ok_au = norm(fam) in first or first in norm(fam)
    ok_year = rec["year"] == year
    return s >= 0.90 and ok_au and ok_year, s, ok_au, ok_year


def bibtex_key(key, r):
    typ = "misc" if r["source"] == "arXiv" else "article"
    authors = " and ".join(f"{f}, {g}".strip(", ") for f, g in r["authors"])
    f = {"author": authors, "title": "{" + r["title"] + "}", "year": str(r["year"])}
    if typ == "misc":
        if r.get("journal_ref"):
            f["howpublished"] = r["journal_ref"]
    elif typ == "article":
        f["journal"] = r["container"]
        for k in ("volume", "issue", "pages"):
            if r.get(k):
                f["number" if k == "issue" else k] = r[k]
    else:
        pass
    if r.get("doi"):
        f["doi"] = r["doi"]
    if r.get("arxiv"):
        f["eprint"] = r["arxiv"]
        f["archivePrefix"] = "arXiv"
    f["note"] = f"Verified against {r['source']} record {r['record']} on {date.today().isoformat()}"
    return f"@{typ}{{{key},\n" + ",\n".join(f"  {k} = {{{v}}}" for k, v in f.items()) + "\n}\n"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    verified, failed = {}, []
    for key, title, fam, year, pref in CANDIDATES:
        recs, tried = [], []
        for idx in ("crossref",):
            try:
                recs = crossref(title, fam, year) if idx == "crossref" else dblp(title, fam, year)
            except Exception as e:  # noqa: BLE001
                tried.append(f"{idx}: error {type(e).__name__}")
                continue
            good = [(accept(r, title, fam, year), r) for r in recs]
            good = [(a, r) for a, r in good if a[0]]
            tried.append(f"{idx}: {len(recs)} records, {len(good)} accepted")
            if good:
                best = max(good, key=lambda x: x[0][1])[1]
                aid, at = arxiv_id(title, fam) if best["source"] == "DBLP" or not best.get("doi") else (None, None)
                if aid:
                    best["arxiv"] = aid
                verified[key] = best
                break
            time.sleep(1)
        else:
            pass
        if key not in verified:
            failed.append((key, title, fam, year, tried))
        print(("OK   " if key in verified else "FAIL ") + key, "|", (verified[key]["source"] + " " + verified[key].get("doi", "")) if key in verified else tried)
        time.sleep(0.7)
    for key, aid, title, fam in ARXIV:
        try:
            r = arxiv_by_id(aid, title, fam)
        except Exception as e:  # noqa: BLE001
            r = None
        if r:
            verified[key] = r
        else:
            failed.append((key, title, fam, "arXiv", [f"arXiv id {aid}: record not retrieved or not matching"]))
        print(("OK   " if r else "FAIL ") + key, "| arXiv", aid, (r or {}).get("journal_ref", ""))
        time.sleep(1)
    (OUT / "references.json").write_text(json.dumps(verified, indent=1))
    (OUT / "references.bib").write_text("% Generated by src/thesis/build_bib.py; every field is copied from the indexed record named in `note`.\n\n" +
                                        "\n".join(bibtex_key(k, v) for k, v in verified.items()))
    (OUT / "references_failed.json").write_text(json.dumps(failed, indent=1))
    print(len(verified), "verified;", len(failed), "unverified")


if __name__ == "__main__":
    main()
