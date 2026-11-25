# CITATIONS_TO_VERIFY

Rule used for the thesis bibliography: an entry is in `results/thesis/references.json` / `references.bib` only if its authors, title, venue, year and DOI were matched against a CrossRef record (title similarity >= 0.90, first author and year agree) or, for conference papers, an arXiv record fetched by identifier. The builder is `src/thesis/build_bib.py`; 26 entries pass, 0 failed. Everything below is **not** in the bibliography, or is in it with a stated limit. No DOI, volume or page number was guessed.

## A. Claims that carry no citation, and what is needed

| # | Where | Exact statement | What could not be confirmed | Needed to close |
|---|---|---|---|---|
| A1 | Ch. 3 (Section 3.5, baselines) and Ch. 5 (5.1, Table 5.1) | "A gradient-boosted decision tree model (LightGBM) ..." | Ke et al. (2017), NeurIPS: no CrossRef record (conference paper without DOI); arXiv has no matching record. Not matched, so not included. | The NeurIPS 2017 proceedings record (authors, title, pages, URL) or the LightGBM repository citation. |
| A2 | Ch. 3 (baselines) | "An AAC random forest used 500 trees ..." | Breiman (2001), *Machine Learning* 45:5-32: not looked up. | CrossRef record for the DOI printed on the journal page. |
| A3 | Ch. 3 (baselines) | "support vector machine ... radial-basis kernel" | Cortes and Vapnik (1995), *Machine Learning* 20:273-297: not looked up. | CrossRef record. |
| A4 | Ch. 3 (training) | "cosine learning-rate schedule" | Loshchilov and Hutter, SGDR (arXiv 1608.03983): not fetched. AdamW (`loshchilov2017`) is verified; the schedule is not cited. | arXiv record 1608.03983 added to `ARXIV` in `build_bib.py`. |
| A5 | Ch. 3 (architecture) | "batch normalisation, a rectified linear unit and dropout" | Ioffe and Szegedy (2015), Srivastava et al. (2014): not looked up. | arXiv / JMLR records. |
| A6 | Ch. 2 (2.1) | RDP58 and vasoactive intestinal peptide examples | Taken from the Introduction of Manavalan et al. (2018) (full text read, PMC copy in `data/external/papers/aippred.txt`). The primary studies they cite (Boismenu et al. 2002; Gonzalez et al. 2005; Delgado et al. 2001) were **not** retrieved, so the sentence is second-hand and says so. | CrossRef records of the three primary studies, if the examiner wants first-hand citations. |
| A7 | Ch. 2 (2.3) | ESM-2 "scaled ... to 15 billion parameters" and the ESM-1b training-set size | Verified against the abstracts of Lin et al. (2023) and Rives et al. (2021). Listed here only because the thesis quotes the numbers. | None. |
| A8 | Ch. 5 (5.7, Table 5.16) | Published AUROC / MCC of AIPpred, PreAIP, AntiInflam, AIPStack | Only values stated **in the abstracts** are entered (AIPpred independent AUC 0.814; PreAIP test AUC 0.840; AIPStack independent set 3 AUC 0.819, MCC 0.510; AntiInflam validation MCC 0.31 for the random forest). Every other cell is TODO. The PreAIP and AIPStack full texts could not be read (PMC bot check). | Full texts of the four papers; for each, the training collection used. |

## B. Statements that were in the earlier drafts of Chapters 1 and 2 and have been **removed** (not verifiable from a record the thesis can cite)

1. "AIEpred", "Pep-CNN" and "IALP" as further AIP predictors (Ch. 2, earlier draft). No record matched.
2. A list of the features used by PreAIP ("CKSAAP" and others). Only "primary sequence, evolutionary and structural information through a random forest" is in the abstract, and only that is kept.
3. "ESM representations consistently outperformed traditional encodings for AIPs / peptide tasks." No source; contradicted by the results of this thesis.
4. "Contrastive learning has been applied effectively in bioinformatics." No source retrieved.
5. NF-kB / MAPK / LPS-binding mechanism sentence (Ch. 2 section 2.1, marked [CITATION NEEDED] in the previous build). Replaced by the two examples in A6; the mechanism claims themselves are not made.
6. "Pre-trained on full-length proteins" (Ch. 1). Replaced by "pre-trained on protein sequences".
7. Cai et al. (2003) as a source for the CTD descriptors (Ch. 3). The CrossRef match was SVM-Prot, not a CTD paper. CTD is cited to Dubchak et al. (1995) only.
8. AIPFusion-Net: the paper could not be read (HTTP 503), so nothing about it appears in any chapter.

## C. Entries in the bibliography with a stated limit

| Key | Limit |
|---|---|
| khosla2020 (arXiv 2004.11362) | Journal/conference venue (NeurIPS 2020) not verified; cited as the arXiv record. |
| vaswani2017 (arXiv 1706.03762) | NeurIPS 2017 venue not verified; cited as the arXiv record. |
| ilse2018 (arXiv 1802.04712) | ICML 2018 venue not verified. |
| loshchilov2017 (arXiv 1711.05101) | ICLR 2019 venue not verified. The year in the text is the arXiv year. |
| paszke2019 (arXiv 1912.01703) | NeurIPS 2019 venue not verified. |
| pedregosa2012 (arXiv 1201.0490) | The arXiv record's `journal_ref` reads "Journal of Machine Learning Research (2011)"; the thesis text shows the arXiv year (2012). Decide on one year and correct `references.json` by hand. |

## D. Descriptions checked against full texts held locally (verified, listed for the examiner)

`data/external/papers/aippred.txt` and `antiinflam.txt` are the PMC full texts. They confirm: the cytokine list that defines an AIP (IL-10, IL-13, IL-22, IL-1RA, TGF-beta, IFN-alpha/beta); AntiInflam training 690 / 1,009 and the validation split; AIPpred benchmark 1,258 / 1,887 and independent set 420 / 629; CD-HIT redundancy removal at a 0.8 identity threshold; negative examples taken from experimentally verified IEDB peptides, with earlier methods drawing negatives from random UniProt peptides. The files of `data/external/preaip_*` and `aippred_*` show that PreAIP's training set contains the AIPpred benchmark (1,258 + 1,887 sequences) and that its test set is the AIPpred independent set (420 + 629).
