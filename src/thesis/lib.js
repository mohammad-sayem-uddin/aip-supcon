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
const BODY_FONT = 'Times New Roman';            // Guidelines p.11
const BODY_SIZE = 24;                           // 12 pt, in half-points
const CM = 566.93;                              // twips per cm
const PAGE = { width: Math.round(21 * CM), height: Math.round(29.7 * CM) };          // A4, Guidelines p.10
const MARGIN = { top: Math.round(2.5 * CM), bottom: Math.round(2.5 * CM),
                 right: Math.round(2.5 * CM), left: Math.round(4.0 * CM),            // Guidelines p.12
                 footer: Math.round(1.0 * CM) };                                     // page number 1 cm from the bottom
const TEXT_WIDTH = PAGE.width - MARGIN.left - MARGIN.right;
const LINE_DOUBLE = 480;                        // 240 = single; Guidelines: double for body text
const LINE_SINGLE = 240;                        // tables, captions, references
const INDENT_FIRST = 720;                       // first-line indent, as the template sets it

// Where the page number sits. The Guidelines say bottom centre; the approved demo.pdf
// puts it bottom right with the copyright notice on the left. Guidelines win by default.
const PAGE_NUMBER_POSITION = 'centre';          // 'centre' (Guidelines) | 'right' (demo.pdf)
const FOOTER_TEXT = '\u00A9Daffodil International University';

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

// words, as a plain-text reader would count them: tags stripped, whitespace collapsed
const wcount = (x) => String(x).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().split(' ').filter(Boolean).length;

const RULE = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
const NONE = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
// Guidelines p.14 / template p.18: horizontal rules only - a rule above the header,
// one below it and one under the last row. No vertical rules anywhere.
const cellBorders = (ri, last) => ({
  top: ri === 0 ? RULE : NONE,
  bottom: (ri === 0 || ri === last) ? RULE : NONE,
  left: NONE, right: NONE,
});

// Footer: the copyright notice sits on the left on every page (demo.pdf); the page
// number sits where PAGE_NUMBER_POSITION says. Both are inside one paragraph so the
// footer is a single line 1 cm from the bottom edge.
function footerParagraph() {
  // the Guidelines say the centre of the PAGE; the left margin (4 cm) is wider than
  // the right (2.5 cm), so the page centre is not the centre of the text block
  const centreTab = Math.round(PAGE.width / 2 - MARGIN.left);
  const rightTab = TEXT_WIDTH;
  const num = new TextRun({ children: [PageNumber.CURRENT], font: BODY_FONT, size: BODY_SIZE });
  if (PAGE_NUMBER_POSITION === 'right') {
    return new Paragraph({
      tabStops: [{ type: TabStopType.RIGHT, position: rightTab }],
      spacing: { after: 0, line: LINE_SINGLE },
      children: [new TextRun({ text: FOOTER_TEXT, font: BODY_FONT, size: BODY_SIZE }), new TextRun({ text: '\t' }), num],
    });
  }
  return new Paragraph({
    tabStops: [{ type: TabStopType.CENTER, position: centreTab }, { type: TabStopType.RIGHT, position: rightTab }],
    spacing: { after: 0, line: LINE_SINGLE },
    children: [new TextRun({ text: FOOTER_TEXT, font: BODY_FONT, size: BODY_SIZE }), new TextRun({ text: '\t' }), num],
  });
}

