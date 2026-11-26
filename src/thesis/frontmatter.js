// Front matter, laid out to SWE_Thesis_Template_2024.pdf, with the logo and the
// signature blocks placed as demo.pdf places them. Items the author must supply are
// left as explicit [PLACEHOLDERS]; nothing here is invented.
const fs = require('fs');
const { chapter, ROOT, THESIS, D, BODY_FONT, BODY_SIZE, LINE_SINGLE, LINE_DOUBLE, TEXT_WIDTH, INDENT_FIRST } = require('./lib.js');
const { Paragraph, TextRun, AlignmentType, TabStopType, ImageRun, Table, TableRow, TableCell, WidthType, BorderStyle, ShadingType, PageBreak } = D;

const AUTHOR = 'Mohammad Sayem Uddin';
const DEGREE = 'Bachelor of Science';
const DEPARTMENT = 'Department of Software Engineering';
const UNIVERSITY = 'DAFFODIL INTERNATIONAL UNIVERSITY';
const PH = {
  title: '[THESIS TITLE]', id: '[STUDENT ID]', session: '[ACADEMIC SESSION]',
  date: '[SUBMISSION MONTH YEAR]', supervisor: '[SUPERVISOR FULL NAME]',
  position: '[SUPERVISOR POSITION]', dob: '[DATE OF BIRTH]',
};

const L = chapter(-1, 'FRONT MATTER', 'FRONT MATTER thesis.docx', { numberAs: 'i' });
const { add } = L;

// page numbers for the Table of Content and the lists; written by scripts/paginate.js
// after the thesis has been rendered once. Missing -> a dash, never a guessed number.
const PAGEMAP = fs.existsSync(`${THESIS}/pagemap.json`) ? JSON.parse(fs.readFileSync(`${THESIS}/pagemap.json`, 'utf8')) : {};
const pageOf = (key) => (PAGEMAP[key] === undefined ? '—' : String(PAGEMAP[key]));

// ---------------------------------------------------------------- helpers
const line = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.CENTER,
  spacing: { before: o.before || 0, after: o.after === undefined ? 0 : o.after, line: o.line || LINE_SINGLE },
  indent: o.indent,
  children: [new TextRun({ text, font: BODY_FONT, size: o.size || BODY_SIZE, bold: !!o.bold, allCaps: !!o.caps })],
});
const blank = (n = 1) => Array.from({ length: n }, () => line(''));
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const logo = () => {
  const b = fs.readFileSync(`${ROOT}/figures/assets/diu_logo.png`);
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new ImageRun({ type: 'png', data: b, transformation: { width: 90, height: 90 },
      altText: { title: 'Daffodil International University', description: 'University crest', name: 'diu_logo' } })] });
};
// "label : value" rows with the colons aligned, as the template sets them
const field = (label, value, labelWidth = 2400) => new Paragraph({
  spacing: { after: 120, line: LINE_SINGLE },
  tabStops: [{ type: TabStopType.LEFT, position: labelWidth }, { type: TabStopType.LEFT, position: labelWidth + 300 }],
  children: [new TextRun({ text: `${label}\t:\t${value}`, font: BODY_FONT, size: BODY_SIZE })],
});
const signature = (caption) => [
  line('_______________________________', { align: AlignmentType.LEFT, before: 480 }),
  line(caption, { align: AlignmentType.LEFT, after: 240 }),
];
// a dot-leader row for the Table of Content and the lists
// Left-aligned, not justified: the document default is justified, and justification
// stretches the tab between a caption's number and its title to the full line, which
// pushed short entries ("Table A.10  The fine-tuned 8M model...") across the page and
// their page number onto a line of its own. The left stop puts every title in the same
// column whatever the width of the number beside it.
const leader = (left, page, indent = 0) => {
  // An entry that carries its own tab ("Table A.10<tab>The fine-tuned ...") gets a hanging
  // indent rather than a left tab stop, for two reasons: every title then starts in the
  // same column whatever the width of the number, and a wrapped line starts past that
  // column, so the tab before the page number can only reach the right stop. With a left
  // tab stop instead, a short continuation line ("were trained...") sat before the stop
  // and swallowed the page number's tab, printing the number mid-line.
  const col = left.includes('\t') ? 1500 : 0;
  return new Paragraph({
    alignment: AlignmentType.LEFT,
    spacing: { after: 0, line: LINE_SINGLE },
    indent: { left: indent + col, hanging: col },
    tabStops: [{ type: TabStopType.RIGHT, position: TEXT_WIDTH }],
    children: [new TextRun({ text: `${left}\t${page}`, font: BODY_FONT, size: BODY_SIZE })],
  });
};

