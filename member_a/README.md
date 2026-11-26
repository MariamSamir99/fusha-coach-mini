# Member A — data audit, splits, phoneme map

Owner of the dataset layer. Everything downstream depends on the two files this
folder produces, so they are frozen before anyone else starts modelling.

## Data sources

| Source | Link | Access | Use |
|---|---|---|---|
| **L2-KSU** (primary) | https://huggingface.co/datasets/IWAN/L2-KSU-Dataset | gated, auto-approval | training + evaluation |
| L2-KSU (original) | https://catalog.ldc.upenn.edu/LDC2024S11 | LDC licence | fallback if the HF gate is refused |
| Arabic-Dataset-for-CAPT | https://github.com/bhalima/Arabic-Dataset-for-CAPT | open | optional sanity check only (children, 9 speakers x 16 prompts) |
| IQRA 2026 | https://arxiv.org/abs/2603.29087 | open | fallback corpus with a published MDD protocol |

**Current working corpus:** `MON3EMPASHA/arabic_mispronunciation_dataset`
(open, no gate: 4,842 utterances, 79 speakers, 100 words, 686 mispronounced,
16 kHz mono, 0.90 h). Used to bring the pipeline up while the L2-KSU gate is
blocked; every script is dataset-agnostic and only reads `data/annotations.csv`.
The licence of that corpus is undeclared, so it is not redistributed and its use
is recorded in `docs/decisions.md`.

Licence of L2-KSU: **CC BY-NC-ND 4.0**. Research use inside this project is fine;
redistribution of audio or derivatives is not.

## Getting the data

1. Create a Hugging Face account and accept the gate on the dataset page.
2. Create a read token: https://huggingface.co/settings/tokens
3. Download:

```powershell
pip install -U huggingface_hub
hf auth login
hf download IWAN/L2-KSU-Dataset --repo-type dataset --local-dir data/raw_repo
```

4. Unzip and lay it out as:

```
data/
├── raw/                 all wav files
├── annotations.csv      the annotation table
├── splits.csv           produced by 02_make_splits.py
├── splits.csv.sha256
└── splits.csv.meta.json
```

`data/raw/` and `data/annotations.csv` are gitignored on purpose.

## Scripts

| Script | Purpose | Output |
|---|---|---|
| `00_smoke_test.py` | verifies the environment on synthetic data | PASS / FAIL |
| `01_audit.py` | counts speakers, hours, labels, per-phoneme errors, broken files | `data_audit_report.md` |
| `02_make_splits.py` | speaker-disjoint 60/20/20 split, frozen with sha256 | `data/splits.csv` |
| `03_verify_splits.py` | 17 QA checks, blocks the hand-off on leakage or a weak test set | `splits_qa.md` |
| `prepare_dataset.py` | unpacks audio embedded in a parquet dump into `data/raw/` + `data/annotations.csv` | annotation table |
| `make_phoneme_map.py` | writes the prompt / target-phoneme map with live counts | `docs/phoneme_map.md` |

Run order:

```powershell
python member_a/00_smoke_test.py

# only when the corpus ships audio inside a parquet dump
python member_a/prepare_dataset.py --parquet data/_download/arabic_md.parquet

python member_a/01_audit.py --annotations data/annotations.csv --audio-dir data/raw

python member_a/02_make_splits.py --annotations data/annotations.csv ^
  --speaker-col speaker_id --utt-col audio_path --label-col label ^
  --text-col text --contrast-col contrast --out data/splits.csv --seed 42

python member_a/03_verify_splits.py --splits data/splits.csv ^
  --annotations data/annotations.csv --audio-dir data/raw --contrast-col contrast

python member_a/make_phoneme_map.py --annotations data/annotations.csv
```

In VS Code use `Ctrl+Shift+B` for the smoke test, or the tasks
**A1 / A2 / A3** from `Terminal → Run Task`.

Adjust `--speaker-col`, `--utt-col`, `--label-col` to the real column names
printed by `01_audit.py`; the guesses are only defaults.

## Deliverables

| Item | Due | Acceptance |
|---|---|---|
| `data_audit_report.md` | day 2 | real counts: speakers, files, errors per contrast |
| Written scope decision (one contrast or two) | day 3 | justified by positive/negative counts |
| `data/splits.csv` + sha256 | day 4 | speaker-disjoint, frozen |
| `docs/phoneme_map.md` | day 4 | prompt → phoneme sequence → target + competitor |

## Decisions to make (not just scripts)

1. Can each contrast supply enough mispronounced examples?
   Below roughly 60–80 negatives per contrast, drop to one contrast.
2. Which prompts to keep (10–20 short, fully vowelised words/phrases).
3. If the test set ends up with fewer than ~30 errors, report the limitation
   instead of claiming a statistically meaningful F1 difference.

## Rules

- Do not edit `data/splits.csv` after it is frozen.
- Do not tune anything on the test split — that is Member C's red line too.
- Do not commit audio, `annotations.csv`, or archives.
