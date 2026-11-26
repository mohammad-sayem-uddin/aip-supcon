# WORD_BUDGET — measurement, cuts made, and the decision I need from you

Assembly run, Part 2. Measured 2026-11-26 from the generated `.docx` files, not estimated: the build now counts every word as it emits it (`src/thesis/lib.js`), categorises it as prose, heading, caption or table cell, and writes the tally into `results/thesis/meta_chN.json`. Re-running the build regenerates these numbers.

## 2.1 The three definitions you asked for

| | Definition | Words |
|---|---|---|
| **(a)** | body prose only (Chapters 1–5, including their headings) | **25,433** |
| **(b)** | (a) + tables, figure captions and equations — **working figure** | **30,875** |
| **(c)** | everything: (b) + abstract + references + appendices | **36,086** |

Per chapter, on definition (b), after the cuts described below:

| Chapter | prose | headings | captions | tables | (a) | (b) |
|---|---:|---:|---:|---:|---:|---:|
| 1 Introduction | 3,864 | 42 | 0 | 0 | 3,906 | 3,906 |
| 2 Literature Review | 3,739 | 43 | 42 | 344 | 3,782 | 4,168 |
| 3 Methodology | 8,723 | 198 | 348 | 992 | 8,921 | 10,261 |
| 4 Results and Discussion | 6,869 | 190 | 1,060 | 2,628 | 7,059 | 10,747 |
| 5 Conclusion | 1,740 | 53 | 0 | 0 | 1,793 | 1,793 |
| **Body total** | | | | | **25,433** | **30,875** |
| Abstract | 260 | 1 | — | — | 261 | 261 |
| References | 2,130 | 1 | — | — | 2,131 | 2,131 |
| Appendix A | 61 | 4 | 128 | 1,678 | 65 | 1,871 |
| Appendix B | 50 | 6 | 134 | 758 | 56 | 948 |

**Equations** are counted as 0 words. There are 19, all in Chapter 3. They are OMML objects, and a word count of them is not well defined — Word counts the symbols in an equation inconsistently and a plain-text extraction counts none. Treating them as 0 understates (b) by at most a few dozen words.

### One thing worth noticing before anything else

DIU's own limit is **30,000 words for a Bachelor thesis** (Guidelines p.10). On definition (a) the thesis is **under** it with 4,567 to spare. On definitions (b) and (c) it is **over** it — by 875 and 6,086. So which definition DIU uses is not only a question about your 22,000–23,000 target; it decides whether the thesis complies with the departmental limit at all. The Guidelines do not say.

## 2.2 Cuts made, in your priority order

**Lever 1 — move per-seed and per-fold detail tables to an appendix: −2,640 words.**
Two appendices were created (`src/thesis/appendices.js`), and every table moved is cited from the chapter it left.

| Moved to | Table | Words |
|---|---|---:|
| Appendix A | Performance on Ind_425, all models × 3 regimes | 567 |
| Appendix A | Performance on Ind_1049, all models × 3 regimes | 567 |
| Appendix A | Paired comparisons of the representation study | 475 |
| Appendix A | Temperature sweep at the selected λ | 184 |
| Appendix B | Layer-by-layer definitions of models B1–B6 (6 tables) | 629 |
| Appendix B | Compute time per stage | 253 |

The aggregated cross-validation table (now Table 4.1) stays in Chapter 4, as you asked.

**Lever 2 — never a table and a figure for the same data: −435 words, and six fewer floats.**

| Removed | Kept | Why |
|---|---|---|
| Figure (leakage gap across regimes) | Table 4.4 | the table carries the per-model drop figures, which the finding rests on |
| Figure (six architectures at λ* vs λ = 0) | Table 4.9 | the table also carries the confidence intervals and adjusted p-values |
| Figure (pooling variants) | Table 4.12 | the table carries the numbers |
| Figure (fusion and fine-tuning) | Table 4.14 | the table carries the numbers |
| Table (cross-benchmark MCC per pairing) | Figure 4.2 heat map | a 3 × 3 × 3 grid reads better as a heat map |
| Table (λ sweep) | Figure 4.3 | a sweep is a curve |

