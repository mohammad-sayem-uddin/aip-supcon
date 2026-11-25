"""Second pass of the bibliography (completion run).

Adds generic method references and upgrades arXiv-only entries to their published venue. A published-venue record is used only if the
publisher's own page (NeurIPS proceedings, PMLR or JMLR) can be fetched and is parsed for the title, authors, volume and pages; the
OpenAlex index is used only to find the proceedings URL. Journal articles with DOIs come from CrossRef (title similarity >= 0.90,
first author and year agree). ICLR papers could not be verified at the publisher (OpenReview blocks automated access) and stay arXiv
preprints. Nothing is guessed; failures go to results/thesis/references_failed2.json.
"""
from __future__ import annotations
import json, re, sys, time, urllib.parse, html
sys.path.insert(0, ".")
from src.thesis.build_bib import crossref, accept, get, norm, sim, bibtex_key, arxiv_by_id, OUT

def oa_urls(title, fam):
    q = urllib.parse.urlencode({"search": title, "per-page": 6, "select": "title,publication_year,authorships,primary_location,locations"})
    out = []
    for w in json.loads(get(f"https://api.openalex.org/works?{q}"))["results"]:
        if sim(w["title"], title) < 0.9 or not w["authorships"] or fam.lower() not in w["authorships"][0]["author"]["display_name"].lower(): continue
        for loc in [w.get("primary_location") or {}] + (w.get("locations") or []):
            u = loc.get("landing_page_url") or ""
            if re.match(r"https?://(proceedings\.neurips\.cc|proceedings\.mlr\.press|jmlr\.org)", u): out.append(u)
    return out
def text(url):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", get(url).decode("utf8", "ignore"))))
def names(s):
    out = []
    for n in [x.strip() for x in re.split(r",|\band\b", s) if x.strip()]:
        p = n.split(); i = len(p) - 1
        while i > 0 and p[i - 1].lower() in {"van", "der", "de", "von", "den"}: i -= 1
        out.append((" ".join(p[i:]), " ".join(p[:i])))
    return out

# key, title, first-author family, year of the published version, direct URL (a lookup key; the page content is what is verified) or None
PUBLISHED = [
    ("ke2017", "LightGBM: A Highly Efficient Gradient Boosting Decision Tree", "Ke", 2017, None),
    ("khosla2020", "Supervised Contrastive Learning", "Khosla", 2020, None),
    ("vaswani2017", "Attention Is All You Need", "Vaswani", 2017, None),
    ("paszke2019", "PyTorch: An Imperative Style, High-Performance Deep Learning Library", "Paszke", 2019, None),
    ("ilse2018", "Attention-based Deep Multiple Instance Learning", "Ilse", 2018, None),
    ("ioffe2015", "Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift", "Ioffe", 2015, None),
    ("pedregosa2012", "Scikit-learn: Machine Learning in Python", "Pedregosa", 2011, "https://jmlr.org/papers/v12/pedregosa11a.html"),
    ("srivastava2014", "Dropout: A Simple Way to Prevent Neural Networks from Overfitting", "Srivastava", 2014, "https://jmlr.org/papers/v15/srivastava14a.html"),
    ("vandermaaten2008", "Visualizing Data using t-SNE", "van der Maaten", 2008, "https://jmlr.org/papers/v9/vandermaaten08a.html"),
]
CROSSREF = [("breiman2001", "Random Forests", "Breiman", 2001), ("cortes1995", "Support-vector networks", "Cortes", 1995),
            ("zhao2021", "iAIPs: Identifying Anti-Inflammatory Peptides Using Random Forest", "Zhao", 2021),
            ("zhang2021", "AIEpred: An Ensemble Predictive Model of Classifier Chain to Identify Anti-Inflammatory Peptides", "Zhang", 2021),
            ("gaffar2024", "IF-AIP: A machine learning method for the identification of anti-inflammatory peptides using multi-feature fusion strategy", "Gaffar", 2024),
            ("wang2026", "AIPFusion-Net: an interaction-fusion framework for anti-inflammatory peptide prediction using protein language model embeddings, local sequence patterns, and handcrafted descriptors", "Wang", 2026),
            ("delgado2001", "Vasoactive intestinal peptide prevents experimental arthritis by downregulating both autoimmune and inflammatory components of the disease", "Delgado", 2001),
            ("gonzalez2005", "Modulating bladder neuro-inflammation: RDP58, a novel anti-inflammatory peptide, decreases inflammation and nerve growth factor production in experimental cystitis", "Gonzalez", 2005)]

