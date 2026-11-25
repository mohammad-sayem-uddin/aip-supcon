// Shared helpers for building the thesis chapters (.docx) with docx-js.
// Run with NODE_PATH pointing at a directory that contains the `docx` package.
const fs = require('fs');
const path = require('path');
const D = require('docx');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, AlignmentType,
  ImageRun, TabStopType, PageNumber, Footer, PageBreak,
} = D;

const ROOT = '/Users/sayemuddin/Desktop/Yassir_Thesis';
const THESIS = `${ROOT}/results/thesis`;
fs.mkdirSync(THESIS, { recursive: true });
const BODY_FONT = 'Calibri';

// ------------------------------------------------------------------ references (verified bibliography only)
const REFS = JSON.parse(fs.readFileSync(`${THESIS}/references.json`, 'utf8'));
const fam = (k) => REFS[k].authors.map((a) => a[0]);
function citeText(k, narrative) {
  if (!REFS[k]) return null;
  const f = fam(k), y = REFS[k].year;
  const who = f.length === 1 ? f[0] : f.length === 2 ? `${f[0]} and ${f[1]}` : `${f[0]} et al.`;
  return narrative ? `${who} (${y})` : `${who}, ${y}`;
}

// ------------------------------------------------------------------ labels across chapters
function loadLabels() {
  const m = {};
  for (const f of fs.readdirSync(THESIS)) {
    if (/^labels_ch\d+\.csv$/.test(f)) {
      fs.readFileSync(`${THESIS}/${f}`, 'utf8').split('\n').slice(1).forEach((l) => { const [a, b] = l.split(','); if (a) m[a] = b; });
    }
  }
  return m;
}

function rich(str, base, ctx) {
  const out = [];
  const re = /<(i|b|sub|sup|todo|cn)>(.*?)<\/\1>/gs;
  let last = 0, m;
  while ((m = re.exec(str)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: str.slice(last, m.index), ...base }));
    const o = { text: m[2], ...base };
    if (m[1] === 'i') o.italics = true;
    if (m[1] === 'b') o.bold = true;
    if (m[1] === 'sub') o.subScript = true;
    if (m[1] === 'sup') o.superScript = true;
    if (m[1] === 'todo') { o.highlight = 'yellow'; o.bold = true; o.text = `[TODO: ${m[2]}]`; ctx.todos.push(m[2]); }
    if (m[1] === 'cn') { o.highlight = 'yellow'; o.bold = true; o.text = '[CITATION NEEDED]'; ctx.needed.push(m[2]); }
    out.push(new TextRun(o));
    last = m.index + m[0].length;
  }
  if (last < str.length) out.push(new TextRun({ text: str.slice(last), ...base }));
  // highlight any [CITATION NEEDED] marker
  return out.flatMap((r) => r);
}

const border = { style: BorderStyle.SINGLE, size: 4, color: '808080' };
const borders = { top: border, bottom: border, left: border, right: border };

