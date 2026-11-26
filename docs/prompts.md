# Demo prompts

Selected from the working corpus by error frequency, so every prompt exercises
the target phoneme with real mispronunciations behind it.

- `contrast` H = ح vs هـ, S = ص vs س
- `target_letter` is what the app should highlight
- `tip_en` is the one-line feedback shown after the judgement
- counts come from `data/annotations.csv` at build time

| id | prompt | contrast | highlight | utterances | errors |
|---|---|---|---|---|---|
| H01 | الحقيقة | H | ح | 69 | 20 |
| H02 | الذهاب | H | ه | 69 | 14 |
| H03 | حالك | H | ح | 65 | 10 |
| H04 | مرحباً | H | ح | 71 | 8 |
| H05 | الحياة | H | ح | 70 | 8 |
| H06 | صحيح | H | ح | 69 | 8 |
| H07 | التحدث | H | ح | 29 | 7 |
| H08 | الهاتف | H | ه | 27 | 7 |
| S01 | أستطيع | S | س | 72 | 13 |
| S02 | صديقي | S | ص | 29 | 11 |
| S03 | الشمس | S | س | 30 | 10 |
| S04 | صحيح | S | ص | 69 | 8 |
| S05 | آسف | S | س | 71 | 7 |
| S06 | السيارة | S | س | 70 | 7 |
| S07 | رسالة | S | س | 30 | 7 |
| S08 | الصباح | S | ص | 20 | 7 |

## Feedback lines

- **الحقيقة** (H01): For ح the friction is deep in the throat, not at the lips. Say a tired 'ahh' and tighten the pharynx.
- **الذهاب** (H02): هـ is a light breath from the open glottis. If you hear friction like clearing your throat, you said ح instead.
- **حالك** (H03): Hold the constriction of ح through the vowel that follows it; do not let it relax into هـ at the end of the word.
- **مرحباً** (H04): Think of fogging a mirror very softly: that is هـ. ح needs visible effort in the throat.
- **الحياة** (H05): For ح the friction is deep in the throat, not at the lips. Say a tired 'ahh' and tighten the pharynx.
- **صحيح** (H06): هـ is a light breath from the open glottis. If you hear friction like clearing your throat, you said ح instead.
- **التحدث** (H07): Hold the constriction of ح through the vowel that follows it; do not let it relax into هـ at the end of the word.
- **الهاتف** (H08): Think of fogging a mirror very softly: that is هـ. ح needs visible effort in the throat.
- **أستطيع** (S01): For ص pull the tongue body back and hollow the mouth; the sound is darker and heavier than س.
- **صديقي** (S02): س is a front hiss near the teeth. In ص the tongue retreats and the resonance moves to the back of the mouth.
- **الشمس** (S03): Keep the emphasis of ص through the whole syllable - it colours the neighbouring vowels.
- **صحيح** (S04): If ص sounds like a plain س, the tongue tip is too far forward. Retract it and lower the jaw slightly.
- **آسف** (S05): For ص pull the tongue body back and hollow the mouth; the sound is darker and heavier than س.
- **السيارة** (S06): س is a front hiss near the teeth. In ص the tongue retreats and the resonance moves to the back of the mouth.
- **رسالة** (S07): Keep the emphasis of ص through the whole syllable - it colours the neighbouring vowels.
- **الصباح** (S08): If ص sounds like a plain س, the tongue tip is too far forward. Retract it and lower the jaw slightly.