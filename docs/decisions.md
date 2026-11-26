# Decisions log

One line per decision that changes the protocol. Newest at the bottom.
Format: `YYYY-MM-DD — member — decision — reason`

- 2026-11-26 — A — repository created, speaker-disjoint split protocol frozen in `member_a/02_make_splits.py` — baseline requirement of the proposal (section 4).
- 2026-11-26 — A — **working corpus for pipeline bring-up = `MON3EMPASHA/arabic_mispronunciation_dataset`** (open, no gate; 4,842 utterances, 79 speakers, 100 words, 686 mispronounced, 16 kHz mono, 0.90 h) — L2-KSU returned HTTP 403 ("email confirmation required") and is still blocked; the pipeline is dataset-agnostic, so this unblocks B/C/D without changing the design.
- 2026-11-26 — A — **splits frozen**: seed 42, ratios 60/20/20, speaker-disjoint ⇒ 48/15/16 speakers, 2,904/986/952 utterances, 406/136/144 mispronounced. sha256 `3353a1470fb4a966…`, see `data/splits.csv.sha256`. Do not edit; any change requires `splits_v2.csv`.
- 2026-11-26 — A — **modelling unit = (utterance, target phoneme) pair**, not utterance: words containing both target letters (e.g. صباح) yield one row per contrast. At target level the held-out test set holds H: 155 rows / 20 errors and S: 183 rows / 27 errors, versus 17 and 24 if H+S words were discarded.
- 2026-11-26 — A — **licence risk recorded**: the working corpus declares no licence (`license: undefined`). Used for pipeline bring-up only, never redistributed, and to be re-confirmed with the uploader / replaced by a licensed corpus for any published number.
