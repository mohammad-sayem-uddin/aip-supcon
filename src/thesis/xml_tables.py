"""Dump table-wrap elements (label, caption, rows) of Europe PMC full-text XML to plain text for manual transcription."""
import sys, re
import xml.etree.ElementTree as ET
def txt(e): return re.sub(r"\s+", " ", "".join(e.itertext())).strip()
for f in sys.argv[1:]:
    root = ET.parse(f).getroot()
    print("=" * 30, f)
    for tw in root.iter("table-wrap"):
        lab = tw.find("label"); cap = tw.find("caption")
        print("\n--", txt(lab) if lab is not None else "?", "|", txt(cap)[:300] if cap is not None else "")
        for tr in tw.iter("tr"):
            print("   ", " | ".join(txt(c) for c in tr))
        foot = tw.find("table-wrap-foot")
        if foot is not None: print("   FOOT:", txt(foot)[:300])