**Lever 3 — compress prose that narrates table values: measured, and far smaller than expected.**

You predicted most of the slack would be here. It is not, and I can show why. Chapter 4's prose is 6,869 words carrying 302 interpolated values — it is dense with numbers, but the numbers are not padding. Taking the worst offender, a 538-word paragraph in Section 4.4.3 with 28 recited values, and rewriting it exactly as you specified — recited per-model figures out, the meaning of the comparison in — removed **5 values and 16 words**. That is the real exchange rate: about 3 words per recited value, because each `0.425` is one word whether it is in a table or a sentence.

Extrapolating honestly: removing *every* recitation in Chapter 4 that is safe to remove would save roughly **1,200–1,400 words**, not the several thousand the lever was expected to yield. Levers 4 (merge subsections) and 5 (tighten the discussion) would add perhaps 600–700 more.

## 2.3 I have stopped here, because the rest would have to come out of what you said never to cut

Where that leaves the arithmetic:

```
  now, on definition (b)                        30,875
  lever 3 at its realistic maximum              − 1,300
  levers 4 and 5 at their realistic maximum     −   650
  ------------------------------------------------------
  best reachable without touching protected text 28,925
  your target                                    23,000
  REMAINING GAP                                 ≈ 5,900
```

Those 5,900 words can only come from material rule 2.3 protects:

| Where the remaining 5,900 would have to come from | Words available | What it costs |
|---|---:|---|
| Chapter 3 methodology prose | 8,723 | this is the reproducibility detail — the audit procedure, the regimes, the loss definitions, the statistical protocol. Cutting 5,900 means cutting two thirds of it, and the work stops being reproducible from the thesis. |
| Chapters 1 and 2 | 8,074 | explicitly protected, and you asked me last week to *grow* them to 8–12 pages each; they are at 7 and 8. |
| Chapter 4's limitations and statistical caveats | ~1,900 | the confidence intervals, the minimum-detectable-effect statements and Section 4.10 — the things that make the negative result defensible rather than just unsupported. |
| Chapter 5 Conclusion | 1,793 | contains the limitations summary. |

So: **I cannot reach 23,000 without cutting one of those four, and I have not touched any of them.**

## What I need you to decide

Four ways forward, in the order I would recommend them:

1. **Settle the definition first.** If DIU counts body prose — which is how a word limit is usually read, and how a supervisor eyeballing a draft would count — the thesis is at **25,433** and already inside DIU's 30,000. Then the only question is whether you still want 22,000–23,000 as a personal target, and the gap is 2,400, which levers 3–5 nearly close on their own. **Ask your supervisor which definition applies.** This is the cheapest question to ask and it may dissolve the problem.
2. **Relax the target to about 28,000–29,000 on definition (b).** I finish levers 3, 4 and 5, nothing protected is touched, and the thesis is comfortably inside DIU's 30,000 on every definition. I can do this immediately on your word.
3. **Move most of the remaining tables to the appendices.** Chapter 3 and Chapter 4 still hold 3,620 words of table text and 1,408 of captions in the body. Pushing nearly all of it into appendices would take (b) to roughly **25,500** while losing nothing at all — every table still exists and is still cited. The cost is a results chapter that is mostly prose and cross-references, which reads poorly and which an examiner may dislike. I would do this only if you want it.
4. **Authorise a specific protected cut.** If you want 23,000 on definition (b), tell me which of the four rows above to cut and by how much, and I will do exactly that and nothing more.

Nothing in Parts 3 to 8 depends on this decision, so the run continues: formatting, front matter, diagrams, citations, compliance and the final build all proceed, and the word count is re-measured at the end in `DIU_COMPLIANCE.md`.
