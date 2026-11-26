const fs = require('fs');
const { chapter, ROOT, THESIS, REFS } = require('./lib.js');
const L = chapter(6, 'REFERENCES', 'REFERENCES thesis.docx');
const cited = new Set();
// chapters 1-5 and both appendices (6 is this file); a source cited only in an appendix
// still belongs in the reference list
for (const i of [1, 2, 3, 4, 5, 7, 8]) {
  const f = `${THESIS}/meta_ch${i}.json`;
  if (!fs.existsSync(f)) continue;
  JSON.parse(fs.readFileSync(f, 'utf8')).cited.forEach((k) => cited.add(k));
}
const ini = (g) => g.split(/[\s.]+/).filter(Boolean).map((x) => x[0].toUpperCase() + '.').join(' ');
const fmtAuth = (a) => { const s = a.map(([f, g]) => (g ? `${f}, ${ini(g)}` : f)); return s.length === 1 ? s[0] : s.length <= 20 ? `${s.slice(0, -1).join(', ')}, & ${s[s.length - 1]}` : `${s.slice(0, 19).join(', ')}, ... ${s[s.length - 1]}`; };

// APA 7 asks for sentence case in article titles. The verified records in
// references.json keep each publisher's own capitalisation, so the conversion happens
// here, at render time, and the audit trail is left exactly as it was retrieved.
// A word is lowercased only when it is plainly an ordinary word: anything carrying an
// internal capital (BiTCNs, PyTorch, t-SNE), a digit (ESM-2, RDP58) or a place on the
// keep-list is left alone, and the word after a colon is capitalised again.
const KEEP = new Set(['Python', 'Bayesian', 'Gaussian', 'Markov', 'Monte', 'Carlo', 'English',
  'UniProt', 'UniRef', 'Microsoft', 'Daffodil', 'Benjamini', 'Hochberg', 'Hopkins', 'I']);
const KEEP_PHRASES = ['Global Burden of Disease'];
function sentenceCase(title) {
  let guarded = title;
  const stash = [];
  KEEP_PHRASES.forEach((p) => {
    if (guarded.includes(p)) { stash.push(p); guarded = guarded.replace(p, `\u0000${stash.length - 1}\u0000`); }
  });
  let newSentence = true;
  const out = guarded.split(/(:\s+)/).map((seg) => {
    if (/^:\s+$/.test(seg)) { newSentence = true; return seg; }
    return seg.split(/(\s+)/).map((w) => {
      if (/^\s*$/.test(w)) return w;
      const core = w.replace(/^[(\["']+/, '').replace(/[)\]"'.,;]+$/, '');
      const at = w.indexOf(core);
      const lead = at > 0 ? w.slice(0, at) : '';
      const tail = w.slice(lead.length + core.length);
      let res;
      if (newSentence) {
        // the opening word keeps its capital, but a hyphenated compound lowercases its tail
        res = /^[A-Z][a-z'\u2019]*(-[A-Z][a-z'\u2019]+)+$/.test(core)
          ? core.split('-').map((p, i) => (i === 0 || KEEP.has(p) ? p : p.charAt(0).toLowerCase() + p.slice(1))).join('-')
          : core;
        newSentence = false;
      }
      else if (KEEP.has(core)) res = core;
      // a plain capitalised word, possibly hyphenated with more plain words
      else if (/^[A-Z][a-z'\u2019]*(-[A-Z]?[a-z'\u2019]+)*$/.test(core)) {
        res = core.split('-').map((p) => (KEEP.has(p) ? p : p.charAt(0).toLowerCase() + p.slice(1))).join('-');
      } else res = core;      // acronyms, mixed case, anything with a digit
      return lead + res + tail;
    }).join('');
  }).join('');
  return out.replace(/\u0000(\d+)\u0000/g, (_, i) => stash[Number(i)]);
}

const keys = [...cited].filter((k) => REFS[k]).sort((a, b) => REFS[a].authors[0][0].localeCompare(REFS[b].authors[0][0]) || REFS[a].year - REFS[b].year);
L.add(L.H1('REFERENCES'));
for (const k of keys) {
  const r = REFS[k]; let t = `${fmtAuth(r.authors)} (${r.year}). ${sentenceCase(r.title.replace(/\.$/, ''))}.`;
  if (r.source === 'arXiv') t += ` <i>arXiv preprint</i> arXiv:${r.arxiv}. https://arxiv.org/abs/${r.arxiv}`;
  else if (r.type === 'inproceedings') {
    t += ` In <i>${r.container}</i>`;
    const neurips = r.volume && /Neural/.test(r.container);
    if (neurips) t += ` (Vol. ${r.volume}`; else if (r.volume) t += ` (PMLR ${r.volume}`;
    if (neurips || r.volume) { if (r.pages) t += `, pp. ${r.pages}`; t += ')'; }
    t += `. ${r.record}`;
  }
  else { t += r.container ? ` <i>${r.container}</i>` : ''; if (r.volume) t += `, <i>${r.volume}</i>`; if (r.issue) t += `(${r.issue})`; if (r.pages) t += `, ${r.pages}`; t += '.'; if (r.doi) t += ` https://doi.org/${r.doi}`; else if (r.source === 'publisher page') t += ` ${r.record}`; }
  L.add(L.P(t, { alignment: undefined, indent: { left: 720, hanging: 720 }, spacing: { after: 120, line: 240 } }));
}
L.add(L.P(`<i>${keys.length} entries, each matched to a CrossRef record or an arXiv record (results/thesis/references.json). Venue, volume and page fields are given only where the record has them. Items that could not be verified are listed in CITATIONS_TO_VERIFY.md and are not in this list.</i>`));
L.build();

module.exports = L;
