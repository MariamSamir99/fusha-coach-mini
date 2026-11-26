"""
Generate docs/phoneme_map.md from the annotation table.

The map answers one question per prompt: which sound is being judged, and which
sound is the expected confusion. Both are needed by member B (feature extraction)
and member D (highlighting the target letter in the UI).

Counts are read from the data, so the document never drifts from the corpus.
IPA strings are reference values only; the canonical phoneme sequence used at
inference time is produced by the phonemizer in member_b/.

Usage:
    python member_a/make_phoneme_map.py \
        --annotations data/annotations.csv \
        --out docs/phoneme_map.md
"""

import argparse
from pathlib import Path

import pandas as pd

TARGET_LETTERS = {"ح": "H", "ه": "H", "ص": "S", "س": "S"}

CONTRAST_INFO = {
    "H": {
        "target": "ح /ħ/ voiceless pharyngeal fricative",
        "competitor": "هـ /h/ glottal fricative",
        "cue": "ح is constricted deep in the throat; هـ is a light breath from the glottis",
    },
    "S": {
        "target": "ص /sˤ/ emphatic sibilant",
        "competitor": "س /s/ plain sibilant",
        "cue": "ص has a backed, lowered tongue body and a darker resonance; س is front and flat",
    },
}

HEADER = """# Phoneme map — target contrasts

Defines which sound is judged for every prompt and which sound the learner is
expected to confuse it with.

## Convention

- One judgement per **(utterance, target phoneme)** pair, not one per utterance.
  A word containing both target letters (e.g. صَبَاح) yields **two** rows, one per
  contrast.
- `label` is inherited from the utterance: `1 = mispronounced`, `0 = correct`.
- Canonical phoneme sequences are produced at runtime by the phonemizer in
  `member_b/`, never typed by hand, so the mapping stays reproducible. IPA below
  is reference material only.
- Prompts without a target letter are excluded: they cannot be scored.

## Contrasts

| id | target (correct) | competitor (expected confusion) | articulatory cue |
|---|---|---|---|
"""


def build_table(df):
    rows = []
    for word, group in df.groupby("text"):
        if not isinstance(word, str):
            continue
        for letter, contrast in TARGET_LETTERS.items():
            if letter in word:
                rows.append(dict(word=word, contrast=contrast, letter=letter,
                                 n=len(group), err=int(group["label"].sum())))
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["rate"] = (out["err"] / out["n"]).round(3)
    return out.sort_values(["contrast", "err"], ascending=[True, False])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", default="data/annotations.csv")
    ap.add_argument("--out", default="docs/phoneme_map.md")
    args = ap.parse_args()

    df = pd.read_csv(args.annotations)
    table = build_table(df)

    lines = [HEADER.rstrip()]
    for cid, info in CONTRAST_INFO.items():
        lines.append(f"| **{cid}** | {info['target']} | {info['competitor']} | {info['cue']} |")
    lines.append("")
    lines.append("## Prompts with a target phoneme")
    lines.append("")
    lines.append("Counts are read from `data/annotations.csv`. `error rate` is the observed")
    lines.append("label rate — useful for picking prompts that carry enough error examples.")
    lines.append("")

    for cid in CONTRAST_INFO:
        sub = table[table.contrast == cid]
        lines.append(f"### {cid}")
        lines.append("")
        lines.append("| word | target letter | utterances | mispronounced | error rate |")
        lines.append("|---|---|---|---|---|")
        for _, r in sub.iterrows():
            lines.append(f"| {r.word} | {r.letter} | {r.n} | {r.err} | {r.rate:.3f} |")
        lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")

    summary = table.groupby("contrast").agg(words=("word", "nunique"),
                                            utterances=("n", "sum"),
                                            errors=("err", "sum"))
    print(f"[ok] wrote {out}")
    print(summary.to_string())


if __name__ == "__main__":
    main()
