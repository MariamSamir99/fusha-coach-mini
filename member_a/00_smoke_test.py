"""
Member A - smoke test (run this first).

Builds a tiny synthetic dataset (12 speakers, real wav files, correct/wrong
labels) and runs 01_audit.py -> 02_make_splits.py -> 03_verify_splits.py
on it. Nothing here touches the real corpus.

If this ends with "SMOKE TEST PASSED", the local environment is ready.

Usage:
    python member_a/00_smoke_test.py
"""

import random
import shutil
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def make_fake_data(root: Path, n_speakers: int = 13, per_speaker: int = 5, seed: int = 0):
    """Create a synthetic corpus that deliberately contains the defects the
    pipeline is supposed to catch:

    * speaker S13 duplicates S12 byte for byte  -> leakage across speaker ids
    * one zero-byte file under S11              -> unreadable clip
    """
    random.seed(seed)
    audio = root / "audio"
    audio.mkdir(parents=True, exist_ok=True)

    prompts = ["صَبَاح الخَيْر", "حَلِيب", "سَيْف", "صَيْف", "هَرَم", "حَرَم"]
    phones = ["ħ", "h", "sˤ", "s"]
    rows = []

    for s in range(1, n_speakers + 1):
        for u in range(per_speaker):
            name = f"spk{s:02d}_u{u}.wav"
            dest = audio / name

            if s == n_speakers:
                # copy the previous speaker's bytes: identical audio, new speaker id
                shutil.copy2(audio / f"spk{n_speakers - 1:02d}_u{u}.wav", dest)
            elif s == 11 and u == 0:
                dest.write_bytes(b"")          # zero-byte, unreadable
            else:
                with wave.open(str(dest), "w") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(16000)
                    frames = 16000 * random.randint(1, 3)
                    w.writeframes(
                        b"".join(struct.pack("<h", random.randint(-3000, 3000))
                                 for _ in range(frames))
                    )

            rows.append(
                dict(
                    speaker_id=f"S{s:02d}",
                    audio_path=f"audio/{name}",
                    text=random.choice(prompts),
                    phoneme=random.choice(phones),
                    contrast=random.choice(["H", "S"]),
                    label=random.choice(["correct", "wrong"]),
                )
            )

    pd.DataFrame(rows).to_csv(root / "annotations.csv", index=False)
    return root / "annotations.csv", len(rows)


def run(cmd):
    """Run one step as a subprocess and return its exit code."""
    print("\n" + "=" * 70, flush=True)
    print("$", " ".join(str(c) for c in cmd), flush=True)
    print("=" * 70, flush=True)
    return subprocess.run([sys.executable, "-X", "utf8", *map(str, cmd)]).returncode


def main():
    tmp = Path(tempfile.mkdtemp(prefix="fusha_smoke_"))
    ann, n = make_fake_data(tmp)
    n_wav = len(list((tmp / "audio").glob("*.wav")))
    print(f"[setup] synthetic dataset: {n} rows, {n_wav} wav files", flush=True)
    print(f"[setup] location: {tmp}", flush=True)

    failures = []

    if run([HERE / "01_audit.py", "--annotations", ann, "--audio-dir", tmp,
            "--out", tmp / "data_audit_report.md"]) != 0:
        failures.append("01_audit.py")

    # Integrity gate: finds the planted duplicate pair and the zero-byte clip,
    # and writes the speaker -> group map that the split step needs.
    if run([HERE / "06_check_integrity.py", "--annotations", ann,
            "--audio-dir", tmp,
            "--out-groups", tmp / "speaker_groups.csv",
            "--out-report", tmp / "integrity_report.md"]) != 0:
        failures.append("06_check_integrity.py")

    # Splitting must refuse to run without the groups file, then succeed with it.
    rc = run([HERE / "02_make_splits.py", "--annotations", ann,
              "--speaker-col", "speaker_id", "--utt-col", "audio_path",
              "--label-col", "label", "--text-col", "text",
              "--contrast-col", "contrast", "--audio-dir", tmp,
              "--out", tmp / "splits_no_groups.csv", "--seed", "42"])
    if rc == 0:
        print("[FAIL] split step accepted leaking data without --groups")
        failures.append("02_make_splits.py integrity gate")

    if run([HERE / "02_make_splits.py", "--annotations", ann,
            "--speaker-col", "speaker_id", "--utt-col", "audio_path",
            "--label-col", "label", "--text-col", "text",
            "--contrast-col", "contrast", "--audio-dir", tmp,
            "--groups", tmp / "speaker_groups.csv",
            "--out", tmp / "splits.csv", "--seed", "42"]) != 0:
        failures.append("02_make_splits.py")

    # 03 exits 0 on PASS; warnings do not fail the gate
    if run([HERE / "03_verify_splits.py", "--splits", tmp / "splits.csv",
            "--annotations", ann, "--audio-dir", tmp,
            "--contrast-col", "contrast", "--out", tmp / "splits_qa.md"]) != 0:
        failures.append("03_verify_splits.py")

    print("\n" + "#" * 70)
    if failures:
        print("SMOKE TEST FAILED: " + ", ".join(failures))
        return 1

    print("SMOKE TEST PASSED - environment is ready")
    print("Next: accept the dataset gate on Hugging Face, download L2-KSU,")
    print("      then run 01_audit.py on the real annotations.csv")
    print("Outputs of this test:", tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
