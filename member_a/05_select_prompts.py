"""
Step 5 - select the demo prompt list (Member A deliverable).

Picks the 10-20 prompts that carry the most error examples per contrast, so the
demo and the evaluation use words that actually exercise the target phoneme.
Writes a machine-readable table (docs/prompts.csv) plus a readable page
(docs/prompts.md) that member D can wire straight into the Gradio app: the
Arabic prompt, the letters to highlight, and one short English articulatory tip.

Usage:
    python member_a/05_select_prompts.py --per-contrast 8 --min-utts 20
"""

import argparse
from pathlib import Path

import pandas as pd

LETTERS = {"ح": "H", "ه": "H", "ص": "S", "س": "S"}

TIPS = {
    "H": [
        "For ح the friction is deep in the throat, not at the lips. Say a tired "
        "'ahh' and tighten the pharynx.",
        "هـ is a light breath from the open glottis. If you hear friction like "
        "clearing your throat, you said ح instead.",
        "Hold the constriction of ح through the vowel that follows it; do not let "
        "it relax into هـ at the end of the word.",
        "Think of fogging a mirror very softly: that is هـ. ح needs visible effort "
        "in the throat.",
    ],
    "S": [
        "For ص pull the tongue body back and hollow the mouth; the sound is darker "
        "and heavier than س.",
        "س is a front hiss near the teeth. In ص the tongue retreats and the "
        "resonance moves to the back of the mouth.",
        "Keep the emphasis of ص through the whole syllable - it colours the "
        "neighbouring vowels.",
        "If ص sounds like a plain س, the tongue tip is too far forward. Retract it "
        "and lower the jaw slightly.",
    ],
}

HEADER = """# Demo prompts

Selected from the working corpus by error frequency, so every prompt exercises
the target phoneme with real mispronunciations behind it.

- `contrast` H = ح vs هـ, S = ص vs س
- `target_letter` is what the app should highlight
- `tip_en` is the one-line feedback shown after the judgement
- counts come from `data/annotations.csv` at build time
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", default="data/annotations.csv")
    ap.add_argument("--splits", default="data/splits.csv")
    ap.add_argument("--per-contrast", type=int, default=8)
    ap.add_argument("--min-utts", type=int, default=20)
    ap.add_argument("--out-csv", default="docs/prompts.csv")
    ap.add_argument("--out-md", default="docs/prompts.md")
    args = ap.parse_args()

    df = pd.read_csv(args.annotations)
    df["contrast"] = df["contrast"].fillna("")

    rows = []
    for contrast in ("H", "S"):
        pool = df[df.contrast.str.contains(contrast)]
        stats = (pool.groupby("text")
                     .agg(n=("label", "size"), errors=("label", "sum"))
                     .reset_index())
        stats = stats[stats.n >= args.min_utts]
        stats = stats.sort_values(["errors", "n"], ascending=False)
        for _, r in stats.head(args.per_contrast).iterrows():
            letters = [l for l, c in LETTERS.items() if c == contrast and l in str(r.text)]
            if not letters:
                continue
            rows.append(dict(prompt_id=f"{contrast}{len([x for x in rows if x['contrast'] == contrast]) + 1:02d}",
                             arabic=r.text, contrast=contrast,
                             target_letter="".join(letters),
                             n_utts=int(r.n), n_errors=int(r.errors),
                             error_rate=round(r.errors / r.n, 3)))

    out = pd.DataFrame(rows)
    if out.empty:
        raise SystemExit("[error] no prompt passed the filters - lower --min-utts")

    # assign tips round-robin within each contrast
    out["tip_en"] = ""
    for c in ("H", "S"):
        idx = out.index[out.contrast == c].tolist()
        for i, j in enumerate(idx):
            out.at[j, "tip_en"] = TIPS[c][i % len(TIPS[c])]

    csv_path = Path(args.out_csv)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(csv_path, index=False, encoding="utf-8")

    lines = [HEADER.rstrip(), "",
             "| id | prompt | contrast | highlight | utterances | errors |",
             "|---|---|---|---|---|---|"]
    for _, r in out.iterrows():
        lines.append(f"| {r.prompt_id} | {r.arabic} | {r.contrast} | {r.target_letter} "
                     f"| {r.n_utts} | {r.n_errors} |")
    lines += ["", "## Feedback lines", ""]
    for _, r in out.iterrows():
        lines.append(f"- **{r.arabic}** ({r.prompt_id}): {r.tip_en}")
    Path(args.out_md).write_text("\n".join(lines), encoding="utf-8")

    print(f"[ok] {len(out)} prompts -> {csv_path} and {args.out_md}")
    print(out.groupby("contrast").agg(prompts=("arabic", "nunique"),
                                      errors=("n_errors", "sum")).to_string())


if __name__ == "__main__":
    main()
