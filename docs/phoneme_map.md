# Phoneme map — target contrasts

Defines which sound is judged for every prompt and which sound the learner is
expected to confuse it with.

## Convention

- One judgement per **(utterance, target phoneme)** pair, not one per utterance.
  A word containing both target letters (e.g. صَبَاح) yields **two** rows, one per
  contrast.
- `label` is inherited from the utterance: `1 = mispronounced`, `0 = correct`.
- Canonical phoneme sequences are produced at runtime by the phonemizer in
  `member_b/`, never typed by hand, so the mapping stays reproducible. IPA below
  is reference material only.
- Prompts without a target letter are excluded: they cannot be scored.

## Contrasts

| id | target (correct) | competitor (expected confusion) | articulatory cue |
|---|---|---|---|
| **H** | ح /ħ/ voiceless pharyngeal fricative | هـ /h/ glottal fricative | ح is constricted deep in the throat; هـ is a light breath from the glottis |
| **S** | ص /sˤ/ emphatic sibilant | س /s/ plain sibilant | ص has a backed, lowered tongue body and a darker resonance; س is front and flat |

## Prompts with a target phoneme

Counts are read from `data/annotations.csv`. `error rate` is the observed
label rate — useful for picking prompts that carry enough error examples.

### H

| word | target letter | utterances | mispronounced | error rate |
|---|---|---|---|---|
| الحقيقة | ح | 69 | 20 | 0.290 |
| الذهاب | ه | 69 | 14 | 0.203 |
| حالك | ح | 65 | 10 | 0.154 |
| الحياة | ح | 70 | 8 | 0.114 |
| صحيح | ح | 69 | 8 | 0.116 |
| مرحباً | ح | 71 | 8 | 0.113 |
| التحدث | ح | 29 | 7 | 0.241 |
| الصباح | ح | 20 | 7 | 0.350 |
| الهاتف | ه | 27 | 7 | 0.259 |
| الله | ه | 69 | 6 | 0.087 |
| صباح | ح | 67 | 6 | 0.090 |
| نهاية | ه | 28 | 4 | 0.143 |
| لحظة | ح | 65 | 3 | 0.046 |
| حياة | ح | 17 | 2 | 0.118 |
| البحر | ح | 30 | 1 | 0.033 |

### S

| word | target letter | utterances | mispronounced | error rate |
|---|---|---|---|---|
| أستطيع | س | 72 | 13 | 0.181 |
| صديقي | ص | 29 | 11 | 0.379 |
| الشمس | س | 30 | 10 | 0.333 |
| صحيح | ص | 69 | 8 | 0.116 |
| آسف | س | 71 | 7 | 0.099 |
| السيارة | س | 70 | 7 | 0.100 |
| الصباح | ص | 20 | 7 | 0.350 |
| رسالة | س | 30 | 7 | 0.233 |
| صباح | ص | 67 | 6 | 0.090 |
| آسفة | س | 49 | 5 | 0.102 |
| اسم | س | 28 | 5 | 0.179 |
| الناس | س | 72 | 5 | 0.069 |
| أصدقاء | ص | 30 | 4 | 0.133 |
| الأسبوع | س | 28 | 4 | 0.143 |
| الرئيس | س | 30 | 4 | 0.133 |
| المدرسة | س | 30 | 4 | 0.133 |
| النساء | س | 26 | 4 | 0.154 |
| شخص | ص | 77 | 4 | 0.052 |
| مساء | س | 29 | 3 | 0.103 |
| الساعة | س | 29 | 2 | 0.069 |
| السماء | س | 30 | 1 | 0.033 |
| ساعة | س | 30 | 1 | 0.033 |
| سنة | س | 30 | 1 | 0.033 |
