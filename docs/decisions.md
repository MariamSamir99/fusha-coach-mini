# Decisions log

One line per decision that changes the protocol. Newest at the bottom.
Format: `YYYY-MM-DD — member — decision — reason`

- 2026-11-26 — A — repository created, speaker-disjoint split protocol frozen in `member_a/02_make_splits.py` — baseline requirement of the proposal (section 4).
- 2026-11-26 — A — **working corpus for pipeline bring-up = `MON3EMPASHA/arabic_mispronunciation_dataset`** (open, no gate; 4,842 utterances, 79 speakers, 100 words, 686 mispronounced, 16 kHz mono, 0.90 h) — L2-KSU returned HTTP 403 ("email confirmation required") and is still blocked; the pipeline is dataset-agnostic, so this unblocks B/C/D without changing the design.
- 2026-11-26 — A — **splits frozen**: seed 42, ratios 60/20/20, speaker-disjoint ⇒ 48/15/16 speakers, 2,904/986/952 utterances, 406/136/144 mispronounced. sha256 `3353a1470fb4a966…`, see `data/splits.csv.sha256`. Do not edit; any change requires `splits_v2.csv`.
- 2026-11-26 — A — **modelling unit = (utterance, target phoneme) pair**, not utterance: words containing both target letters (e.g. صباح) yield one row per contrast. At target level the held-out test set holds H: 155 rows / 20 errors and S: 183 rows / 27 errors, versus 17 and 24 if H+S words were discarded.
- 2026-11-26 — A — **licence risk recorded**: the working corpus declares no licence (`license: undefined`). Used for pipeline bring-up only, never redistributed, and to be re-confirmed with the uploader / replaced by a licensed corpus for any published number.
- 2026-11-26 — A — **unit of prediction changed from target phoneme to word**, after a manual audit of 30 mispronounced held-out clips: only 5 (17%) of the perceived errors fell on the target consonant, 13 (43%) were elsewhere in the word and 8 (27%) sounded correct. The corpus labels utterances, not phonemes, so a phoneme-level claim cannot be supported. Features (phoneme posteriors) and the split protocol are unchanged; see `member_a/label_findings.md`.
- 2026-11-26 — A — **integrity defect found and fixed**: 50 recordings are byte-identical between speaker ids `speaker_62_b_50` and `speaker_64_b_50`, and all 50 pairs sat in different splits, i.e. real leakage. Splitting now runs on **speaker groups** (`data/speaker_groups.csv`, 79 ids → 78 groups) and QA checks group-disjointness. Verified: cross-split duplicates 50 → 0.
- 2026-11-26 — A — **one unreadable clip removed** (`speaker_31_g_50/7.wav`, 0 bytes) from `data/annotations.csv`; 4,842 → 4,841 rows. No other row was filtered.
- 2026-11-26 — A — **splits re-frozen** (seed 42, 60/20/20, on groups): 47/14/17 groups, 2,957/984/900 utterances, 404/136/146 mispronounced, pos_rate 0.137/0.138/0.162. New sha256 `4fddfab74f736dac…`; supersedes `3353a147…` before any downstream use (`data/splits.csv` history is in git).
