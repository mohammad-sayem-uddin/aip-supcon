const { chapter } = require('./lib.js');
const ABSTRACT = require('./abstract_text.js');
const L = chapter(0, 'ABSTRACT', 'ABSTRACT thesis.docx');
console.log('abstract words:', ABSTRACT.words);
L.add(L.H1('ABSTRACT'));
L.add(L.P(ABSTRACT.text));
L.add(L.P(`<i>Keywords:</i> ${ABSTRACT.keywords}`));
module.exports = L;
if (require.main === module && process.argv[2] !== 'dry') L.build();
