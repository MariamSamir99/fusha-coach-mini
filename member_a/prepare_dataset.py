"""
Step 0b - build a local audio folder and annotation table from a parquet dump.

Some Hugging Face MDD datasets ship audio embedded in a parquet column instead
of loose wav files. This script unpacks it into the layout the rest of the
pipeline expects:

    data/raw/<folder>/<file>.wav
    data/annotations.csv

It also derives the contrast columns used later (which target letters a word
contains), so member B and C can filter by contrast without re-parsing text.

Usage:
    python member_a/prepare_dataset.py \
        --parquet data/_download/arabic_md.parquet \
        --audio-dir data/raw \
        --out data/annotations.csv
"""

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

# Arabic letters -> contrast group. Used only to tag rows, never to label them.
TARGET_LETTERS = {
    "ح": "H",   # voiceless pharyngeal
    "ه": "H",   # plain glottal fricative (competitor of ح)
    "ص": "S",   # emphatic
    "س": "S",   # plain sibilant (competitor of ص)
}


def contrast_tags(text: str):
    """Return per-letter flags and the combined contrast tag(s) for a word."""
    flags = {"has_H": 0, "has_h": 0, "has_S": 0, "has_s": 0}
    codes = set()
    if not isinstance(text, str):
        return flags, ""
    if "ح" in text:
        flags["has_H"] = 1
        codes.add("H")
    if "ه" in text:
        flags["has_h"] = 1
        codes.add("H")
    if "ص" in text:
        flags["has_S"] = 1
        codes.add("S")
    if "س" in text:
        flags["has_s"] = 1
        codes.add("S")
    return flags, "+".join(sorted(codes))


def write_audio(blob: bytes, dest: Path):
    """Write raw bytes, wrapping PCM data in a WAV container when needed."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if blob[:4] == b"RIFF":
        dest.write_bytes(blob)
        return "wav-passthrough"
    # Fallback: array stored as float32 mono at 16 kHz.
    import numpy as np
    import soundfile as sf

    sf.write(str(dest), np.frombuffer(blob, dtype=np.float32), 16000)
    return "wrapped-float32"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", required=True)
    ap.add_argument("--audio-dir", default="data/raw")
    ap.add_argument("--out", default="data/annotations.csv")
    ap.add_argument("--limit", type=int, default=0, help="optional row cap for a dry run")
    args = ap.parse_args()

    src = Path(args.parquet)
    audio_root = Path(args.audio_dir)
    rows = []
    modes = Counter()
    n = 0

    pf = pq.ParquetFile(src)
    for rg in range(pf.metadata.num_row_groups):
        table = pf.read_row_group(rg, columns=["audio", "filename", "transcript",
                                               "label", "speaker_id", "word_index",
                                               "folder_name", "audio_path"])
        for rec in table.to_pylist():
            if args.limit and n >= args.limit:
                break
            folder = rec.get("folder_name") or "unknown"
            name = rec.get("filename") or f"row{n:05d}.wav"
            dest = audio_root / folder / name
            modes[write_audio(rec["audio"]["bytes"], dest)] += 1

            flags, contrast = contrast_tags(rec.get("transcript"))
            rows.append(
                dict(
                    audio_path=(Path(folder) / name).as_posix(),
                    text=rec.get("transcript"),
                    label=int(rec["label"]),
                    speaker_id=str(rec["speaker_id"]),
                    word_index=rec.get("word_index"),
                    **flags,
                    contrast=contrast,
                )
            )
            n += 1
        if args.limit and n >= args.limit:
            break

    df = pd.DataFrame(rows)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8")

    print(f"[ok] wrote {len(df)} rows -> {out}")
    print(f"[ok] audio -> {audio_root}  ({dict(modes)})")
    print(f"[info] speakers={df.speaker_id.nunique()}  words={df.text.nunique()}")
    print(f"[info] label balance: {df.label.value_counts().to_dict()}")
    print(f"[info] rows per contrast: {df.contrast.replace('', 'none').value_counts().to_dict()}")


if __name__ == "__main__":
    main()
