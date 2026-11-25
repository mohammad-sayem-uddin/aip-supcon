Ranked, most important first:

1. **Decide the thesis framing before writing Chapter 5.** The data supports "leakage audit as headline, SupCon as a rigorous null/negative ablation" (playbook Risk 1). Read `INTERPRETATION.md`; if you agree, soften Chapter 1's "superior predictive stability" and the contribution wording, as the playbook suggests.
2. **Find out why AAC+RF beats every ESM-2 model.** Regime B MCC 0.425/0.374 (AAC+RF) vs 0.330/0.265 (best ESM-2). Cheap, informative checks: RF on ESM embeddings + AAC, and whether benchmark negatives are fragments of positive-source proteins. This is the examiner's likeliest first question.
3. **Fill Table 5.7** with published AIPpred/PreAIP/etc. numbers from the original papers (none were available to me and none were invented). Keep the Regime A caveat.
4. **Sanity-read the headline tables and figures** in `results/tables/` and `figures/` (all 12 figure jobs succeeded; I looked at the t-SNE and leakage-gap figures only).
5. **Optional extensions (all cheap on CPU):** extend lambda beyond 2.0 (best lambda sat on the grid edge at 8M and 150M); report the tuned-threshold results (`T5_2b`) next to the 0.5-threshold ones; consider a larger-n test by pooling Ind_425 and Ind_1049 Regime B (note the 77-sequence overlap between them).
6. **Chapters 1-2 fixes and Chapters 3-6 drafting** (playbook Prompts 12-14) were out of scope for this run and remain to do.
7. **Housekeeping.** The disk was close to full all night (free space swung from 0.1 to 8 GB); `.venv` is 1.3 GB and `embeddings/` holds the four cached checkpoints (gitignored). Kaggle was not needed: all four ESM-2 checkpoints ran on this Mac's CPU (650M took about 51 minutes), and the Kaggle CLI is logged in as the new account if you want to use it later.