def parse(url, title, fam, year):
    t = text(url).replace("\xa0", " ")
    spots = [m.end() for m in re.finditer(re.escape(title).replace(r"\ ", r"\s+"), t, re.I)]
    if not spots: return None, "title not on page"
    why = "no citation line"
    for e in spots:
        rest = t[e:e + 700]
        rec = {"title": title, "year": year, "doi": "", "issue": "", "pages": "", "volume": "", "record": url, "source": "publisher page", "type": "inproceedings"}
        if "neurips.cc" in url:
            m = re.match(r"\s*(.+?)\s+(Advances in Neural Information Processing Systems (\d+)) \(", rest)
            if m: rec.update(authors=names(m.group(1)), container="Advances in Neural Information Processing Systems", volume=m.group(3))
        elif "mlr.press" in url:
            m = re.match(r"\s*(.+?)\s+(Proceedings of the [^,]+?)\s*,\s*PMLR (\d+):(\d+)-(\d+), (\d{4})", rest)
            if m: rec.update(authors=names(m.group(1)), container=m.group(2), volume=m.group(3), pages=f"{m.group(4)}-{m.group(5)}", year=int(m.group(6)))
        else:
            m = re.match(r"\s*(.+?)\s*;\s*(\d+)\((\d+)\):\s*(\d+)\W+(\d+),\s*(\d{4})", rest)
            if m: rec.update(authors=names(m.group(1)), container="Journal of Machine Learning Research", volume=m.group(2), issue=m.group(3), pages=f"{m.group(4)}-{m.group(5)}", type="article", year=int(m.group(6)))
        if not m: continue
        if not rec["authors"] or norm(fam) not in norm(rec["authors"][0][0]): why = "first author mismatch"; continue
        if rec["year"] != year: why = f"year {rec['year']} != {year}"; continue
        return rec, "ok"
    return None, why

def main():
    R = json.loads((OUT / "references.json").read_text()); failed = []
    for key, title, fam, year, url in PUBLISHED:
        urls = [url] if url else oa_urls(title, fam)
        rec = None; why = "no proceedings URL found"
        for u in urls:
            try: rec, why = parse(u, title, fam, year)
            except Exception as e: rec, why = None, f"{u}: {type(e).__name__}"
            if rec: break
        if rec:
            if R.get(key, {}).get("arxiv"): rec["arxiv"] = R[key]["arxiv"]
            R[key] = rec; print("OK  ", key, rec["container"], rec["volume"], rec["pages"], rec["year"], rec["record"], "|", len(rec["authors"]), "authors")
        else: failed.append((key, why)); print("FAIL", key, why)
        time.sleep(0.8)
    for key, title, fam, year in CROSSREF:
        good = [r for a, r in [(accept(r, title, fam, year), r) for r in crossref(title, fam, year)] if a[0]]
        if good: R[key] = min(good, key=lambda r: len(r["title"])); print("OK  ", key, "CrossRef", R[key]["doi"], R[key]["container"], R[key]["volume"], R[key]["pages"])
        else: failed.append((key, "no CrossRef match"))
    r = arxiv_by_id("1608.03983", "SGDR: Stochastic Gradient Descent with Warm Restarts", "Loshchilov")
    if r: R["loshchilov2016"] = r; print("OK   loshchilov2016 (arXiv preprint)")
    else: failed.append(("loshchilov2016", "arXiv record did not match"))
    failed.append(("loshchilov2017", "ICLR 2019 version not verifiable: OpenReview blocks automated access; kept as the arXiv preprint"))
    (OUT / "references.json").write_text(json.dumps(R, indent=1)); (OUT / "references_failed2.json").write_text(json.dumps(failed, indent=1))
    bib = []
    for k, v in R.items():
        if v["source"] == "publisher page":
            f = {"author": " and ".join(f"{a}, {b}" for a, b in v["authors"]), "title": "{" + v["title"] + "}", "year": str(v["year"])}
            f["journal" if v["type"] == "article" else "booktitle"] = v["container"]
            for a in ("volume", "issue", "pages"):
                if v.get(a): f["number" if a == "issue" else a] = v[a]
            f["url"] = v["record"]; f["note"] = "Verified against the publisher page on 2026-11-26"
            bib.append(f"@{'article' if v['type']=='article' else 'inproceedings'}{{{k},\n" + ",\n".join(f"  {a} = {{{b}}}" for a, b in f.items()) + "\n}\n")
        else: bib.append(bibtex_key(k, v))
    (OUT / "references.bib").write_text("\n".join(bib)); print("failed/notes:", failed)
main()
