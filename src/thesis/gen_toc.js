// Builds results/thesis/toc.json from what the chapters actually emitted, so the
// Table of Content and the lists cannot drift from the document. Run after a build pass.
const fs = require('fs');
const { THESIS } = require('./lib.js');

const read = (i) => JSON.parse(fs.readFileSync(`${THESIS}/meta_ch${i}.json`, 'utf8'));
const caps = (i) => (fs.existsSync(`${THESIS}/captions_ch${i}.json`) ? JSON.parse(fs.readFileSync(`${THESIS}/captions_ch${i}.json`, 'utf8')) : []);

// front matter, in the order the template sets
const front = [
  ['DECLARATION OF THESIS AND COPYRIGHT', 'Front:declaration'],
  ["SUPERVISOR'S DECLARATION", 'Front:supervisor'],
  ["STUDENT'S DECLARATION", 'Front:student'],
  ['TITLE PAGE', 'Front:title'],
  ['ACKNOWLEDGEMENTS', 'Front:ack'],
  ['DEDICATION', 'Front:dedication'],
  ['ABSTRACT', 'Front:abstract'],
  ['TABLE OF CONTENT', 'Front:toc'],
  ['LIST OF TABLES', 'Front:lot'],
  ['LIST OF FIGURES', 'Front:lof'],
  ['LIST OF SYMBOLS', 'Front:los'],
  ['LIST OF ABBREVIATIONS', 'Front:loa'],
  ['LIST OF APPENDICES', 'Front:loap'],
].map(([title, key]) => ({ title, key }));

// body: chapters 1-5, then references, then the appendices
const body = [];
for (const i of [1, 2, 3, 4, 5]) {
  for (const h of read(i).headings) {
    const title = h.level === 1 ? h.text.replace(':', '') : h.text;
    body.push({ level: h.level, title, key: `H:${h.text}` });
  }
}
body.push({ level: 1, title: 'REFERENCES', key: 'H:REFERENCES' });
for (const [i, name] of [[7, 'APPENDIX A: DETAILED RESULTS'], [8, 'APPENDIX B: MODEL AND IMPLEMENTATION DETAIL']]) {
  body.push({ level: 1, title: name.replace(':', ''), key: `H:${name}` });
}

// every table and figure, in document order, for the two lists
const captions = [];
for (const i of [1, 2, 3, 4, 5, 7, 8]) {
  for (const c of caps(i)) {
    // the lists carry a short title: the caption up to its first full stop
    const m = /^(.+?\.)(\s|$)/.exec(c.text);
    let short = (m ? m[1] : c.text).replace(/\s+/g, ' ').trim();
    if (short.length > 95) short = short.slice(0, 92).replace(/\s+\S*$/, '') + '...';
    captions.push({ kind: c.kind, number: c.number, short, label: c.label });
  }
}

fs.writeFileSync(`${THESIS}/toc.json`, JSON.stringify({ front, body, captions }, null, 1));
console.log(`toc.json: ${front.length} front entries, ${body.length} headings, ` +
  `${captions.filter((c) => c.kind === 'Table').length} tables, ${captions.filter((c) => c.kind === 'Figure').length} figures`);
