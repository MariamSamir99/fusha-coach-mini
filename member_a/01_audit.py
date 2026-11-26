"""
Step 1 - dataset audit.

Reads the annotation table, scans the audio folder (headers only, no decoding),
and prints every number needed to decide the project scope:
speakers, utterances, duration, sample rates, broken/missing files, label
balance, and per-phoneme counts for the target contrasts.

Writes a markdown report ready to paste into the final document.

Usage:
    python member_a/01_audit.py \
        --annotations data/L2KSU/annotations.csv \
        --audio-dir data/L2KSU \
        --out member_a/data_audit_report.md
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

AUDIO_EXT = {".wav", ".flac", ".mp3", ".m4a", ".ogg"}

# Substrings used to guess the role of each column in an unknown CSV layout.
CANDIDATES = {
    "speaker": ["speaker", "spk", "talker", "subject", "participant"],
    "audio": ["audio", "path", "file", "wav", "filename"],
    "label": ["label", "correct", "decision", "gold", "verdict", "mispron"],
    "text": ["text", "sentence", "prompt", "transcript", "utt"],
    "phoneme": ["phoneme", "phone", "ipa"],
    "canonical": ["canonical", "reference"],
}

# Contrasts of interest for this project.
TARGET_PHONEMES = ["ħ", "h", "sˤ", "s", "ح", "ه", "هـ", "ص", "س", "H", "S"]

POSITIVE_VALUES = {"1", "1.0", "true", "yes", "wrong", "incorrect",
                   "mispronounced", "error", "err"}
NEGATIVE_VALUES = {"0", "0.0", "false", "no", "correct", "ok", "right", "good"}


def pick_columns(df):
    """Return {logical_name: actual_column} using keyword matching."""
    found = {}
    lowered = {c: str(c).lower() for c in df.columns}
    for logical, keys in CANDIDATES.items():
        for col, low in lowered.items():
            if any(k in low for k in keys):
                found[logical] = col
                break
    return found


def audio_inventory(audio_dir):
    """Collect duration / sample rate for every audio file. Header read only."""
    files = [p for p in Path(audio_dir).rglob("*") if p.suffix.lower() in AUDIO_EXT]
    rows = []
    try:
        import soundfile as sf
    except ImportError:
        print("[warn] soundfile is not installed - duration checks skipped "
              "(pip install soundfile)", file=sys.stderr)
        return pd.DataFrame([dict(path=str(p), dur=0.0, sr=0, ch=0, ok=True, err="")
                             for p in files])

    for p in files:
        try:
            info = sf.info(str(p))
            rows.append(dict(path=str(p), dur=info.frames / max(info.samplerate, 1),
                             sr=info.samplerate, ch=info.channels, ok=True, err=""))
        except Exception as exc:
            rows.append(dict(path=str(p), dur=0.0, sr=0, ch=0, ok=False, err=str(exc)[:80]))
    return pd.DataFrame(rows)


def normalise_labels(series):
    """Map label values to 1 = mispronounced, 0 = correct. Returns (mapped, unknown)."""
    def to01(v):
        s = str(v).strip().lower()
        if s in POSITIVE_VALUES:
            return 1
        if s in NEGATIVE_VALUES:
            return 0
        return None

    mapped = series.map(to01)
    unknown = sorted({str(v) for v, m in zip(series, mapped) if m is None})[:10]
    return mapped, unknown


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", required=True, help="path to annotations.csv")
    ap.add_argument("--audio-dir", default=None, help="folder containing the audio")
    ap.add_argument("--out", default="member_a/data_audit_report.md")
    args = ap.parse_args()

    ann = Path(args.annotations)
    if not ann.exists():
        sys.exit(f"[error] not found: {ann}")

    # Try common separators before falling back to latin-1.
    df = None
    for sep in (",", ";", "\t", "|"):
        try:
            cand = pd.read_csv(ann, sep=sep, encoding="utf-8")
            if cand.shape[1] > 1:
                df = cand
                break
        except Exception:
            continue
    if df is None:
        df = pd.read_csv(ann, encoding="latin-1")

    print("=" * 70)
    print("ANNOTATION TABLE")
    print("=" * 70)
    print(f"rows={len(df)}  columns={df.shape[1]}")
    print("columns:", list(df.columns))

    nulls = df.isna().sum()
    print("\nnull counts (non-zero only):")
    print(nulls[nulls > 0].to_string() if (nulls > 0).any() else "  none")

    print("\nfirst 3 rows:")
    print(df.head(3).to_string(max_colwidth=40))
    print("\ndtypes:")
    print(df.dtypes.to_string())

    cols = pick_columns(df)
    print("\ndetected columns:", cols)

    label_stats = {}
    if "label" in cols:
        mapped, unknown = normalise_labels(df[cols["label"]])
        pos, neg = int((mapped == 1).sum()), int((mapped == 0).sum())
        print(f"\nlabel column '{cols['label']}': "
              f"mispronounced={pos}  correct={neg}  unmapped={int(mapped.isna().sum())}")
        if unknown:
            print("unmapped values (fix the mapping):", unknown)
        label_stats = {"pos": pos, "neg": neg}

        if "phoneme" in cols:
            per = df.loc[mapped == 1, cols["phoneme"]].astype(str).value_counts()
            print("\nper-phoneme mispronounced counts (top 30):")
            print(per.head(30).to_string())
            hits = {t: int(sum(c for ph, c in per.items() if t in ph)) for t in TARGET_PHONEMES}
            print("\ntarget contrast hits:", {k: v for k, v in hits.items() if v})
    else:
        print("\n[warn] no label column detected - inspect the columns manually")

    if "speaker" in cols:
        spk = df[cols["speaker"]].astype(str)
        vc = spk.value_counts()
        print(f"\nunique speakers = {spk.nunique()}")
        print(f"utterances per speaker: min={vc.min()} median={int(vc.median())} max={vc.max()}")

    inv = None
    if args.audio_dir:
        print("\n" + "=" * 70)
        print("AUDIO INVENTORY")
        print("=" * 70)
        inv = audio_inventory(args.audio_dir)
        ok = inv[inv["ok"]]
        print(f"files found={len(inv)}  readable={len(ok)}  broken={len(inv) - len(ok)}")
        if len(ok):
            print(f"total duration = {ok['dur'].sum() / 3600:.2f} h")
            print("duration sec: min=%.2f median=%.2f max=%.2f"
                  % (ok["dur"].min(), ok["dur"].median(), ok["dur"].max()))
            print("sample rates:", dict(Counter(ok["sr"])))
            print("channels:", dict(Counter(ok["ch"])))
        if len(inv) - len(ok):
            print("broken files (first 5):")
            print(inv[~inv["ok"]].head(5).to_string())

        # Path integrity: every annotation row must point to a real file.
        if "audio" in cols:
            names = {Path(p).name for p in inv["path"]}
            refs = df[cols["audio"]].astype(str).map(lambda s: Path(s.replace("\\", "/")).name)
            missing = refs[~refs.isin(names)]
            print(f"\nannotation rows with a missing audio file = {len(missing)}")
            if len(missing):
                print("examples:", missing.head(5).tolist())

    # ---------------- report ----------------
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Data Audit — L2-KSU", "", f"Source: `{ann}`", "", "## Annotation table",
             f"- rows: **{len(df)}**",
             f"- columns: `{list(df.columns)}`",
             f"- detected roles: `{cols}`"]
    if label_stats:
        lines.append(f"- mispronounced: **{label_stats['pos']}** · correct: **{label_stats['neg']}**")
    if "speaker" in cols:
        lines.append(f"- unique speakers: **{df[cols['speaker']].nunique()}**")
    if inv is not None:
        ok = inv[inv["ok"]]
        lines += ["", "## Audio",
                  f"- files found: **{len(inv)}** (broken: {len(inv) - len(ok)})"]
        if len(ok):
            lines.append(f"- total duration: **{ok['dur'].sum() / 3600:.2f} h**")
            lines.append(f"- sample rates: `{dict(Counter(ok['sr']))}`")
    lines += ["", "## Open items",
              "- [ ] licence terms read and recorded",
              "- [ ] contrast selection justified with per-phoneme counts",
              "- [ ] decision recorded: one contrast or two"]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[ok] wrote {out}")


if __name__ == "__main__":
    main()
