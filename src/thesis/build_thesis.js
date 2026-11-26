// Assembles the whole thesis into one .docx: front matter in lower-case Roman with the
// title page unnumbered, then body, references and appendices in Arabic from 1.
// Run after a normal two-pass chapter build, so the labels and captions are current.
process.env.THESIS_COMBINED = '1';

const fs = require('fs');
const lib = require('./lib.js');
const { D, ROOT, PAGE, MARGIN, BODY_FONT, BODY_SIZE, footerParagraph } = lib;
const { Document, Packer, Paragraph, PageBreak, Footer, NumberFormat } = D;

const front = require('./frontmatter.js');
const parts = [
  require('./ch1.js'), require('./ch2.js'), require('./ch3.js'),
  require('./ch4.js'), require('./ch5.js'), require('./references.js'),
];
const app = require('./appendices.js');

const pageBreak = () => new Paragraph({ children: [new PageBreak()] });

// every chapter, reference list and appendix starts on a fresh page
const body = [];
for (const p of parts) {
  if (body.length) body.push(pageBreak());
  body.push(...p.out);
}
for (const a of [app.A, app.B]) { body.push(pageBreak()); body.push(...a.out); }

const pageProps = { size: { width: PAGE.width, height: PAGE.height }, margin: MARGIN };

const doc = new Document({
  creator: 'Mohammad Sayem Uddin',
  title: 'Thesis',
  styles: { default: { document: { run: { font: BODY_FONT, size: BODY_SIZE } } } },
  sections: [
    {
      // preliminaries: lower-case Roman. The title page is (i) and its number is not typed,
      // which is what titlePage + an empty first-page footer gives.
      properties: { page: { ...pageProps, pageNumbers: { start: 1, formatType: NumberFormat.LOWER_ROMAN } }, titlePage: true },
      footers: { first: new Footer({ children: [new Paragraph({ children: [] })] }), default: new Footer({ children: [footerParagraph()] }) },
      children: front.out,
    },
    {
      // body, references and appendices: Arabic from 1
      properties: { page: { ...pageProps, pageNumbers: { start: 1, formatType: NumberFormat.DECIMAL } } },
      footers: { default: new Footer({ children: [footerParagraph()] }) },
      children: body,
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = `${ROOT}/AIP THESIS - Mohammad Sayem Uddin.docx`;
  fs.writeFileSync(out, buf);
  console.log(`wrote ${out}`);
  console.log(`  front matter paragraphs: ${front.out.length}`);
  console.log(`  body paragraphs:         ${body.length}`);
});
