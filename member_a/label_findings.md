# Label quality audit — findings

**Date:** 2026-11-26
**Owner:** Member A
**Corpus:** `MON3EMPASHA/arabic_mispronunciation_dataset` (working corpus)

## Question

The corpus labels whole utterances (`1 = mispronounced`, `0 = correct`). The
project targets a *specific phoneme* (ح/هـ, ص/س). Before building anything on
top of these labels we asked: **is the error actually on the target letter?**

## Method

- 30 clips sampled at random from the held-out split, all labelled `1`
  (mispronounced): 15 per contrast, `member_a/04_sample_for_review.py`.
- Each clip was listened to and judged by a native speaker on one dimension
  only: the marked target letter.
- Four verdicts: `target` (error is on that letter), `other` (word is wrong,
  error elsewhere), `none` (clip sounds correct → label noise),
  `unsure`.

## Results

| contrast | target | other | none | unsure | agreement |
|---|---|---|---|---|---|
| H (ح/هـ) | 1 | 6 | 6 | 2 | **7%** |
| S (ص/س) | 4 | 7 | 2 | 2 | **27%** |
| **total** | **5** | **13** | **8** | **4** | **17%** |

By target letter:

| letter | target | other | none | unsure |
|---|---|---|---|---|
| ح | 1 | 5 | 4 | 0 |
| هـ | 0 | 1 | 2 | 2 |
| س | 4 | 6 | 1 | 2 |
| ص | 0 | 1 | 1 | 0 |

## Reverse check — clips labelled correct

20 clips sampled from the same held-out split with label `0`, judged as whole words.

| contrast | ok | wrong | unsure | agreement |
|---|---|---|---|---|
| H | 7 | 1 | 2 | 70% |
| S | 7 | 1 | 2 | 70% |
| **total** | **14** | **2** | **4** | **70%** (87.5% excluding unsure) |

So the noise is **asymmetric**: the corpus over-marks errors far more than it
misses them. Reading the two checks together, at word level:

- of the clips labelled mispronounced, roughly **60%** really are wrong
  (`target` + `other` = 18/30), **27%** sound correct, 13% undecided;
- of the clips labelled correct, roughly **88%** (excluding unsure) really are correct.

Approximate positive-class precision of the labels: **0.60–0.73**. This caps the
F1 any model can reach on this corpus: a perfect system cannot exceed roughly
0.75–0.80 because the labels themselves disagree with a careful human listener
on a quarter of the positive class.

## Interpretation

1. **The label is word-level, not phoneme-level.** Only 17% of the
   mispronunciations we listened to sit on the target letter; 43% are errors
   elsewhere in the word (wrong vowel, another consonant, a missing letter).
2. **Label noise is material.** 27% of clips labelled "mispronounced" sounded
   correct on a single careful listen.
3. Statistical caution: n = 30, so each percentage has a 95% interval of
   roughly ±13 points. The conclusion is directional, not precise.

## Consequence for the project

The unit of prediction is changed from *target phoneme* to *word*:

- **Task:** word-level mispronunciation detection (binary), speaker-disjoint.
- **Research question:** does a calibrated feature layer over a frozen phoneme
  ASR improve detection F1 over direct decoding, on unseen speakers?
- **Unchanged:** the pipeline, the features (phoneme posteriors are still the
  input), the split protocol, the metrics and the abstention design.
- **Deferred:** the phoneme-level claim now requires a corpus with true
  phoneme-level annotations (L2-KSU, or IQRA/QuranMB with phoneme error
  annotations). If one is obtained, the same code re-runs unchanged.

This is a scope correction justified by an audit, not a silent change: it is
recorded in `docs/decisions.md` and should be mentioned to the instructor.

## Limitations paragraph (for the final report)

> The corpus provides utterance-level labels only. A manual audit of 30
> mispronounced held-out clips found that 5 (17%) of the perceived errors fell
> on the targeted consonant; 13 (43%) were errors elsewhere in the word and 8
> (27%) sounded correct. A reverse audit of 20 clips labelled correct found 14
> (70%) to be correct, 2 (10%) mispronounced and 4 (20%) undecidable. The noise
> is therefore asymmetric: labels over-mark errors rather than missing them,
> and the effective precision of the positive class is roughly 0.60-0.73. We
> therefore report word-level mispronunciation detection and treat phoneme
> posteriors as input features rather than as scoring targets; the ceiling this
> imposes on F1 is stated alongside the results. Estimates from 30 and 20 clips
> carry roughly ±13 and ±16 percentage points at 95% confidence, so the audits
> establish a direction, not a precise error rate. A phoneme-level claim would
> require a corpus annotated at the phoneme level.
