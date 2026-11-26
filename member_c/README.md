# Member C — classifier, training curves, evaluation

Owns the scientific claim of the project: does a light calibration layer beat
the direct-decoding baseline on unseen speakers?

## Inputs

- `data/splits.csv` (Member A) — frozen split membership
- `data/features.parquet` (Member B) — one row per utterance

## Ladder of models

| Step | Model | Notes |
|---|---|---|
| 0 | Baseline | direct phone mismatch from `runs/baseline/preds.csv` |
| 1 | Logistic regression | `class_weight="balanced"`, StandardScaler inside the pipeline, `C` swept on validation |
| 2 | Small MLP | 1–2 hidden layers, 50–200 units, dropout, early stopping on validation F1 |

Fitting only ever uses the `train` split; thresholds and hyperparameters are
selected on `val`; `test` is evaluated once, at the end.

## Training curves — the week-10 deliverable

Six figures, each with the numbers stored in `metrics.json`:

1. **Loss curve** — train vs validation loss per epoch (MLP) or per iteration
   (logistic regression). Label the axis correctly: these are not epochs for LR.
2. **F1 curve** — validation macro-F1 per epoch, with the selected (early-stopped) point marked.
3. **Hyperparameter sweep** — F1 against `C` (LR) or hidden size / lr / weight decay (MLP).
4. **Learning curve** — F1 against training-set fraction (10/25/50/75/100%), mean ± std over 3 folds.
5. **Abstention curve** — F1 and coverage against the abstention threshold.
6. **PR and ROC** — baseline vs improved on validation.

## Outputs

```
runs/<exp_name>/
├── config.yaml      hypothesis + hyperparameters
├── metrics.json     all numbers used in the report
├── preds.csv        audio_path, p_mis, pred, abstain
└── curves.png       all six panels
```

Final comparison in `runs/final/metrics_test.json`:
macro-F1 per contrast, averaged macro-F1, precision/recall per class,
false-rejection rate on correct sounds, confusion matrices, and the absolute
difference (percentage points) versus baseline.

## Failure analysis

Inspect 15–20 held-out errors and classify each one:
recogniser error / alignment error / short-vowel or boundary issue /
noisy audio / genuine difficult pronunciation.

## Rules

- One test evaluation, after every decision is frozen.
- No number appears in the report unless it exists in `runs/`.
- If validation and test disagree badly (e.g. 0.95 vs 0.55), the cause is a
  leak or a feature problem: go back to Member B, do not tune harder.
- Accountability is for methodology and honest reporting, not for a positive
  result. "No improvement measured" is an acceptable outcome if reported cleanly.

## Review duty

You review Member A's split logic.