// ================================================================ 1. title page (short)
// spacing chosen to sit the four blocks where the template sits them: the title high on
// the page, the name near the middle, the degree and the university in the lower third
add(line(PH.title, { bold: true, before: 2000 }));
add(line(AUTHOR, { before: 5200 }));
add(line(DEGREE, { before: 4200 }));
add(line(UNIVERSITY, { before: 1400 }));
add(pageBreak());

// ================================================================ 2. declaration of thesis and copyright
add(line(UNIVERSITY, { bold: true, after: 360 }));
const boxed = (children) => new Table({
  width: { size: TEXT_WIDTH, type: WidthType.DXA }, columnWidths: [TEXT_WIDTH], alignment: AlignmentType.CENTER,
  rows: [new TableRow({ children: [new TableCell({
    width: { size: TEXT_WIDTH, type: WidthType.DXA },
    margins: { top: 200, bottom: 200, left: 200, right: 200 },
    borders: { top: { style: BorderStyle.SINGLE, size: 6, color: '000000' }, bottom: { style: BorderStyle.SINGLE, size: 6, color: '000000' },
               left: { style: BorderStyle.SINGLE, size: 6, color: '000000' }, right: { style: BorderStyle.SINGLE, size: 6, color: '000000' } },
    children,
  })] })],
});
const checkbox = (name, note) => new Paragraph({
  spacing: { after: 120, line: LINE_SINGLE },
  tabStops: [{ type: TabStopType.LEFT, position: 400 }, { type: TabStopType.LEFT, position: 2400 }],
  indent: { left: 2400, hanging: 2400 },      // wrapped note lines stay in the note column
  children: [new TextRun({ text: `\u2610\t${name}\t${note}`, font: BODY_FONT, size: BODY_SIZE })],
});
add(boxed([
  line('DECLARATION OF THESIS AND COPYRIGHT', { align: AlignmentType.LEFT, bold: true, after: 240 }),
  field("Author's Full Name", AUTHOR),
  field('Date of Birth', PH.dob),
  field('Title', PH.title),
  field('Academic Session', PH.session),
  line('I declare that this thesis is classified as:', { align: AlignmentType.LEFT, before: 240, after: 160 }),
  checkbox('CONFIDENTIAL', '(Contains confidential information under the Official Secret Act 1997)*'),
  checkbox('RESTRICTED', '(Contains restricted information as specified by the organization where research was done)*'),
  checkbox('OPEN ACCESS', 'I agree that my thesis to be published as online open access (Full Text)'),
  line('I acknowledge that Daffodil International University reserves the following rights:', { align: AlignmentType.LEFT, before: 240, after: 160 }),
  ...['The Thesis is the Property of Daffodil International University.',
      'The Library of Daffodil International University has the right to make copies of the thesis for the purpose of research only.',
      'The Library of Daffodil International University has the right to make copies of the thesis for academic exchange.']
    .map((t, i) => new Paragraph({ spacing: { after: 100, line: LINE_SINGLE },
      tabStops: [{ type: TabStopType.LEFT, position: 600 }], indent: { left: 600, hanging: 600 },
      children: [new TextRun({ text: `${i + 1}.\t${t}`, font: BODY_FONT, size: BODY_SIZE })] })),
  line('Certified by:', { align: AlignmentType.LEFT, before: 240, after: 480 }),
  new Paragraph({
    spacing: { after: 0, line: LINE_SINGLE },
    tabStops: [{ type: TabStopType.LEFT, position: Math.round(TEXT_WIDTH / 2) }],
    children: [new TextRun({ text: '_____________________\t_______________________', font: BODY_FONT, size: BODY_SIZE })],
  }),
  new Paragraph({
    spacing: { after: 360, line: LINE_SINGLE },
    tabStops: [{ type: TabStopType.LEFT, position: Math.round(TEXT_WIDTH / 2) }],
    children: [new TextRun({ text: "(Student's Signature)\t(Supervisor's Signature)", font: BODY_FONT, size: BODY_SIZE })],
  }),
  new Paragraph({
    spacing: { after: 0, line: LINE_SINGLE },
    tabStops: [{ type: TabStopType.LEFT, position: Math.round(TEXT_WIDTH / 2) }],
    children: [new TextRun({ text: '_____________________\t_______________________', font: BODY_FONT, size: BODY_SIZE })],
  }),
  new Paragraph({
    spacing: { after: 0, line: LINE_SINGLE },
    tabStops: [{ type: TabStopType.LEFT, position: Math.round(TEXT_WIDTH / 2) }],
    children: [new TextRun({ text: `${PH.id}\t${PH.supervisor}`, font: BODY_FONT, size: BODY_SIZE })],
  }),
  new Paragraph({
    spacing: { after: 0, line: LINE_SINGLE },
    tabStops: [{ type: TabStopType.LEFT, position: Math.round(TEXT_WIDTH / 2) }],
    children: [new TextRun({ text: 'Date:\tDate:', font: BODY_FONT, size: BODY_SIZE })],
  }),
]));
add(line('NOTE : * If the thesis is CONFIDENTIAL or RESTRICTED, please attach a thesis declaration letter.',
  { align: AlignmentType.LEFT, before: 240 }));
