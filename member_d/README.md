# Member D — demo, integration, packaging

Turns the pipeline into something that runs in front of the class, with numbers
that match the report.

## Deliverables

| File | Contents |
|---|---|
| `app.py` | single-page Gradio app |
| `member_d/latency.md` | per-stage timing: preprocess / inference / features / classify |
| `requirements-demo.txt` | pinned dependencies |
| demo script | 3-minute walkthrough, including one "uncertain — retry" case |

## App behaviour

1. Pick a prompt from the list (10–20 prompts, target letter highlighted).
2. Record from the microphone or upload a file.
3. Output: decision (`correct` / `needs practice` / `uncertain — please retry`),
   probability, one short English articulation tip for that contrast, retry button.

## Integration rules (the part that actually matters)

- Import `preprocess()` from `member_b/preprocess.py` — do not reimplement it.
- Load the model and the saved threshold once at startup, not per request.
- The abstention threshold is the one selected on validation by Member C,
  never a hardcoded 0.5.
- The predicted decision for a given file must be identical to the row in
  `runs/final/preds.csv`.

## Integration test

Run 10 real files through the app and diff against `runs/*/preds.csv`.
Any mismatch is a bug in the demo, not in the model.

## Packaging checklist

- [ ] `pip install -r requirements.txt -r requirements-demo.txt` on a clean machine
- [ ] `python app.py` starts without warnings
- [ ] no audio, no gated files, no `*.parquet` committed
- [ ] `.gitignore` still covers `data/raw/` and `data/annotations.csv`
- [ ] latency figures recorded (mean and p95)

## Review duty

You review Member B's feature extraction (is it reproducible from the README?).
