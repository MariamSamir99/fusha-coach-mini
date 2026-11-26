"""
Step 2 - speaker-disjoint split builder.

Splits by SPEAKER (never by utterance), keeps repeated takes of the same
prompt together automatically, balances the number of mispronounced examples
across splits, prints a summary table, and freezes the result with sha256.

The output file must not be edited afterwards. Any change means a new file
(splits_v2.csv) plus one line in docs/decisions.md.

Usage:
    python member_a/02_make_splits.py \
        --annotations data/L2KSU/annotations.csv \
        --speaker-col speaker_id --utt-col audio_path --label-col label \
        --out data/splits.csv --seed 42
"""

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

SPLITS = ["train", "val", "test"]

POSITIVE_VALUES = {"1", "1.0", "true", "yes", "wrong", "incorrect",
                   "mispronounced", "error", "err"}
NEGATIVE_VALUES = {"0", "0.0", "false", "no", "correct", "ok", "right", "good"}


def normalise_label(s):
    s = str(s).strip().lower()
    if s in POSITIVE_VALUES:
        return 1
    if s in NEGATIVE_VALUES:
        return 0
    return pd.NA


def duplicate_speaker_pairs(df, utt_col, spk_col, audio_dir):
    """Return speaker pairs that share at least one byte-identical recording.

    A duplicate across two speaker ids means the same recording can end up in
    two splits, which invalidates the evaluation. Cheap enough to run always:
    ~100 MB of audio hashes in about a second.
    """
    root = Path(audio_dir)
    if not root.exists():
        print(f"[warn] --audio-dir not found ({root}); integrity check skipped")
        return set()

    by_hash = defaultdict(set)
    hashed = 0
    for utt, spk in zip(df[utt_col].astype(str), df[spk_col].astype(str)):
        f = root / utt
        if not f.exists() or f.stat().st_size < 100:
            continue
        by_hash[hashlib.md5(f.read_bytes()).hexdigest()].add(spk)
        hashed += 1

    pairs = set()
    for speakers in by_hash.values():
        if len(speakers) > 1:
            ordered = sorted(speakers)
            for i, a in enumerate(ordered):
                for b in ordered[i + 1:]:
                    pairs.add((a, b))
    if hashed:
        print(f"[check] hashed {hashed} files; "
              f"{sum(1 for v in by_hash.values() if len(v) > 1)} duplicate groups "
              f"across speaker ids")
    return pairs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", required=True)
    ap.add_argument("--speaker-col", required=True)
    ap.add_argument("--utt-col", required=True, help="unique utterance id (usually the audio path)")
    ap.add_argument("--label-col", required=True, help="0/1, correct/wrong, ...")
    ap.add_argument("--text-col", default=None, help="prompt text (used to report repeated takes)")
    ap.add_argument("--contrast-col", default=None, help="optional: target contrast label")
    ap.add_argument("--out", default="data/splits.csv")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--ratios", default="0.6,0.2,0.2")
    ap.add_argument("--min-test-pos", type=int, default=30)
    ap.add_argument("--groups", default=None,
                    help="CSV mapping speaker_id,group_id - splits are built per group "
                         "(use when two ids share identical audio)")
    ap.add_argument("--group-speaker-col", default="speaker_id")
    ap.add_argument("--group-col", default="group_id")
    ap.add_argument("--audio-dir", default="data/raw",
                    help="used by the mandatory duplicate check")
    ap.add_argument("--no-integrity", action="store_true",
                    help="skip the duplicate check (not recommended)")
    args = ap.parse_args()

    try:
        ratios = [float(x) for x in args.ratios.split(",")]
    except ValueError:
        sys.exit("[error] --ratios must look like 0.6,0.2,0.2")
    if len(ratios) != 3 or abs(sum(ratios) - 1) > 1e-6:
        sys.exit("[error] --ratios needs three values summing to 1")

    df = pd.read_csv(args.annotations)
    for col in (args.speaker_col, args.utt_col, args.label_col):
        if col not in df.columns:
            sys.exit(f"[error] column '{col}' not found in {list(df.columns)}")

    df = df.copy()
    df["_label"] = df[args.label_col].map(normalise_label)
    bad = int(df["_label"].isna().sum())
    if bad:
        seen = df.loc[df["_label"].isna(), args.label_col].astype(str).unique()[:10]
        print(f"[warn] dropping {bad} rows with an unrecognised label. Values seen: {list(seen)}")
        df = df[df["_label"].notna()].copy()
    df["_label"] = df["_label"].astype(int)
    df["_speaker"] = df[args.speaker_col].astype(str)

    # ---- mandatory integrity gate -------------------------------------------------
    # Refuse to build a split that could leak: two speaker ids sharing identical
    # audio must be declared as one group first.
    if not args.no_integrity:
        pairs = duplicate_speaker_pairs(df, args.utt_col, args.speaker_col, args.audio_dir)
        if pairs:
            if args.groups:
                print(f"[ok] {len(pairs)} duplicate speaker pair(s) declared; "
                      "splitting will keep each pair together")
            else:
                shown = ", ".join(f"{a} = {b}" for a, b in sorted(pairs)[:5])
                sys.exit(
                    "[refused] byte-identical recordings are shared by different speaker ids:\n"
                    f"          {shown}\n"
                    "          Splitting now would place the same recording in two splits.\n"
                    "          Fix:\n"
                    "            python member_a/06_check_integrity.py --splits data/splits.csv\n"
                    "            python member_a/02_make_splits.py ... --groups data/speaker_groups.csv\n"
                    "          (or pass --no-integrity if you are certain this is intentional)"
                )

    # Speaker ids that share identical audio must move together.
    df["_group"] = df["_speaker"]
    if args.groups:
        gm = pd.read_csv(args.groups, dtype=str)
        mapping = dict(zip(gm[args.group_speaker_col], gm[args.group_col]))
        df["_group"] = df["_speaker"].map(mapping).fillna(df["_speaker"])
        n_merged = df["_speaker"].nunique() - df["_group"].nunique()
        if n_merged:
            print(f"[info] {n_merged} speaker id(s) merged into shared groups; "
                  f"{df['_speaker'].nunique()} ids -> {df['_group'].nunique()} groups")

    # ---- per-group table ----
    spk = (df.groupby("_group")
             .agg(n_utt=("_label", "size"), n_pos=("_label", "sum"),
                  n_speakers=("_speaker", "nunique"))
             .reset_index())
    if len(spk) < 5:
        sys.exit(f"[error] only {len(spk)} speaker groups - speaker-disjoint splitting is "
                 "meaningless at this size.")

    # ---- greedy balanced assignment ----
    # Shuffle for tie-breaking, then place the biggest contributors first into
    # whichever split is furthest below its target share of errors and rows.
    spk = spk.sample(frac=1, random_state=args.seed).reset_index(drop=True)
    spk = spk.sort_values("n_pos", ascending=False, kind="mergesort").reset_index(drop=True)

    total_pos, total_utt = spk["n_pos"].sum(), spk["n_utt"].sum()
    target_pos = [r * total_pos for r in ratios]
    target_utt = [r * total_utt for r in ratios]
    got_pos = [0, 0, 0]
    got_utt = [0, 0, 0]
    assign = {}

    for _, row in spk.iterrows():
        fill = [
            (got_pos[i] / target_pos[i] if target_pos[i] else 0.0)
            + (got_utt[i] / target_utt[i] if target_utt[i] else 0.0)
            for i in range(3)
        ]
        i = int(min(range(3), key=lambda k: fill[k]))
        assign[row["_group"]] = SPLITS[i]
        got_pos[i] += row["n_pos"]
        got_utt[i] += row["n_utt"]

    df["split"] = df["_group"].map(assign)

    # ---- leakage checks (on groups, not ids) ----
    sets = {s: set(df.loc[df["split"] == s, "_group"]) for s in SPLITS}
    for a, b in (("train", "val"), ("train", "test"), ("val", "test")):
        if sets[a] & sets[b]:
            sys.exit(f"[FATAL] speaker group overlap between {a} and {b}")
    spk_sets = {s: set(df.loc[df["split"] == s, "_speaker"]) for s in SPLITS}

    # ---- summary ----
    print("\n" + "=" * 70)
    print(f"{'split':6}{'groups':>8}{'speakers':>10}{'utts':>8}{'wrong':>7}{'pos_rate':>10}")
    print("=" * 70)
    for s in SPLITS:
        sub = df[df["split"] == s]
        pos = int(sub["_label"].sum())
        print(f"{s:6}{len(sets[s]):>8}{len(spk_sets[s]):>10}{len(sub):>8}{pos:>7}"
              f"{pos / max(len(sub), 1):>10.3f}")
    print("=" * 70)

    # ---- warnings ----
    test_pos = int(df.loc[df["split"] == "test", "_label"].sum())
    if test_pos < args.min_test_pos:
        print(f"\n[WARN] test has only {test_pos} mispronounced examples "
              f"(< {args.min_test_pos}). An F1 difference would be noise.\n"
              "       -> use a single contrast, or report the limitation explicitly "
              "instead of claiming a reliable result.")

    if args.text_col and args.text_col in df.columns:
        key = df["_speaker"].astype(str) + "||" + df[args.text_col].astype(str)
        n_rep = int(key.duplicated(keep=False).sum())
        if n_rep:
            print(f"[info] {n_rep} rows are repeated takes of the same speaker+prompt; "
                  "they stay in the same split because splits are defined per speaker.")

    # ---- write + freeze ----
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = [args.utt_col, args.speaker_col, "split", "_label"]
    if args.groups:
        cols.insert(2, "_group")
    if args.text_col and args.text_col in df.columns:
        cols.append(args.text_col)
    if args.contrast_col and args.contrast_col in df.columns:
        cols.append(args.contrast_col)

    rename = {"_label": "label", "_group": "group_id"}
    df[cols].rename(columns=rename).to_csv(out, index=False, encoding="utf-8")

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    Path(str(out) + ".sha256").write_text(digest + "\n", encoding="utf-8")

    meta = {
        "source": str(args.annotations),
        "seed": args.seed,
        "ratios": ratios,
        "sha256": digest,
        "groups_used": bool(args.groups),
        "counts": {s: int((df["split"] == s).sum()) for s in SPLITS},
        "positives": {s: int(df.loc[df["split"] == s, "_label"].sum()) for s in SPLITS},
        "groups": {s: sorted(sets[s]) for s in SPLITS},
        "speakers": {s: sorted(spk_sets[s]) for s in SPLITS},
    }
    Path(str(out) + ".meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[ok] wrote {out}")
    print(f"[ok] sha256 = {digest[:16]}...  ->  {out}.sha256")
    print("[next] run 03_verify_splits.py before handing this file to the team")


if __name__ == "__main__":
    main()