function chapter(no, title, outFile) {
  const ctx = { todos: [], needed: [], used: new Set(), unresolved: [], labels: [] };
  const LABELS = loadLabels();
  const out = [];
  let tabNo = 0, figNo = 0;
  const api = {
    ctx, out, no,
    add: (...x) => x.flat().forEach((e) => out.push(e)),
    n: (x) => Number(x).toLocaleString('en-US'),
    pct: (x, d = 1) => `${(100 * x).toFixed(d)}%`,
    ref(label) {
      const v = LABELS[label];
      if (!v) { ctx.unresolved.push(label); return '??'; }
      return v.replace(/^(Table|Figure) /, '');
    },
    cit(...keys) {
      const parts = keys.map((k) => { const t = citeText(k, false); if (!t) { ctx.needed.push(`unknown key ${k}`); return 'CITATION NEEDED'; } ctx.used.add(k); return t; });
      return `(${parts.join('; ')})`;
    },
    citN(k) { const t = citeText(k, true); if (!t) { ctx.needed.push(`unknown key ${k}`); return '[CITATION NEEDED]'; } ctx.used.add(k); return t; },
    needed(note) { return `<cn>${note}</cn>`; },
    P(str, opts = {}) { return new Paragraph({ children: rich(str, {}, ctx), spacing: { after: 160, line: 259 }, ...opts }); },
    H1: (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: 'Times New Roman', bold: true, size: 48, color: '000000' })], spacing: { before: 0, after: 240 }, keepNext: true }),
    H2: (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: 'Times New Roman', bold: true, size: 36, color: '000000' })], spacing: { before: 360, after: 160 }, keepNext: true }),
    H3: (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t, font: 'Times New Roman', bold: true, size: 28, color: '000000' })], spacing: { before: 240, after: 120 }, keepNext: true }),
    pageBreak: () => new Paragraph({ children: [new PageBreak()] }),
    table(rows, widths, opts = {}) {
      const fs_ = opts.size || 18;
      const total = widths.reduce((a, b) => a + b, 0);
      return new Table({
        width: { size: total, type: WidthType.DXA }, columnWidths: widths,
        rows: rows.map((r, ri) => new TableRow({
          tableHeader: ri === 0, cantSplit: true,
          children: r.map((c, ci) => new TableCell({
            borders, width: { size: widths[ci], type: WidthType.DXA },
            shading: ri === 0 ? { fill: 'E7E6E6', type: ShadingType.CLEAR, color: 'auto' } : (opts.boldLast && ri === rows.length - 1 ? { fill: 'F3F3F3', type: ShadingType.CLEAR, color: 'auto' } : (opts.shadeRows && opts.shadeRows.includes(ri) ? { fill: 'F7F7F7', type: ShadingType.CLEAR, color: 'auto' } : undefined)),
            margins: { top: 50, bottom: 50, left: 90, right: 90 },
            children: [new Paragraph({ spacing: { after: 0, line: 240 }, alignment: (opts.right && opts.right.includes(ci) && ri > 0) ? AlignmentType.RIGHT : AlignmentType.LEFT,
              children: rich(String(c), { size: fs_, bold: ri === 0 || (opts.boldLast && ri === rows.length - 1), font: BODY_FONT }, ctx) })],
          })),
        })),
      });
    },
    caption(label, text) {
      tabNo += 1; ctx.labels.push([label, `Table ${no}.${tabNo}`]);
      ctx.captions = ctx.captions || []; ctx.captions.push({ label, kind: 'Table', number: `${no}.${tabNo}`, text });
      return new Paragraph({ keepNext: true, spacing: { before: 200, after: 80 }, children: [new TextRun({ text: `Table ${no}.${tabNo}: `, bold: true, size: 20 }), ...rich(text, { size: 20 }, ctx)] });
    },
    afterTable: () => new Paragraph({ spacing: { after: 120 }, children: [] }),
    figure(label, file, text, widthPx) {
      const b = fs.readFileSync(`${ROOT}/figures/${file}`);
      const w = b.readUInt32BE(16), h = b.readUInt32BE(20);
      figNo += 1; ctx.labels.push([label, `Figure ${no}.${figNo}`]);
      ctx.captions = ctx.captions || []; ctx.captions.push({ label, kind: 'Figure', number: `${no}.${figNo}`, text });
      return [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 160, after: 60 }, keepNext: true,
          children: [new ImageRun({ type: 'png', data: b, transformation: { width: widthPx, height: Math.round(widthPx * h / w) }, altText: { title: `Figure ${no}.${figNo}`, description: text, name: file } })] }),
        new Paragraph({ spacing: { after: 200 }, children: [new TextRun({ text: `Figure ${no}.${figNo}: `, bold: true, size: 20 }), ...rich(text, { size: 20 }, ctx)] }),
      ];
    },
    async build() {
      const doc = new Document({
        creator: 'AIP thesis', title,
        styles: { default: { document: { run: { font: BODY_FONT, size: 22 } } } },
        sections: [{
          properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
          footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }) },
          children: out,
        }],
      });
      fs.writeFileSync(`${ROOT}/${outFile}`, await Packer.toBuffer(doc));
      fs.writeFileSync(`${THESIS}/labels_ch${no}.csv`, 'label,number\n' + ctx.labels.map((l) => l.join(',')).join('\n') + '\n');
      fs.writeFileSync(`${THESIS}/meta_ch${no}.json`, JSON.stringify({ file: outFile, cited: [...ctx.used], todos: ctx.todos, citation_needed: ctx.needed, unresolved_refs: [...new Set(ctx.unresolved)], tables: tabNo, figures: figNo }, null, 1));
      fs.writeFileSync(`${THESIS}/captions_ch${no}.json`, JSON.stringify(ctx.captions || [], null, 1));
      console.log(`ch${no}: ${outFile} tables ${tabNo} figures ${figNo} cited ${ctx.used.size} todos ${ctx.todos.length} needed ${ctx.needed.length} unresolved ${[...new Set(ctx.unresolved)].length}`);
    },
  };
  return api;
}

// ------------------------------------------------------------------ equations
const { Math: DMath, MathRun, MathFraction, MathSum, MathSubScript, MathSuperScript, MathRadical, MathRoundBrackets, MathSquareBrackets, MathFunction, MathSubSuperScript } = D;
const M = {
  R: (t) => new MathRun(t),
  sub: (b, s) => new MathSubScript({ children: [new MathRun(b)], subScript: [new MathRun(s)] }),
  sup: (b, s) => new MathSuperScript({ children: [new MathRun(b)], superScript: [new MathRun(s)] }),
  subsup: (b, s, p) => new MathSubSuperScript({ children: [new MathRun(b)], subScript: [new MathRun(s)], superScript: [new MathRun(p)] }),
  frac: (a, b) => new MathFraction({ numerator: a, denominator: b }),
  fn: (name, args) => new MathFunction({ name: [new MathRun(name)], children: args }),
  par: (...c) => new MathRoundBrackets({ children: c }),
  sq: (...c) => new MathSquareBrackets({ children: c }),
  sum: (lo, hi, ...body) => new MathSum({ children: body, subScript: lo, ...(hi ? { superScript: hi } : {}) }),
  rad: (c) => new MathRadical({ children: c }),
  eqPara: (numberText, ...children) => new Paragraph({ spacing: { before: 120, after: 160 }, tabStops: [{ type: TabStopType.CENTER, position: 4680 }, { type: TabStopType.RIGHT, position: 9360 }],
    children: [new TextRun('\t'), new DMath({ children }), new TextRun(`\t${numberText}`)] }),
};

module.exports = { chapter, M, ROOT, THESIS, REFS, D };