add(pageBreak());

// ================================================================ 3. supervisor's declaration
add(logo());
add(line("SUPERVISOR'S DECLARATION", { bold: true, after: 480 }));
add(new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: LINE_DOUBLE },
  children: [new TextRun({ text: `I hereby declare that I have checked this thesis entitled "${PH.title}" and in my opinion, this thesis is adequate in terms of scope and quality for the award of the degree of ${DEGREE} in Software Engineering.`, font: BODY_FONT, size: BODY_SIZE })],
}));
add(blank(4));
add(...signature("(Supervisor's Signature)"));
add(field('Full Name', PH.supervisor, 1600));
add(field('Position', PH.position, 1600));
add(field('Date', '', 1600));
add(pageBreak());

// ================================================================ 4. student's declaration
add(logo());
add(line("STUDENT'S DECLARATION", { bold: true, after: 480 }));
add(new Paragraph({
  alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: LINE_DOUBLE },
  children: [new TextRun({ text: 'I hereby declare that the work in this thesis is based on my original work except for quotations and citations which have been duly acknowledged. I also declare that it has not been previously or concurrently submitted for any other degree at Daffodil International University or any other institution.', font: BODY_FONT, size: BODY_SIZE })],
}));
add(blank(4));
add(...signature("(Student's Signature)"));
add(field('Full Name', AUTHOR, 1600));
add(field('ID Number', PH.id, 1600));
add(field('Date', '', 1600));
add(pageBreak());

// ================================================================ 5. title page (full)
add(line(PH.title, { bold: true, before: 1700 }));
add(line(AUTHOR, { before: 3400 }));
add(line('Thesis submitted in fulfillment of the requirements', { before: 3000 }));
add(line('for the award of the degree of'));
add(line(DEGREE, { before: 500 }));
add(line(DEPARTMENT, { before: 2800 }));
add(line(UNIVERSITY, { before: 900 }));
add(line(PH.date, { before: 900 }));
add(pageBreak());

// ================================================================ 6. acknowledgements
add(line('ACKNOWLEDGEMENTS', { bold: true, after: 480 }));
add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: LINE_DOUBLE },
  indent: { firstLine: INDENT_FIRST },
  children: [new TextRun({ text: '[ACKNOWLEDGEMENTS — to be written by the author. This page normally thanks the supervisor, the Department of Software Engineering, Daffodil International University, and family. It is personal to the author and has deliberately not been drafted here.]', font: BODY_FONT, size: BODY_SIZE })] }));
