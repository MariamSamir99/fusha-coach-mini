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


def sample(df, splits, per_contrast, seed, label=1):
    sp = pd.read_csv(splits, dtype={"speaker_id": str})
    key = "audio_path"
    df = df.merge(sp[[key, "split"]], on=key, how="inner")

    rows = []
    for contrast in ("H", "S"):
        pool = df[(df.split == "test") & (df.label == label) &
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


def read_sheet(path):
    """Read the review sheet with verdict/notes as plain strings (never floats)."""
    return pd.read_csv(path, dtype={"verdict": str, "notes": str}, keep_default_na=False)


def write_csv(df, path):
    """Write a CSV, turning an Excel lock into a clear instruction."""
    try:
        df.to_csv(path, index=False, encoding="utf-8")
    except PermissionError:
        raise SystemExit(
            f"[error] cannot write {path}\n"
            "        The file is probably open in Excel. Press Ctrl+S, close it, and run again."
        )


def write_player(review, sheet_df, label=1):
    """Offline interactive player: listen, pick a verdict, download the filled CSV.

    Removes Excel from the loop entirely - the browser rebuilds the same CSV.
    """
    import json as _json

    base = sheet_df[sorted(sheet_df.columns)].to_dict(orient="records")
    data_json = _json.dumps(base, ensure_ascii=False).replace("</", "<\\/")

    download_name = "review_sheet.csv" if label == 1 else "review_sheet_correct.csv"

    if label == 1:
        options = [("target", "target"), ("other", "other"),
                   ("none", "none"), ("unsure", "unsure")]
        title = "Label spot-check - clips labelled mispronounced"
        explain = ("<b>target</b> = the error is on the marked letter - "
                   "<b>other</b> = word is wrong, but the error is elsewhere - "
                   "<b>none</b> = sounds correct - <b>unsure</b> = cannot tell.")
    else:
        options = [("ok", "ok (sounds correct)"), ("wrong", "wrong (mispronounced)"),
                   ("unsure", "unsure")]
        title = "Label spot-check - clips labelled correct"
        explain = ("<b>ok</b> = the clip sounds correct - "
                   "<b>wrong</b> = the clip sounds mispronounced - "
                   "<b>unsure</b> = cannot tell.")
    opts_html = "".join(f'<option value="{v}">{t}</option>' for v, t in options)

    rows = []
    for i, r in sheet_df.iterrows():
        rel = Path(r.review_path).as_posix().replace(f"{review.as_posix()}/", "") if r.review_path else ""
        rows.append(f"""
    <tr id="r{i}">
      <td class="c">{i + 1}</td>
      <td class="c">{r.contrast}</td>
      <td class="w" dir="rtl">{r.word}</td>
      <td class="l">{r.target_letter}</td>
      <td class="s">{r.speaker_id}</td>
      <td><audio controls preload="none" src="{rel}"></audio></td>
      <td>
        <select data-i="{i}" class="v">
          <option value=""></option>
          {opts_html}
        </select>
      </td>
      <td><input data-i="{i}" class="n" placeholder="notes"></td>
    </tr>""")

    html = f"""<!doctype html>
<html lang="en"><meta charset="utf-8">
<title>Label spot-check</title>
<style>
 body{{font-family:system-ui,Segoe UI,Arial;margin:24px;background:#fafafa;color:#222}}
 h1{{font-size:19px;margin:0 0 4px}}
 p{{margin:6px 0;color:#555;font-size:14px}}
 table{{border-collapse:collapse;background:#fff;margin-top:14px}}
 th,td{{border:1px solid #e2e2e2;padding:5px 9px;font-size:14px}}
 th{{background:#f2f2f2;position:sticky;top:0}}
 tr.done{{background:#f0fbf3}}
 .w{{font-size:19px;min-width:90px}}
 .c,.l,.s{{text-align:center;color:#666}}
 audio{{height:32px;width:230px}}
 select,input{{padding:4px;font-size:13px}}
 #bar{{position:sticky;bottom:0;background:#fff;border-top:2px solid #ddd;padding:12px;
       margin-top:16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}}
 button{{padding:9px 16px;font-size:14px;border-radius:6px;border:1px solid #1a7f37;
         background:#1a7f37;color:#fff;cursor:pointer}}
 #count{{font-weight:600}}
</style>
<h1>{title}</h1>
<p>Listen to the <b>marked letter only</b>. Pick one verdict per clip:
{explain}</p>
<p>When all clips are judged, press <b>Download {download_name}</b> and replace the file in
<code>member_a/review/</code>.</p>
<p style="background:#fff4e5;border-left:4px solid #d97706;padding:9px 12px">
<b>Nothing is saved until you download.</b> Judgements live only in this browser tab.
Closing the tab loses them.</p>

<table>
<tr><th>#</th><th>contrast</th><th>word</th><th>letter</th><th>speaker</th><th>audio</th>
    <th>verdict</th><th>notes</th></tr>
{''.join(rows)}
</table>

<div id="bar">
  <span id="count">0 / 30 judged</span>
  <button onclick="download()">Download review_sheet.csv</button>
  <span id="msg"></span>
</div>

<script>
const BASE = {data_json};
const COLS = {_json.dumps(sorted(sheet_df.columns))};

function refresh() {{
  let n = 0;
  document.querySelectorAll('select.v').forEach(s => {{
    const tr = s.closest('tr');
    if (s.value) {{ n++; tr.classList.add('done'); }} else {{ tr.classList.remove('done'); }}
  }});
  document.getElementById('count').textContent = n + ' / ' + BASE.length + ' judged';
}}

function esc(v) {{
  v = (v === undefined || v === null) ? '' : String(v);
  return '"' + v.replace(/"/g, '""') + '"';
}}

function download() {{
  const rows = BASE.map((r, i) => Object.assign({{}}, r));
  document.querySelectorAll('select.v').forEach(s => {{
    rows[+s.dataset.i].verdict = s.value;
  }});
  document.querySelectorAll('input.n').forEach(inp => {{
    rows[+inp.dataset.i].notes = inp.value;
  }});
  const lines = [COLS.map(esc).join(',')];
  rows.forEach(r => lines.push(COLS.map(c => esc(r[c])).join(',')));
  const blob = new Blob(['\\ufeff' + lines.join('\\r\\n')], {{type: 'text/csv;charset=utf-8'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = {download_name!r};
  a.click();
  const missing = rows.filter(r => !r.verdict).length;
  document.getElementById('msg').textContent =
    missing ? 'downloaded with ' + missing + ' clips still unjudged' : 'downloaded - all 30 judged';
}}

document.querySelectorAll('select.v').forEach(s => s.addEventListener('change', refresh));
refresh();
</script>
</html>
"""
    out = review / "review.html"
    out.write_text(html, encoding="utf-8")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--annotations", default="data/annotations.csv")
    ap.add_argument("--splits", default="data/splits.csv")
    ap.add_argument("--audio-dir", default="data/raw")
    ap.add_argument("--review-dir", default="member_a/review")
    ap.add_argument("--per-contrast", type=int, default=15)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--summarize", action="store_true")
    ap.add_argument("--status", action="store_true",
                    help="show how many verdicts each sheet has collected")
    ap.add_argument("--force", action="store_true",
                    help="rebuild the sheet even if verdicts were already entered")
    ap.add_argument("--label", type=int, default=1, choices=[0, 1],
                    help="1 = review clips labelled mispronounced, 0 = review clips labelled correct")
    ap.add_argument("--sheet-name", default=None,
                    help="override the sheet file name (use one per direction)")
    args = ap.parse_args()

    review = Path(args.review_dir)
    default_sheet = "review_sheet.csv" if args.label == 1 else "review_sheet_correct.csv"
    sheet = review / (args.sheet_name or default_sheet)

    if args.status:
        for name, what in (("review_sheet.csv", "clips labelled mispronounced"),
                           ("review_sheet_correct.csv", "clips labelled correct")):
            p = review / name
            if not p.exists():
                print(f"  {name:28} missing - not sampled yet")
                continue
            d = read_sheet(p)
            done = int((d.verdict.str.strip() != "").sum())
            flag = "done" if done == len(d) else ("EMPTY - nothing downloaded" if done == 0
                                                  else "in progress")
            print(f"  {name:28} {done:2}/{len(d):2} judged  ({what})  -> {flag}")
        print("\nJudgements are made in the browser and only reach disk when you press Download.")
        return

    if args.summarize:
        if not sheet.exists():
            raise SystemExit(f"[error] {sheet} not found - run the sampling step first")
        df = read_sheet(sheet)
        filled = df[df.verdict.str.strip() != ""]
        if filled.empty:
            raise SystemExit(
                "[error] the verdict column is still empty.\n"
                "        If you already typed verdicts in Excel: press Ctrl+S, close\n"
                "        the file, then run this command again."
            )
        is_pos = not sheet.name.endswith("_correct.csv")
        agree = "target" if is_pos else "ok"
        what = "target-phoneme errors" if is_pos else "agrees with label=correct"

        print(f"reviewed {len(filled)} / {len(df)} sampled clips ({sheet.name})\n")
        print(filled.groupby(["contrast", "verdict"]).size().to_string())
        print()
        for c, g in filled.groupby("contrast"):
            share = (g.verdict == agree).mean()
            print(f"  {c}: {what} = {share:.0%} ({int((g.verdict == agree).sum())}/{len(g)})")
        overall = (filled.verdict == agree).mean()
        print(f"\n  overall = {overall:.0%}")
        print(f"  -> write this number into the report's limitations section")

        out = review / ("label_check.md" if is_pos else "label_check_correct.md")
        lines = ["# Label spot-check", "",
                 f"Sheet: `{sheet.name}` · clips reviewed: **{len(filled)} / {len(df)}**", "",
                 f"Agreement metric: **{what}**", "",
                 "| contrast | " + " | ".join(sorted(filled.verdict.unique())) + " | agree |",
                 "|---" * (len(sorted(filled.verdict.unique())) + 2) + "|"]
        for c, g in filled.groupby("contrast"):
            v = g.verdict.str.strip().str.lower().value_counts()
            cols = " | ".join(str(v.get(k, 0)) for k in sorted(filled.verdict.unique()))
            lines.append(f"| {c} | {cols} | {(g.verdict == agree).mean():.0%} |")
        lines += ["", "Write this table into the limitations section of the report."]
        out.write_text("\n".join(lines), encoding="utf-8")
        print(f"  -> table saved to {out}")
        return

    # ---- sampling mode ----
    if sheet.exists() and not args.force:
        existing = read_sheet(sheet)
        done = int((existing.verdict.str.strip() != "").sum())
        if done:
            raise SystemExit(
                f"[refused] {sheet} already has {done} filled verdict(s).\n"
                "          Rebuilding would erase your work.\n"
                "          Use --force only if you really want to start over."
            )

    df = pd.read_csv(args.annotations)
    df["contrast"] = df["contrast"].fillna("")
    sampled = sample(df, args.splits, args.per_contrast, args.seed, args.label)
    if sampled.empty:
        raise SystemExit("[error] nothing sampled - check splits/annotations paths")

    review.mkdir(parents=True, exist_ok=True)
    direction = "" if args.label == 1 else "neg"
    review_paths = []
    for _, r in sampled.iterrows():
        src = Path(args.audio_dir) / r.file
        # keep the speaker folder: basenames repeat across speakers (26_N.wav ...)
        dest = review / direction / r.contrast / Path(r.file)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dest)
            review_paths.append(dest.as_posix())
        else:
            review_paths.append("")
            print(f"[warn] missing audio: {src}")

    sampled["review_path"] = review_paths
    sampled["verdict"] = ""
    sampled["notes"] = ""
    write_csv(sampled, sheet)
    player = write_player(review, sampled, label=args.label)

    kind = "mispronounced" if args.label == 1 else "correct"
    print(f"[ok] {len(sampled)} {kind} clips copied to {review}/<H|S>/")
    print(f"[ok] sheet: {sheet}")
    print(f"[ok] player: {player}   (double-click to open in the browser)")
    print(f"[info] contrast split: {sampled.contrast.value_counts().to_dict()}")
    print(VERDICT_HELP)
    print("Close Excel after editing, then: python member_a/04_sample_for_review.py --summarize")


if __name__ == "__main__":
    main()
