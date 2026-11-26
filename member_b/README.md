# Member B — baseline ASR, alignment, feature extraction

Turns audio into a table. Member C trains only on the table this folder
produces, so a defect here shows up later as "the model does not improve".

## Scope

- Pretrained model: `MostafaMaroof/wav2vec2-arabic-phoneme-asr` (frozen weights)
- One preprocessing function used by both evaluation and the demo
- Baseline decision: CTC decode, align, direct phone mismatch
- Feature table for the calibrated model

## Environment

PyTorch has no wheels for Python 3.14 yet, so use 3.12 for this folder:

```powershell
py -3.12 -m venv .venv312
.\.venv312\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-ml.txt
```

## Required files

| File | Contents |
|---|---|
| `preprocess.py` | `preprocess(path) -> np.ndarray` — 16 kHz mono, trimmed, length-capped, amplitude-normalised |
| `run_baseline.py` | inference over `data/splits.csv`, writes `runs/baseline/` |
| `extract_features.py` | writes `data/features.parquet` |
| `docs/features.md` | one line per feature: what it is and how it is computed |

## Feature table contract

One row per utterance. Required columns:

```
audio_path, speaker_id, split, label, contrast,
p_correct, p_competitor, margin, ratio,
max_confidence, entropy, mean_neighbour_confidence,
align_ok, n_del, n_ins, n_sub, target_frames, rel_position,
duration_sec, num_frames, energy
```

Rules:

- `p_correct` = posterior of the canonical phoneme at the target position
- `p_competitor` = posterior of the contrasting phoneme (ح vs هـ, ص vs س)
- nothing derived from `label` may enter the features (no leakage)
- one run for the whole dataset; the table is frozen once written

## Outputs

- `runs/baseline/metrics.json` — macro-F1, precision, recall, PER
- `runs/baseline/preds.csv` — `audio_path, p_mis, pred, abstain`
- `data/features.parquet`

## Watch out

- Same `audio_path` set as `data/splits.csv`, no re-filtering.
- Assert `samplerate == 16000` explicitly; mixed rates silently break features.
- Verify the model's label vocabulary actually contains ح / هـ / س / ص.
  If one is missing, report it immediately — it changes the project scope.
- Report inference time; Member D needs the number for the demo section.

## Review duty

You review Member D's demo (numbers must match `runs/*/preds.csv`).