add(pageBreak());

// ================================================================ 7. dedication
add(line('DEDICATION', { bold: true, after: 480 }));
add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: LINE_DOUBLE },
  indent: { firstLine: INDENT_FIRST },
  children: [new TextRun({ text: '[DEDICATION — to be written by the author.]', font: BODY_FONT, size: BODY_SIZE })] }));
add(pageBreak());

// ================================================================ 8. abstract
const ABSTRACT = require('./abstract_text.js');
add(line('ABSTRACT', { bold: true, after: 480 }));
add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: LINE_DOUBLE },
  indent: { firstLine: INDENT_FIRST },
  children: [new TextRun({ text: ABSTRACT.text, font: BODY_FONT, size: BODY_SIZE })] }));
add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 240, line: LINE_SINGLE },
  children: [new TextRun({ text: 'Keywords: ', font: BODY_FONT, size: BODY_SIZE, italics: true }),
             new TextRun({ text: ABSTRACT.keywords, font: BODY_FONT, size: BODY_SIZE })] }));
add(pageBreak());

// ================================================================ 9. table of content
add(line('TABLE OF CONTENT', { bold: true, after: 480 }));
const TOC = JSON.parse(fs.readFileSync(`${THESIS}/toc.json`, 'utf8'));
for (const e of TOC.front) add(leader(e.title, pageOf(e.key)));
add(line('', { after: 120 }));
for (const e of TOC.body) {
  if (e.level === 1) add(line('', { after: 60 }));
  add(leader(e.title, pageOf(e.key), e.level === 1 ? 0 : (e.level === 2 ? 400 : 800)));
}
add(pageBreak());

// ================================================================ 10-11. list of tables / figures
for (const [heading, kind] of [['LIST OF TABLES', 'Table'], ['LIST OF FIGURES', 'Figure']]) {
  add(line(heading, { bold: true, after: 480 }));
  for (const c of TOC.captions.filter((x) => x.kind === kind)) {
    add(leader(`${kind} ${c.number}\t${c.short}`, pageOf(`${kind}:${c.number}`)));
  }
  add(pageBreak());
}

// ================================================================ 12. list of symbols
add(line('LIST OF SYMBOLS', { bold: true, after: 480 }));
for (const [sym, meaning] of [
  ['λ', 'weight of the supervised contrastive term in the combined objective'],
  ['τ', 'temperature of the supervised contrastive loss'],
  ['α', 'significance level of a statistical test'],
  ['σ', 'logistic (sigmoid) function'],
  ['Δ', 'difference between two models in a paired comparison'],
  ['±', 'mean plus or minus one standard deviation'],
  ['z', 'output of the projection head, L2-normalised'],
  ['h', 'hidden state of a residue position in the language model'],
]) add(new Paragraph({ spacing: { after: 60, line: LINE_SINGLE },
  tabStops: [{ type: TabStopType.LEFT, position: 1400 }],
  children: [new TextRun({ text: `${sym}\t${meaning}`, font: BODY_FONT, size: BODY_SIZE })] }));
add(pageBreak());

// ================================================================ 13. list of abbreviations
add(line('LIST OF ABBREVIATIONS', { bold: true, after: 480 }));
const ABBR = JSON.parse(fs.readFileSync(`${THESIS}/abbreviations.json`, 'utf8'));
for (const a of ABBR) add(new Paragraph({ spacing: { after: 60, line: LINE_SINGLE },
  tabStops: [{ type: TabStopType.LEFT, position: 2000 }],
  children: [new TextRun({ text: `${a.abbr}\t${a.full}`, font: BODY_FONT, size: BODY_SIZE })] }));
add(pageBreak());

// ================================================================ 14. list of appendices
add(line('LIST OF APPENDICES', { bold: true, after: 480 }));
add(leader('Appendix A\tDetailed results', pageOf('Appendix:A')));
add(leader('Appendix B\tModel and implementation detail', pageOf('Appendix:B')));

module.exports = L;
if (require.main === module) L.build();
