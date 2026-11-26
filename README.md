# fusha-coach-mini

Phoneme-level mispronunciation detection for non-native learners of Modern Standard Arabic (MSA) — Speech Recognition course project.

Targeted phoneme-level pronunciation feedback for non-native learners of Modern Standard Arabic.
Two contrasts (ح/هـ, ص/س), frozen wav2vec2 baseline, calibrated error detection, speaker-disjoint
evaluation, and a single-page Gradio demo.

> Note on granularity: the working corpus labels whole utterances, so detection is evaluated at
> **word** level with phoneme posteriors as model features. The audit behind that decision and the
> measured label noise are recorded in `docs/decisions.md` and `member_a/label_findings.md`.

Course project — Speech Recognition, Zewail City of Science, Technology and Innovation.

The system takes a prompted MSA word/phrase plus a learner recording and classifies the
pronunciation of one target consonant as **acceptable** or **mispronounced**, with
conservative (abstaining) feedback. Two contrasts are targeted: /ħ/ vs /h/ (ح / هـ) and
/sˤ/ vs /s/ (ص / س).

---

## Team ownership

| Member | Area | Folder | Main artefacts |
|---|---|---|---|
| **A** | Data audit, splits, phoneme map | `member_a/` | `data/splits.csv`, `member_a/data_audit_report.md` |
| **B** | Baseline ASR, alignment, features | `member_b/` | `data/features.parquet`, `runs/baseline/metrics.json` |
| **C** | Classifier, training curves, evaluation | `member_c/` | `runs/<exp>/`, `runs/final/metrics_test.json` |
| **D** | Gradio demo, integration, docs | `member_d/` | `app.py`, `member_d/latency.md` |

Each member reviews one other member's component before the deadline.
Review rotation: A→C, B→D, C→A, D→B.

---

## Repository layout

```
.
├── member_a/            data audit, splits, QA gate
├── member_b/            baseline inference, alignment, feature extraction
├── member_c/            classifier training, curves, evaluation
├── member_d/            Gradio app, latency, packaging
├── data/                raw audio + annotations (NOT committed) + frozen splits.csv
├── runs/                one folder per experiment: config, metrics, curves
├── docs/                reports, phoneme map, decisions log
├── requirements.txt     core (pandas, soundfile, sklearn, matplotlib)
├── requirements-ml.txt  Member B only (torch, transformers) - needs Python 3.12
└── requirements-demo.txt Member D only (gradio)
```

---

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# verify the local environment with synthetic data (no download needed)
python member_a/00_smoke_test.py
```

In VS Code: `Ctrl+Shift+B` runs the default task (smoke test).
`F5` debugs the file currently open in the editor.

---

## Data rules

1. **Never commit** audio, `annotations.csv`, archives, or model weights.
   The corpus is gated and licensed CC BY-NC-ND 4.0.
2. `data/splits.csv` **is** committed — it is a frozen deliverable.
   It must not be edited. Any change requires a new `splits_v2.csv` and one line
   in `docs/decisions.md`.
3. Splits are **speaker-disjoint**. An utterance-level split invalidates every result.
4. The held-out **test set is touched once**, at the very end. No threshold tuning on test.

---

## Interface contract between members

Downstream code depends only on these files, never on each other's internals.

| File | Written by | Required columns |
|---|---|---|
| `data/splits.csv` | A | `audio_path, speaker_id, split, label [, text, contrast]` |
| `data/features.parquet` | B | `audio_path, speaker_id, split, label, contrast, <feature columns>` |
| `runs/<exp>/preds.csv` | C | `audio_path, p_mis, pred, abstain` |
| `runs/<exp>/metrics.json` | C | `macro_f1, precision, recall, per_contrast, threshold` |

`label` is always `1 = mispronounced`, `0 = correct`.

---

## Git workflow

```powershell
# one branch per member, one branch per task
git switch -c member-a/data-audit

git add <files>
git commit -m "A: add speaker-disjoint split script"
git push -u origin member-a/data-audit
```

Open a pull request into `main`. The reviewer assigned above approves it.
Keep `main` always runnable: `python member_a/00_smoke_test.py` must pass on `main`.

Commit message prefixes: `A:`, `B:`, `C:`, `D:`, `docs:`, `fix:`.

---

## Milestones

| Week | Deliverable | Owner |
|---|---|---|
| 7 | Data/licence audit, frozen split protocol, baseline scores | A, B |
| 10 | Working system + training curves + quantitative comparison | B, C, D |
| 13 | Final report, code, working demo | all |

Research vs engineering split: 70% rigorous evaluation and honest error analysis,
30% demo usability.