function chapter(no, title, outFile, opts = {}) {
  const NUM = opts.numberAs || no;   // appendices number as A.1, B.1 ...
  const ctx = { todos: [], needed: [], used: new Set(), unresolved: [], labels: [], wc: { prose: 0, heading: 0, caption: 0, table: 0, equation: 0 } };
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
    P(str, opts = {}) {
      ctx.wc.prose += wcount(str);
      return new Paragraph({
        children: rich(str, {}, ctx),
        alignment: AlignmentType.JUSTIFIED,
        indent: { firstLine: INDENT_FIRST },
        spacing: { after: 0, line: LINE_DOUBLE },
        widowControl: true,                    // a new paragraph keeps at least 2 lines on a page
        ...opts,
      });
    },
    H1: (t) => {
      ctx.wc.heading += wcount(t);
      const [head, ...rest] = String(t).split(': ');
      const line = (txt, after) => new Paragraph({
        heading: HeadingLevel.HEADING_1, alignment: AlignmentType.CENTER, keepNext: true,
        children: [new TextRun({ text: txt, font: BODY_FONT, bold: true, size: BODY_SIZE, color: '000000' })],
        spacing: { before: 0, after, line: LINE_DOUBLE },
      });
      return rest.length ? [line(head, 480), line(rest.join(': '), 720)] : [line(head, 720)];
    },
    H2: (t) => (ctx.wc.heading += wcount(t), new Paragraph({
      heading: HeadingLevel.HEADING_2, keepNext: true,
      children: [new TextRun({ text: String(t).replace(/^(\d[\d.]*)\s+/, '$1\t'), font: BODY_FONT, bold: true, size: BODY_SIZE, color: '000000' })],
      tabStops: [{ type: TabStopType.LEFT, position: INDENT_FIRST }],
      spacing: { before: 240, after: 120, line: LINE_DOUBLE },
    })),
    H3: (t) => (ctx.wc.heading += wcount(t), new Paragraph({
      heading: HeadingLevel.HEADING_3, keepNext: true,
      children: [new TextRun({ text: String(t).replace(/^(\d[\d.]*)\s+/, '$1\t'), font: BODY_FONT, bold: true, size: BODY_SIZE, color: '000000' })],
      tabStops: [{ type: TabStopType.LEFT, position: INDENT_FIRST }],
      spacing: { before: 240, after: 120, line: LINE_DOUBLE },
    })),
    pageBreak: () => new Paragraph({ children: [new PageBreak()] }),
    table(rows, widths, opts = {}) {
      let tw = 0; rows.forEach((r) => r.forEach((c) => { tw += wcount(c); }));
      ctx.wc.table += tw;
      if (ctx.captions && ctx.captions.length) { const last = ctx.captions[ctx.captions.length - 1]; last.tableWords = (last.tableWords || 0) + tw; }
      const fs_ = opts.size || 18;
      // the column widths were written for the old page size; scale any table that no
      // longer fits between the 4 cm and 2.5 cm margins, keeping the proportions
      let total = widths.reduce((a, b) => a + b, 0);
      if (total > TEXT_WIDTH) {
        const MINW = 820;                       // ~1.45 cm: fits labels like 'Ind_1049' at the table font size
        const k = TEXT_WIDTH / total;
        widths = widths.map((w) => Math.max(MINW, Math.floor(w * k)));
        // the minimum may push the table back over the text width; take the excess off
        // the widest column, which is the one with room to give
        let over = widths.reduce((a, b) => a + b, 0) - TEXT_WIDTH;
        while (over > 0) {
          const i = widths.indexOf(Math.max(...widths));
          const take = Math.min(over, widths[i] - MINW);
          if (take <= 0) break;
          widths[i] -= take; over -= take;
        }
        widths[widths.indexOf(Math.max(...widths))] -= widths.reduce((a, b) => a + b, 0) - TEXT_WIDTH;
        total = TEXT_WIDTH;
      }
      return new Table({
        width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
        rows: rows.map((r, ri) => new TableRow({
          tableHeader: ri === 0, cantSplit: true,
          children: r.map((c, ci) => new TableCell({
            borders: cellBorders(ri, rows.length - 1), width: { size: widths[ci], type: WidthType.DXA },
            shading: ri === 0 ? { fill: 'E7E6E6', type: ShadingType.CLEAR, color: 'auto' } : (opts.boldLast && ri === rows.length - 1 ? { fill: 'F3F3F3', type: ShadingType.CLEAR, color: 'auto' } : (opts.shadeRows && opts.shadeRows.includes(ri) ? { fill: 'F7F7F7', type: ShadingType.CLEAR, color: 'auto' } : undefined)),
            margins: { top: 50, bottom: 50, left: 90, right: 90 },
            children: [new Paragraph({ spacing: { after: 0, line: LINE_SINGLE }, alignment: (opts.right && opts.right.includes(ci) && ri > 0) ? AlignmentType.RIGHT : AlignmentType.LEFT,
              children: rich(String(c), { size: fs_, bold: ri === 0 || (opts.boldLast && ri === rows.length - 1), font: BODY_FONT }, ctx) })],
          })),
        })),
      });
    },
    caption(label, text) {
      tabNo += 1; ctx.wc.caption += wcount(text); ctx.labels.push([label, `Table ${NUM}.${tabNo}`]);
      ctx.captions = ctx.captions || []; ctx.captions.push({ label, kind: 'Table', number: `${NUM}.${tabNo}`, text, captionWords: wcount(text) });
      return new Paragraph({
        keepNext: true, spacing: { before: 240, after: 120, line: LINE_SINGLE },
        tabStops: [{ type: TabStopType.LEFT, position: INDENT_FIRST + 360 }],
        children: [new TextRun({ text: `Table ${NUM}.${tabNo}\t`, font: BODY_FONT, size: BODY_SIZE }),
                   ...rich(text, { font: BODY_FONT, size: BODY_SIZE }, ctx)],
      });
    },
    afterTable: () => new Paragraph({ spacing: { after: 120 }, children: [] }),
    figure(label, file, text, widthPx) {
      const b = fs.readFileSync(`${ROOT}/figures/${file}`);
      const w = b.readUInt32BE(16), h = b.readUInt32BE(20);
      figNo += 1; ctx.wc.caption += wcount(text); ctx.labels.push([label, `Figure ${NUM}.${figNo}`]);
      ctx.captions = ctx.captions || []; ctx.captions.push({ label, kind: 'Figure', number: `${NUM}.${figNo}`, text, captionWords: wcount(text) });
      return [
        new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 0, line: LINE_SINGLE }, keepNext: true,
          children: [new ImageRun({ type: 'png', data: b, transformation: (() => {
            const maxPx = Math.floor(TEXT_WIDTH / 1440 * 96);
            const px = Math.min(widthPx, maxPx);
            return { width: px, height: Math.round(px * h / w) };
          })(), altText: { title: `Figure ${NUM}.${figNo}`, description: text, name: file } })] }),
        new Paragraph({ spacing: { after: 0, line: LINE_SINGLE }, children: [] }),   // the one blank line the Guidelines require
        new Paragraph({
          spacing: { before: 0, after: 240, line: LINE_SINGLE },
          tabStops: [{ type: TabStopType.LEFT, position: INDENT_FIRST + 360 }],
          children: [new TextRun({ text: `Figure ${NUM}.${figNo}\t`, font: BODY_FONT, size: BODY_SIZE }),
                     ...rich(text, { font: BODY_FONT, size: BODY_SIZE }, ctx)],
        }),
      ];
    },
    async build() {
      const doc = new Document({
        creator: 'AIP thesis', title,
        styles: { default: { document: { run: { font: BODY_FONT, size: BODY_SIZE } } } },
        sections: [{
          properties: { page: { size: { width: PAGE.width, height: PAGE.height }, margin: MARGIN } },
          footers: { default: new Footer({ children: [footerParagraph()] }) },
          children: out,
        }],
      });
      fs.writeFileSync(`${ROOT}/${outFile}`, await Packer.toBuffer(doc));
      fs.writeFileSync(`${THESIS}/labels_ch${no}.csv`, 'label,number\n' + ctx.labels.map((l) => l.join(',')).join('\n') + '\n');
      fs.writeFileSync(`${THESIS}/meta_ch${no}.json`, JSON.stringify({ file: outFile, cited: [...ctx.used], todos: ctx.todos, citation_needed: ctx.needed, unresolved_refs: [...new Set(ctx.unresolved)], tables: tabNo, figures: figNo, words: ctx.wc }, null, 1));
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
  eqPara: (numberText, ...children) => new Paragraph({ spacing: { before: 240, after: 240, line: LINE_SINGLE }, tabStops: [{ type: TabStopType.CENTER, position: Math.round(TEXT_WIDTH / 2) }, { type: TabStopType.RIGHT, position: TEXT_WIDTH }],
    children: [new TextRun('\t'), new DMath({ children }), new TextRun(`\t${numberText}`)] }),
};

module.exports = { chapter, M, ROOT, THESIS, REFS, D };
