# POWER ANALYSIS

Minimum detectable effect (MDE) at 80% power, two-sided alpha = 0.05, for the paired lambda>0 vs lambda=0 comparisons actually run. MDE = (1.96 + 0.84) x SE, where SE is the standard deviation of the paired stratified bootstrap distribution (2,000 resamples) of the difference. It applies to *paired* comparisons of two models scored on the same sequences, which is what every test here is; an unpaired comparison would need a larger difference.

| test set | regime | n | comparisons | MDE MCC (median [min, max]) | MDE AUROC (median) |
|---|---|---|---|---|---|
| ind_1049 | A | 1049 | 6 | 0.059 [0.045, 0.076] | 0.020 |
| ind_1049 | B | 751 | 7 | 0.080 [0.056, 0.100] | 0.029 |
| ind_1049 | C | 716 | 6 | 0.086 [0.058, 0.101] | 0.033 |
| ind_425 | A | 425 | 6 | 0.083 [0.051, 0.100] | 0.022 |
| ind_425 | B | 214 | 7 | 0.138 [0.090, 0.165] | 0.046 |
| ind_425 | C | 162 | 6 | 0.174 [0.104, 0.201] | 0.055 |

## How to read a non-significant result

A non-significant paired difference means: *no effect larger than the MDE in the table was detectable at this sample size*. It is not evidence that the two models are equivalent. 
- ind_1049 (Regime B, n = 751): effects below about 0.08 MCC / 0.029 AUROC cannot be ruled out.
- ind_425 (Regime B, n = 214): effects below about 0.14 MCC / 0.046 AUROC cannot be ruled out.

Differences of the size seen between lambda settings in cross-validation (0.005-0.01 MCC) are an order of magnitude below these MDEs, so the independent test sets cannot confirm or refute effects of that size; the 5 x 5 cross-validation (25 paired runs on 3,716 sequences) is the better-powered, but optimistic, view (see T5.11c).
