"""
Step 6 - integrity check (Member A).

Answers the questions that decide whether the split file can be trusted at all:

  * is every audio file non-empty and long enough to score?
  * do any two files contain byte-identical audio?
  * if yes, do those duplicates sit in different splits (leakage)?
  * do any duplicates carry conflicting labels (label contradiction)?
  * which speaker ids are really the same speaker?

Byte-identical audio under two different speaker ids means the same recording
can land in train and in test. The fix is to treat those ids as one speaker
group and split on the group.

Writes member_a/integrity_report.md and data/speaker_groups.csv.

Usage:
    python member_a/06_check_integrity.py \
        --splits data/splits.csv --out-groups data/speaker_groups.csv
"""

import argparse
import hashlib
from collections import defaultdict
from pathlib import Path

import pandas as pd

SHORT_SEC = 0.15


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def cluster_speakers(pairs):
    """Union-find over speaker ids that share identical audio."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            # keep the lexicographically smaller id as the representative
            if rb < ra:
                ra, rb = rb, ra
            parent[rb] = ra

    for a, b in pairs:
        union(a, b)
    return {s: find(s) for s in parent}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", default="data/annotations.csv")
    ap.add_argument("--audio-dir", default="data/raw")
    ap.add_argument("--splits", default=None, help="optional: report split leakage")
    ap.add_argument("--out-report", default="member_a/integrity_report.md")
    ap.add_argument("--out-groups", default="data/speaker_groups.csv")
    args = ap.parse_args()

    ann = pd.read_csv(args.annotations)
    root = Path(args.audio_dir)
    split_of = {}
    if args.splits:
        sp = pd.read_csv(args.splits)
        split_of = dict(zip(sp.audio_path, sp.split))

    # ---- per-file checks ----
    empty, short, hashes = [], [], defaultdict(list)
    import soundfile as sf
    for p in ann.audio_path:
        f = root / p
        if not f.exists():
            empty.append((p, "missing"))
            continue
        if f.stat().st_size < 100:
            empty.append((p, "empty file"))
            continue
        try:
            info = sf.info(str(f))
            dur = info.frames / max(info.samplerate, 1)
            if dur < SHORT_SEC:
                short.append((p, round(dur, 3)))
        except Exception as exc:
            empty.append((p, f"unreadable: {exc}"))
            continue
        hashes[md5(f)].append(p)

    dups = {h: v for h, v in hashes.items() if len(v) > 1}
    label = dict(zip(ann.audio_path, ann.label))
    speaker = dict(zip(ann.audio_path, ann.speaker_id.astype(str)))

    cross_split, conflicts, pairs = [], [], set()
    for h, files in dups.items():
        splits = {split_of.get(p) for p in files if p in split_of}
        if len(splits) > 1:
            cross_split.append((files, splits))
        labels = {label.get(p) for p in files}
        if len(labels) > 1:
            conflicts.append((files, labels))
        spk = {speaker.get(p) for p in files}
        if len(spk) > 1:
            pairs.update({tuple(sorted((a, b))) for a in spk for b in spk if a < b})

    clusters = cluster_speakers(pairs)
    groups = {s: clusters.get(s, s) for s in ann.speaker_id.astype(str).unique()}

    # ---- write speaker groups ----
    pd.DataFrame({"speaker_id": list(groups), "group_id": [groups[s] for s in groups]}) \
        .sort_values("speaker_id").to_csv(args.out_groups, index=False, encoding="utf-8")

    # ---- report ----
    merged = {g: sorted(s for s, v in groups.items() if v == g) for g in set(groups.values())}
    merged = {g: s for g, s in merged.items() if len(s) > 1}

    print("=" * 66)
    print("INTEGRITY")
    print("=" * 66)
    print(f"files checked          : {len(ann)}")
    print(f"empty / unreadable     : {len(empty)}")
    print(f"shorter than {SHORT_SEC}s       : {len(short)}")
    print(f"byte-identical groups  : {len(dups)}")
    print(f"  ...crossing splits   : {len(cross_split)}")
    print(f"  ...label conflicts   : {len(conflicts)}")
    print(f"speakers               : {ann.speaker_id.nunique()}")
    print(f"speaker groups         : {len(set(groups.values()))}")
    for g, members in merged.items():
        print(f"  merged: {g} <- {', '.join(members)}")
    print("=" * 66)

    lines = ["# Integrity check", "",
             "| check | result |", "|---|---|",
             f"| files checked | {len(ann)} |",
             f"| empty / unreadable | **{len(empty)}** |",
             f"| shorter than {SHORT_SEC}s | {len(short)} |",
             f"| byte-identical groups | **{len(dups)}** |",
             f"| ...crossing splits (leakage) | **{len(cross_split)}** |",
             f"| ...with conflicting labels | {len(conflicts)} |",
             f"| speakers | {ann.speaker_id.nunique()} |",
             f"| speaker groups | {len(set(groups.values()))} |", ""]

    if empty:
        lines += ["## Empty or unreadable", ""]
        lines += [f"- `{p}` — {why}" for p, why in empty[:20]]
        lines.append("")
    if short:
        lines += ["## Clips shorter than %.2fs" % SHORT_SEC, "",
                  "Too short to score reliably; exclude them or flag them.", ""]
        lines += [f"- `{p}` — {d}s" for p, d in short[:20]]
        lines.append("")
    if merged:
        lines += ["## Speakers that are the same person", "",
                  "These ids share byte-identical audio, so they must never be split",
                  "across train/val/test:", ""]
        for g, members in merged.items():
            lines.append(f"- **{g}** = {', '.join(members)}")
        lines.append("")
    if cross_split:
        n = sum(len(f) for f, _ in cross_split)
        lines += ["## Leakage through duplicates", "",
                  f"{len(cross_split)} duplicate groups ({n} files) sit in more than one",
                  "split. The split must be rebuilt on speaker **groups**, not ids.", ""]
        for files, splits in cross_split[:5]:
            lines.append(f"- {files[0]} <-> {files[1]} — splits {sorted(s for s in splits if s)}")
        lines.append("")

    lines += ["## Consequence", "",
              "Splitting is done on `group_id` from `data/speaker_groups.csv`.",
              "A group is a set of speaker ids that share at least one identical recording.",
              "This removes leakage without discarding data."]

    out = Path(args.out_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ok] report  -> {out}")
    print(f"[ok] groups  -> {args.out_groups}")


if __name__ == "__main__":
    main()
