"""
Fetch open, human-recorded Mandarin pronunciations for the HSK 3.0 word list.

Source: https://github.com/hugolpz/audio-cmn  (CC BY-SA; word recordings by Yue Tan, syllable
recordings by Chen Wang -- both from the Shtooka/SWAC projects). Audio is NOT committed to git
(about 40 MB); this script downloads and places it under backend/data/audio/hsk{N}/.

Selection rules (accuracy first -- no recording is better than a wrong one):
  1. word recording  <hanzi>.mp3        only if the hanzi has ONE reading in our list (a recording
                                        of 行 can't be matched to xíng vs háng without listening)
  2. syllable recording <hanzi>_<numeric>.mp3   for single-syllable entries, exact reading known
  3. single-syllable word recordings are checked with a pitch-based tone classifier
     (scripts/audio_tone_check.py); a recording whose measured tone contradicts the expected tone
     is rejected and replaced by the syllable recording when one exists.
Everything else gets no file -> the app falls back to synthetic speech.

    pip install praat-parselmouth numpy scikit-learn
    python scripts/fetch_audio.py            # clones audio-cmn into a temp cache
    python scripts/fetch_audio.py --src /path/to/audio-cmn-checkout
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from services.pinyin_service import split_pinyin, tone_marks_to_numeric  # noqa: E402

REPO = "https://github.com/hugolpz/audio-cmn.git"
PINNED = "f759a0f18f27690742957619e1248ed91e9b3f2c"  # 2026-10-26
TIER = "24k-abr"  # 22 kHz mono mp3, ~26 kbps: clear speech at ~4.5 KB per second
OUT = BACKEND / "data" / "audio"


def checkout(dest: Path) -> Path:
    run = lambda *a, **k: subprocess.run(a, check=True, cwd=dest, **k)  # noqa: E731
    subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", REPO, str(dest)], check=True)
    run("git", "sparse-checkout", "init", "--no-cone")
    run("git", "sparse-checkout", "set", f"/{TIER}/hsk/", f"/{TIER}/syllabs/")
    run("git", "-c", "core.quotepath=false", "checkout", PINNED)
    return dest


def write_manifest(path: Path, manifest: dict) -> None:
    """Readable header, then one compact line per file (keeps the committed manifest small and diffable)."""
    head = {k: v for k, v in manifest.items() if k != "files"}
    body = ",\n".join("  " + json.dumps(f, ensure_ascii=False) for f in manifest["files"])
    path.write_text(json.dumps(head, ensure_ascii=False, indent=1)[:-2] + ',\n "files": [\n' + body + "\n ]\n}\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", help="existing audio-cmn checkout (sparse checkout of 24k-abr is enough)")
    ap.add_argument("--no-verify", action="store_true", help="skip the tone check")
    args = ap.parse_args()

    tmp = None
    if args.src:
        src = Path(args.src)
    else:
        tmp = tempfile.mkdtemp(prefix="audio-cmn-")
        src = checkout(Path(tmp))
    words_dir, syl_dir = src / TIER / "hsk", src / TIER / "syllabs"

    words = json.loads((BACKEND / "data" / "hsk" / "hsk30.json").read_text(encoding="utf-8"))
    readings = Counter(w["simplified"] for w in words)

    clf = None
    if not args.no_verify:
        import audio_tone_check as tc
        clf = tc.train_and_report(str(src))

    plan, rejected = [], []
    # 1) word recordings for single-reading hanzi (tone-verified when monosyllabic)
    mono = []
    for w in words:
        numeric = tone_marks_to_numeric(w["pinyin"]).replace(" ", "")
        n_syl = len(split_pinyin(w["pinyin"]))
        wav = words_dir / f"cmn-{w['simplified']}.mp3"
        entry = {"hanzi": w["simplified"], "pinyin": w["pinyin"], "level": w["hsk_level"], "numeric": numeric}
        if readings[w["simplified"]] == 1 and wav.exists():
            entry.update(src=wav, name=f"{w['simplified']}.mp3", kind="word", author="Yue Tan", verified="unchecked")
            tone = split_pinyin(w["pinyin"])[0][1] if n_syl == 1 else None
            if n_syl == 1 and tone in (1, 2, 3, 4) and clf is not None:
                mono.append((entry, tone))
            plan.append(entry)
            continue
        plan.append(entry)  # placeholder; may get a syllable file below
        entry["kind"] = None

    if clf is not None and mono:
        import audio_tone_check as tc
        feats = tc.extract([str(e["src"]) for e, _ in mono])
        agree = 0
        for (e, tone), f in zip(mono, feats):
            if f is None:
                e["verified"] = "unchecked"
                continue
            pred = int(clf.predict([f])[0])
            if pred == tone:
                e["verified"] = "tone-checked"; agree += 1
            else:
                rejected.append({"hanzi": e["hanzi"], "pinyin": e["pinyin"], "expected_tone": tone, "measured_tone": pred})
                e["kind"] = None  # drop the word recording
        print(f"tone check on {len(mono)} single-syllable word recordings: {agree} agree "
              f"({agree/len(mono):.1%}), {len(rejected)} rejected")

    # 2) exact-reading syllable recordings for single-syllable entries without an accepted word file
    for e in plan:
        if e.get("kind") is None:
            syl = syl_dir / f"cmn-{e['numeric']}.mp3"
            if len(split_pinyin(e["pinyin"])) == 1 and syl.exists() and e["numeric"][-1] in "1234":
                e.update(src=syl, name=f"{e['hanzi']}_{e['numeric']}.mp3", kind="syllable", author="Chen Wang", verified="label")

    # 3) place files + manifest
    for old_dir in OUT.glob("hsk[1-9]"):          # replace generated audio only; keep ATTRIBUTION.md / MANIFEST.json
        shutil.rmtree(old_dir)
    kept, per_level = [], defaultdict(Counter)
    for e in plan:
        per_level[e["level"]]["total"] += 1
        if not e.get("kind"):
            continue
        dest = OUT / e["level"].lower() / e["name"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(e["src"], dest)
        per_level[e["level"]][e["kind"]] += 1
        kept.append({k: e[k] for k in ("hanzi", "pinyin", "level", "kind", "author", "verified")} | {"file": f"{e['level'].lower()}/{e['name']}"})

    manifest = {
        "source": "https://github.com/hugolpz/audio-cmn", "commit": PINNED, "tier": TIER,
        "license": "CC BY-SA (Shtooka/SWAC packs); attribution: Yue Tan (words), Chen Wang (syllables)",
        "total_entries": len(plan), "with_audio": len(kept),
        "coverage": {lv: dict(c) | {"pct": round(100 * (c["word"] + c["syllable"]) / c["total"], 1)} for lv, c in sorted(per_level.items())},
        "rejected_tone_mismatch": rejected, "files": kept,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    write_manifest(OUT / "MANIFEST.json", manifest)
    print(f"audio for {len(kept)}/{len(plan)} entries ({len(kept)/len(plan):.0%}) -> {OUT}")
    for lv, c in manifest["coverage"].items():
        print(f"  {lv}: {c['word']} word + {c['syllable']} syllable of {c['total']} = {c['pct']}%")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
