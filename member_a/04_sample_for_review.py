"""
Step 4 - label spot-check (Member A quality gate).

The corpus labels whole utterances (1 = the recording is mispronounced), not
individual phonemes. Before member B and C build anything on top of that, sample
a handful of errors per contrast and listen: is the error actually on the target
letter, or somewhere else in the word?

This script copies the sampled files into a review folder and writes a sheet
with an empty `verdict` column. Fill it while listening, then run the same
script with --summarize to get the agreement rate that goes into the report.

Usage:
    python member_a/04_sample_for_review.py --per-contrast 15
    # ... listen, fill member_a/review/review_sheet.csv ...
    python member_a/04_sample_for_review.py --summarize
"""

import argparse
import shutil
from pathlib import Path

import pandas as pd

LETTERS = {"ح": "H", "ه": "H", "ص": "S", "س": "S"}

VERDICT_HELP = """
Listening instructions
----------------------
For every sampled file, write one of these in the `verdict` column:

  target    the error is on the target letter (ح/هـ or ص/س)      <- what we hope
  other     the word is wrong, but the error is on a different letter
  none      the recording sounds correct to me (label noise)
  unsure    cannot tell (noise, clipping, too short)

A high `target` share means the word-level label is a usable proxy for
target-phoneme error. A high `other`/`none` share means the task has to be
reframed as word-level mispronunciation, and that must be stated in the report.
"""


def sample(df, splits, per_contrast, seed):
    sp = pd.read_csv(splits, dtype={"speaker_id": str})
    key = "audio_path"
    df = df.merge(sp[[key, "split"]], on=key, how="inner")

    rows = []
    for contrast in ("H", "S"):
        pool = df[(df.split == "test") & (df.label == 1) &
                  (df.contrast.fillna("").str.contains(contrast))]
        if pool.empty:
            print(f"[warn] no test errors for contrast {contrast}")
            continue
        take = min(per_contrast, len(pool))
        picked = pool.sample(n=take, random_state=seed)
        for _, r in picked.iterrows():
            letters = [l for l, c in LETTERS.items() if c == contrast and l in str(r.text)]
            rows.append(dict(file=r[key], word=r.text, contrast=contrast,
                             target_letter="".join(letters), speaker_id=r.speaker_id,
                             verdict="", notes=""))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", default="data/annotations.csv")
    ap.add_argument("--splits", default="data/splits.csv")
    ap.add_argument("--audio-dir", default="data/raw")
    ap.add_argument("--review-dir", default="member_a/review")
    ap.add_argument("--per-contrast", type=int, default=15)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--summarize", action="store_true")
    args = ap.parse_args()

    review = Path(args.review_dir)
    sheet = review / "review_sheet.csv"

    if args.summarize:
        if not sheet.exists():
            raise SystemExit(f"[error] {sheet} not found - run the sampling step first")
        df = pd.read_csv(sheet)
        filled = df[df.verdict.fillna("").str.strip() != ""]
        if filled.empty:
            raise SystemExit("[error] the verdict column is still empty")
        print(f"reviewed {len(filled)} / {len(df)} sampled errors\n")
        print(filled.groupby(["contrast", "verdict"]).size().to_string())
        print()
        for c, g in filled.groupby("contrast"):
            share = (g.verdict == "target").mean()
            print(f"  {c}: target-phoneme errors = {share:.0%} ({int((g.verdict == 'target').sum())}"
                  f"/{len(g)})")
        overall = (filled.verdict == "target").mean()
        print(f"\n  overall = {overall:.0%}")
        print(f"  -> write this number into the report's limitations section")
        return

    df = pd.read_csv(args.annotations)
    df["contrast"] = df["contrast"].fillna("")
    sampled = sample(df, args.splits, args.per_contrast, args.seed)
    if sampled.empty:
        raise SystemExit("[error] nothing sampled - check splits/annotations paths")

    review.mkdir(parents=True, exist_ok=True)
    review_paths = []
    for _, r in sampled.iterrows():
        src = Path(args.audio_dir) / r.file
        # keep the speaker folder: basenames repeat across speakers (26_N.wav ...)
        dest = review / r.contrast / Path(r.file)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dest)
            review_paths.append(dest.as_posix())
        else:
            review_paths.append("")
            print(f"[warn] missing audio: {src}")

    sampled["review_path"] = review_paths
    sampled.to_csv(sheet, index=False, encoding="utf-8")
    print(f"[ok] {len(sampled)} files copied to {review}/<H|S>/")
    print(f"[ok] sheet: {sheet}")
    print(f"[info] contrast split: {sampled.contrast.value_counts().to_dict()}")
    print(VERDICT_HELP)
    print("When finished: python member_a/04_sample_for_review.py --summarize")


if __name__ == "__main__":
    main()
