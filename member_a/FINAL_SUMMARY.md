# Member A — final summary (real data)

Everything below was produced by running the scripts in this folder on the
working corpus. Every number is reproducible from the commands in the last
section.

---

## 1. Corpus

| Item | Value |
|---|---|
| Source | `MON3EMPASHA/arabic_mispronunciation_dataset` (Hugging Face, open, no gate) |
| Licence | **not declared** — used for pipeline bring-up only, never redistributed |
| Utterances | **4,841** |
| Speakers | **79** (78 groups, see §3) |
| Distinct words | **100** |
| Mispronounced / correct | **686 / 4,155** (14.2% positive) |
| Total audio | **0.90 h** |
| Format | 16 kHz, mono, wav |
| Broken / missing files | **0 / 0** |
| Excluded | 1 clip, 0 bytes (`speaker_31_g_50/7.wav`) — no audio to score |

The corpus was chosen after the primary corpus (L2-KSU) returned HTTP 403 while
the account email was unverified. The pipeline is dataset-agnostic: it reads
`data/annotations.csv` only.

---

## 2. Data audit

| Split-agnostic checks | Result |
|---|---|
| duration | min 0.00 s · median 0.63 s · max 3.81 s |
| sample rates | `{16000: 4841}` |
| channels | `{1: 4841}` |
| annotation rows pointing to a missing file | 0 |

Words containing the target letters, at target-phoneme level:

| contrast | words | utterances | mispronounced | error rate |
|---|---|---|---|---|
| H (ح/هـ) | 15 | 764 | 111 | 0.145 |
| S (ص/س) | 23 | 975 | 123 | 0.126 |

---

## 3. Integrity finding (real leakage, fixed)

Hashing all 4,841 files found:

- **50 byte-identical recordings** shared by two speaker ids:
  `speaker_62_b_50` and `speaker_64_b_50`
- **all 50 pairs sat in different splits** in the first split release
  → the same recording was in train and in test
- 0 label conflicts among the duplicates (same label on both copies)
- 1 zero-byte file

Fix: both ids are treated as **one speaker group** (79 ids → 78 groups), and the
split is built per group. Re-checked afterwards: **cross-split duplicates = 0**.

The split step now refuses to run when duplicates span speaker ids and no
`--groups` map is supplied.

---

## 4. Split (frozen)

Seed 42 · 60/20/20 · speaker-disjoint **and** group-disjoint.

| Split | Groups | Speakers | Utterances | Mispronounced | pos_rate |
|---|---|---|---|---|---|
| train | 47 | 48 | 2,957 | 404 | 0.137 |
| val | 14 | 14 | 984 | 136 | 0.138 |
| test | 17 | 17 | 900 | 146 | 0.162 |

`sha256 = 4fddfab74f736daccd53b99f8d956eb2…` ([`data/splits.csv.sha256`])

Re-running the exact command reproduced the same hash.

At target-phoneme level (a word with both target letters counts once per contrast):

| contrast | train | val | test |
|---|---|---|---|
| H | 469 utt / 62 err | 158 / 23 | **137 / 26** |
| S | 587 / 71 | 202 / 31 | **186 / 21** |

---

## 5. QA gate

`03_verify_splits.py` → **PASS: 19 checks, 0 failed, 1 warning**

Highlights: no duplicate ids, all three splits populated, speaker-disjoint,
group-disjoint, labels strictly 0/1, every referenced file exists, every row
traceable to the annotation table.

Warning: the 31 test rows whose word contains **both** target letters carry only
5 errors — handled by scoring at target-phoneme level (see §4).

---

## 6. Label audit (30 clips listened to)

| verdict | count | share |
|---|---|---|
| error on the target letter | 5 | **17%** |
| word wrong, error elsewhere | 13 | 43% |
| sounds correct (label noise) | 8 | 27% |
| unsure | 4 | 13% |

Consequence: the corpus labels **utterances**, not phonemes. The unit of
prediction is therefore the **word**; phoneme posteriors remain the model's
input features. See `member_a/label_findings.md` for the limitations paragraph.

Statistical caveat: n = 30 → roughly ±13 percentage points at 95% confidence.

---

## 7. Demo prompts

16 prompts (8 per contrast) chosen by observed error frequency, covering
**82 H errors** and **70 S errors**: `docs/prompts.csv`, `docs/prompts.md`.
Each row carries the letter to highlight and one short English tip.

---

## 8. Limitations to state in the report

1. Licence undeclared; speaker ages/provenance undocumented.
2. Labels are utterance-level (see §6), not phoneme-level.
3. Positive class is 14% — precision/recall must be reported per class, and
   macro-F1 is the primary metric.
4. Test holds 146 errors; a difference smaller than a few points is noise.
5. 1% of the corpus (50 clips) is duplicated under a second speaker id; kept as
   one group rather than discarded.

---

## 9. Reproduce from scratch

```powershell
python member_a/00_smoke_test.py                  # gates the environment

python member_a/prepare_dataset.py --parquet data/_download/arabic_md.parquet
python member_a/01_audit.py --annotations data/annotations.csv --audio-dir data/raw
python member_a/06_check_integrity.py --annotations data/annotations.csv --audio-dir data/raw
python member_a/02_make_splits.py --annotations data/annotations.csv ^
  --speaker-col speaker_id --utt-col audio_path --label-col label ^
  --text-col text --contrast-col contrast --audio-dir data/raw ^
  --groups data/speaker_groups.csv --out data/splits.csv --seed 42
python member_a/03_verify_splits.py --splits data/splits.csv ^
  --annotations data/annotations.csv --audio-dir data/raw --contrast-col contrast
python member_a/make_phoneme_map.py --annotations data/annotations.csv
python member_a/05_select_prompts.py --per-contrast 8 --min-utts 20
python member_a/04_sample_for_review.py --summarize
```
