# WORD_BUDGET — the measurement, and how the target was met

Target: **22,000–23,000 words**, treated as a requirement. Final: **22,954**.

Every figure here is measured by the build itself, which counts and categorises each word
as it emits it (`results/thesis/meta_ch*.json`), and cross-checked against the generated
`.docx` by `src/thesis/compliance.py`.

## The three definitions, measured

| | counts | final |
|---|---|---:|
| **(a)** body prose only | Chapters 1–5, running text and headings | **22,044** |
| **(b)** body prose + tables, figure captions and equations | the working figure, and the target | **22,954** |
| **(c)** everything | (b) + abstract + references + appendices | **34,940** |

Definition (b) is the one the target applies to. Both (a) and (b) are also inside DIU's own
30,000-word limit for a Bachelor thesis, so the count no longer turns on which definition
the department applies — a question this document raised when the thesis stood at 31,213,
and which no longer needs an answer.

## Before and after, by chapter

| | before any cutting | after the first pass | final |
|---|---:|---:|---:|
| Chapter 1 Introduction | 3,906 | 3,906 | 3,906 |
| Chapter 2 Literature Review | 4,168 | 4,168 | 3,782 |
| Chapter 3 Methodology | 11,134 | 10,261 | 7,225 |
| Chapter 4 Results and Discussion | 12,965 | 10,747 | 6,454 |
| Chapter 5 Conclusion | 1,793 | 1,793 | 1,587 |
| **body, definition (b)** | **33,966** | **30,875** | **22,954** |

Outside the count, and still in the thesis: abstract 261, references 2,131, Appendices A
and B 9,594.

By category, over the second pass (30,875 → 22,954, a reduction of 7,921):

| | after the first pass | final | change |
|---|---:|---:|---:|
| prose | 24,891 | 21,586 | −3,305 |
| tables | 4,246 | 321 | −3,925 |
| captions | 1,212 | 589 | −623 |
| headings | 526 | 458 | −68 |

## What actually moved the number

The brief's five levers were applied in its order of priority. Measured, they are worth
very different amounts, and the difference is the whole story of this budget.

**Lever 1 — detail tables to an appendix. By far the largest, about 8,500 words over the
two passes.** Twenty-seven tables moved: every per-model result table for Ind_425 and
Ind_1049, the paired comparisons, the temperature sweep, the published-figures table and
the minimum-detectable-effect table to Appendix A; the dataset, cleaning, identity,
embedding, pooling, fine-tuning, training, software, device and hash tables to Appendix B.
Chapter 2's Table 2.1 went the same way, which is the whole of that chapter's reduction —
no Chapter 2 prose was cut. Each table keeps its caption, its source line and its number,
and each is still cited by number from the chapter it left. `src/thesis/relocate.js` is
the single list that controls this, with the reasoning in its header; moving a label in or
out of that list moves the table.

Two tables were deliberately **kept in the body** because the central finding rests on
them: `tab:overlap` (how much of each independent set occurs in the training file) and
`tab:gaps` (what removing that overlap does to every model).

**Lever 1b — whole sections to an appendix, which is where most of the prose went.** The
implementation record that the restructure had folded into Chapter 3 — the hardware and
software environment, the stage-by-stage compute time, the layer-by-layer definitions of
the six architectures, the hyperparameters and search ranges, the reproducibility
arrangements and the deviations from the plan — now forms Appendix B, Sections B.1 to B.6.
In the second pass two more moved: the provenance of the published figures and the
observations drawn from them (Section 4.7 → Appendix A.1, 268 words) and the verification
of the embedding cache (Section 3.5.2 → Appendix B.5, 158 words). Nothing was deleted, and
each is cited from the section it left. `NUMBERS_CHANGED.md` §7 records what stayed behind.

**Lever 2 — never a table and a figure for the same data. −435.** Four figures went whose
tables carry the numbers and the confidence intervals (leakage gap, six architectures,
pooling, fine-tuning), and two tables went whose figures read better (the cross-benchmark
heat map and the λ sweep curve).

**Lever 3 — compressing prose that narrates table values. Worth far less than expected,
about 500 words.** The brief predicted most of the slack would be here. Measured on the
worst offender in the thesis — a 538-word paragraph reciting 28 values — removing five
values saved **sixteen words**, because a number costs one word wherever it sits. Across
Chapters 3 and 4 roughly 90 sentence rewrites yielded about 500 words: real, but a
seventeenth of what relocation gave, for most of the effort. Worth recording, because the
intuition that narration is where the fat is turns out to be wrong for a results chapter.
Twelve figure captions were shortened the same way (−623 including the captions of
relocated tables); none lost a panel label, a count, a source line or a greyscale reading
hint.

**Lever 4 — merging redundant subsections.** The old Chapter 4's training-protocol section
was merged into Section 3.7.5 during the restructure, and a duplicate printing of the
hyperparameter table was found and dropped in this pass (`NUMBERS_CHANGED.md` §7).

**Lever 5 — tightening the Discussion. Section 4.9 is dense and gave up little; Chapter 5,
which is a restatement by construction, gave up 206.** Its four objective answers, four
contributions, six items of future work and all six limitations are intact, with every
interval, p-value and minimum-detectable-effect statement unchanged.

## What was never touched

As instructed, and verified against the built file:

- **Chapters 1 and 2.** Chapter 1 is unchanged to the word. Chapter 2's prose is unchanged
  to the word; its 390-word reduction is Table 2.1 moving to Appendix A as Table A.1.
- **Every methodology detail needed to reproduce the work.** Relocation to Appendix B is
  not removal: the layer tables, loss definitions, folds, metrics, hyperparameters,
  software versions, devices and file digests are all in the thesis, cited by number from
  the chapter that describes the choice.
- **The leakage finding and its mechanism** — Sections 3.2.2, 4.4.1 to 4.4.5, Figure 3.2,
  Figure 4.3 and the two tables kept in the body.
- **The limitations** — Section 4.10 and Section 5.3, intact.
- **Every statistical caveat, confidence interval and minimum-detectable-effect
  statement.** None was shortened; several sentences around them were.

## The one thing to check with your supervisor

The count is met on every definition, so nothing is blocked. The one judgement worth
confirming is that **a Methodology chapter of 7,225 words with its implementation record in
Appendix B** reads the way your department expects, rather than as a chapter that has been
hollowed out. Nothing was lost and every appendix table is cited from the body, but whether
an examiner would rather have that detail in Chapter 3 is a question about local
convention, not about content. If the answer is that it belongs in the body,
`relocate.js` moves any table back in one line — at the cost of the words it carries.
