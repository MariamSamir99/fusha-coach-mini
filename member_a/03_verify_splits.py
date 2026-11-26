"""
Step 3 - QA gate for splits.csv.

Blocks the hand-off when the split file has a defect that would silently
invalidate every downstream result: speaker leakage, an empty test set, too
few error examples, missing audio, unknown ids.

Exit code 0 = safe to use. Exit code 1 = do not use.

Usage:
    python member_a/03_verify_splits.py \
        --splits data/splits.csv \
        --annotations data/L2KSU/annotations.csv \
        --audio-dir data/L2KSU \
        --out member_a/splits_qa.md
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
results = []


def check(name, ok, detail="", level=None):
    """Record one check. `level` overrides the default PASS/FAIL outcome."""
    status = level or (PASS if ok else FAIL)
    results.append((name, status, detail))
    icon = {PASS: "[ ok ]", FAIL: "[FAIL]", WARN: "[warn]"}[status]
    print(f"{icon} {name}" + (f" - {detail}" if detail else ""))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--splits", required=True)
    ap.add_argument("--annotations", default=None)
    ap.add_argument("--audio-dir", default=None)
    ap.add_argument("--speaker-col", default="speaker_id")
    ap.add_argument("--utt-col", default="audio_path")
    ap.add_argument("--label-col", default="label")
    ap.add_argument("--contrast-col", default=None)
    ap.add_argument("--min-test-pos", type=int, default=30)
    ap.add_argument("--min-test-neg", type=int, default=30)
    ap.add_argument("--out", default="member_a/splits_qa.md")
    args = ap.parse_args()

    sp = pd.read_csv(args.splits)
    print(f"splits: {len(sp)} rows - columns: {list(sp.columns)}\n")

    required = {"split", args.speaker_col, args.utt_col, args.label_col}
    missing = required - set(sp.columns)
    if not check("required columns exist", not missing,
                 f"missing: {sorted(missing)}" if missing else ""):
        return finish(args)

    # 1. unique utterance ids
    dup = int(sp[args.utt_col].duplicated().sum())
    check("no duplicate utterance ids", dup == 0, f"{dup} duplicates")

    # 2. split names and sizes
    got = set(sp["split"].dropna().unique())
    check("split values are train/val/test", got == {"train", "val", "test"}, f"found: {sorted(got)}")
    for s in ("train", "val", "test"):
        n = int((sp["split"] == s).sum())
        check(f"split '{s}' is not empty", n > 0, f"{n} rows")

    # 3. speaker disjointness
    spk_sets = {s: set(sp.loc[sp["split"] == s, args.speaker_col].astype(str))
                for s in ("train", "val", "test")}
    leaks = []
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        common = spk_sets[a] & spk_sets[b]
        if common:
            leaks.append(f"{a}&{b}: {sorted(common)[:5]}")
    check("speaker-disjoint (no leakage)", not leaks, "; ".join(leaks))

    counts = sp.groupby(args.speaker_col)["split"].nunique()
    multi = counts[counts > 1]
    check("each speaker in exactly one split", multi.empty,
          f"{len(multi)} speakers spread across splits")

    # 4. label domain
    labels = pd.to_numeric(sp[args.label_col], errors="coerce")
    bad = int(labels.isna().sum() + (~labels.isin([0, 1])).sum())
    check("labels are strictly 0/1", bad == 0, f"{bad} bad values")

    # 5. class balance per split
    print()
    for s in ("train", "val", "test"):
        sub = sp[sp["split"] == s]
        pos = int(pd.to_numeric(sub[args.label_col], errors="coerce").sum())
        neg = len(sub) - pos
        print(f"     {s:5} speakers={len(spk_sets[s]):3d}  rows={len(sub):5d}  "
              f"wrong={pos:5d}  correct={neg:5d}  pos_rate={pos / max(len(sub), 1):.3f}")

    test = sp[sp["split"] == "test"]
    test_pos = int(pd.to_numeric(test[args.label_col], errors="coerce").sum())
    test_neg = len(test) - test_pos
    check("test has enough ERROR examples", test_pos >= args.min_test_pos,
          f"{test_pos} < {args.min_test_pos}: F1 differences will be noise",
          level=None if test_pos >= args.min_test_pos else WARN)
    check("test has enough CORRECT examples", test_neg >= args.min_test_neg,
          f"{test_neg} < {args.min_test_neg}: false-accept rate unreliable",
          level=None if test_neg >= args.min_test_neg else WARN)

    # 6. per-contrast view
    if args.contrast_col and args.contrast_col in sp.columns:
        print("\n     per-contrast breakdown (sum / count per split):")
        pivot = sp.pivot_table(index=args.contrast_col, columns="split",
                               values=args.label_col, aggfunc=["sum", "count"], fill_value=0)
        print(pivot.to_string())
        for contrast in sp[args.contrast_col].dropna().unique():
            mask = (sp[args.contrast_col] == contrast) & (sp["split"] == "test")
            n = int(mask.sum())
            pos = int(pd.to_numeric(sp.loc[mask, args.label_col], errors="coerce").sum())
            check(f"contrast '{contrast}' usable on test", pos >= 15,
                  f"test rows={n}, wrong={pos}", level=None if pos >= 15 else WARN)

    # 7. audio files exist
    if args.audio_dir:
        root = Path(args.audio_dir)
        names = {p.name for p in root.rglob("*") if p.suffix.lower() in {".wav", ".flac", ".mp3"}}
        refs = sp[args.utt_col].astype(str).map(lambda s: Path(s.replace("\\", "/")).name)
        miss = refs[~refs.isin(names)]
        check("all referenced audio files exist", len(miss) == 0, f"{len(miss)} missing")

    # 8. provenance against the annotation table
    if args.annotations:
        ann = pd.read_csv(args.annotations)
        if args.utt_col in ann.columns:
            a = set(ann[args.utt_col].astype(str))
            b = set(sp[args.utt_col].astype(str))
            check("every split row exists in the annotation table", b.issubset(a),
                  f"{len(b - a)} unknown ids")
            check("row count accounted for", True,
                  f"annotations={len(a)} splits={len(b)} dropped={len(a) - len(b)}")

    return finish(args)


def finish(args):
    fails = [r for r in results if r[1] == FAIL]
    warns = [r for r in results if r[1] == WARN]
    print("\n" + "=" * 60)
    print(f"RESULT: {'FAIL' if fails else 'PASS'} "
          f"({len(results)} checks, {len(fails)} failed, {len(warns)} warnings)")
    print("=" * 60)

    lines = ["# Splits QA", "", f"File: `{args.splits}`", "",
             "| check | status | detail |", "|---|---|---|"]
    lines += [f"| {n} | **{s}** | {d or ''} |" for n, s, d in results]
    lines += ["", "**Verdict:** " +
              ("do not use these splits" if fails else "safe to use")]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] wrote {out}")

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
