"""
Build backend/data/hsk/hsk30.json from the OFFICIAL HSK syllabus (HSK 考试大纲, published 2025-11,
in force 2026-07), levels 1-6. Level, reading and part of speech come from the syllabus itself
(scripts/extract_hsk_syllabus.py, validated row by row); English meanings, traditional forms and
frequency come from drkameleon/complete-hsk-vocabulary (MIT; meanings originate from CC-CEDICT,
CC BY-SA 4.0 -- see NOTICE.md).

    python scripts/extract_hsk_syllabus.py --pdf <syllabus.pdf> --out /tmp/syllabus_vocab.json
    python scripts/build_hsk30.py --syllabus /tmp/syllabus_vocab.json --drk /path/complete.min.json \\
        --cedict /path/cedict_ts.u8      # e.g. the file bundled in `pip download pycccedict`

The generated JSON is committed so the app needs no network at import time.
Levels 7-9 are excluded by product scope.
"""
import argparse, csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT
sys.path.insert(0, str(BACKEND))
from services.pinyin_service import numeric_to_tone_marks, tone_marks_to_numeric, _SYL as SYL  # noqa: E402

OUT = BACKEND / "data" / "hsk" / "hsk30.json"
MAX_DEFS = 8

# Hand-checked meanings for entries the automatic match cannot resolve (colloquial readings such as
# 谁 shuí / 血 xiě, or multi-word patterns absent from CC-CEDICT).
MANUAL = {
    ("谁", "shuí"): ["who", "whom"],
    ("熟", "shóu"): ["ripe", "cooked", "familiar"],
    ("血", "xiě"): ["blood"],
    ("见过", "jiànguo"): ["to have seen (before)", "to have met"],
    ("这时候", "zhè shíhou"): ["at this time", "at this moment"],
    ("能不能", "néng bu néng"): ["can (you) or not?", "is it possible?"],
    ("电动车", "diàn dòng chē"): ["electric vehicle", "electric bike or scooter"],
    ("眼里", "yǎnli"): ["in one's eyes", "in one's view"],
    ("城里", "chénglǐ"): ["in the city", "downtown"],
    ("很难说", "hěn nánshuō"): ["hard to say", "difficult to tell"],
    ("指着", "zhǐzhe"): ["pointing at"],
    ("不一会儿", "bù yīhuìr"): ["in a moment", "before long"],
    ("那里", "nàlǐ"): ["there", "that place"],
    ("真的", "zhēn de"): ["really", "truly", "real; genuine"],
    ("关系", "guānxì"): ["relationship", "connection", "to concern; to affect"],
    ("恶心", "ěxin"): ["nauseous", "to feel sick", "disgusting"],
    ("〇", "líng"): ["zero"],
    ("哪儿", "nǎ r"): ["where", "wherever; anywhere"],
    ("那儿", "nà r"): ["there", "that place"],
    ("这儿", "zhè r"): ["here", "this place"],
    ("一点儿", "yì diǎn r"): ["a little", "a bit"],
    ("一会儿", "yí huì r"): ["a moment", "a little while"],
    ("一块儿", "yí kuài r"): ["together", "in the same place"],
    ("嗯", "ǹg"): ["yes; uh-huh (agreement)", "hmm"],
    ("呀", "yā"): ["(particle expressing surprise or softening a remark)"],
    ("新媒体", "xīn méi tǐ"): ["new media"],
    ("新能源", "xīn néng yuán"): ["new energy", "renewable energy"],
    ("占比", "zhàn bǐ"): ["proportion", "share (as a percentage)"],
    ("纪录", "jì lù"): ["record (e.g. a world record)", "to record"],
    ("干吗", "gàn má"): ["what for?", "why?", "what are you doing?"],
    ("体检", "tǐ jiǎn"): ["physical examination", "medical check-up"],
    # erhua forms whose base word is not a separate dictionary entry
    ("好玩儿", "hǎo wán r"): ["fun", "interesting"],
    ("没事儿", "méi shì r"): ["it's nothing", "no problem", "to be free"],
    ("男孩儿", "nán hái r"): ["boy"],
    ("女孩儿", "nǚ hái r"): ["girl"],
    ("小孩儿", "xiǎo hái r"): ["child", "kid"],
    ("一会儿", "yī huì r"): ["a moment", "a little while"],
    ("一块儿", "yī kuài r"): ["together", "in the same place"],
    ("一下儿", "yī xià r"): ["once", "a bit (after a verb)"],
    ("一点儿", "yī diǎn r"): ["a little", "a bit"],
    ("干活儿", "gàn huó r"): ["to do manual work", "to work"],
    ("快点儿", "kuài diǎn r"): ["faster", "hurry up"],
    ("那会儿", "nà huì r"): ["at that time", "then"],
    ("有空儿", "yǒu kòng r"): ["to have free time"],
    ("有点儿", "yǒu diǎn r"): ["a bit", "somewhat"],
    ("有一点儿", "yǒu yī diǎn r"): ["a bit", "somewhat"],
    ("老头儿", "lǎo tóu r"): ["old man"],
    ("没法儿", "méi fǎ r"): ["there is no way", "cannot help it"],
    ("模特儿", "mó tè r"): ["(fashion) model"],
    ("味儿", "wèi r"): ["taste", "flavor", "smell"],
    ("有劲儿", "yǒujìnr"): ["strong", "energetic", "interesting"],
    ("差点儿", "chà diǎn r"): ["almost", "nearly"],
    ("差一点儿", "chà yī diǎn r"): ["almost", "nearly"],
    ("大伙儿", "dà huǒ r"): ["everybody", "everyone"],
    ("待会儿", "dāi huì r"): ["in a moment", "later"],
}


def norm_toned(p: str) -> str:
    return re.sub(r"[\s\-'’·]", "", p).lower()


def norm_num(p: str) -> str:
    return re.sub(r"[\s5]", "", p.lower().replace("u:", "ü").replace("v", "ü"))


_JUNK = re.compile(
    r"^(surname |name of |erhua variant of|variant of|old variant of|also pr\.|also written|abbr\. for|"
    r"see |\(Internet slang\)|used in |CL:)", re.I)


_XREF_PAREN = re.compile(r"\s*\([^()]*[\u4e00-\u9fff][^()]*\)")        # (abbr. for 電子商務|电子商务[dian4 ...])
_XREF_HANZI = re.compile(r"\s*[\u4e00-\u9fff|]+(\[[^\]]*\])?")            # ... 地支[di4 zhi1]


def clean_meanings(meanings):
    """Drop dictionary noise (surnames, variant notes, internet slang, hanzi cross-references)
    unless nothing else remains."""
    cleaned = []
    for m in meanings:
        m = _XREF_HANZI.sub("", _XREF_PAREN.sub("", m)).strip(" ,;")
        if m:
            cleaned.append(m)
    good = [m for m in cleaned if not _JUNK.match(m.strip())]
    return good or cleaned or list(meanings)


def _norm_manual():
    return {(w, norm_toned(p)): v for (w, p), v in MANUAL.items()}


def cedict_numeric(field: str):
    m = re.search(r"\[([^\]]+)\]", field or "")
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--syllabus", default=str(OUT.parent / "syllabus_vocab_l1-6.json"), help="output of extract_hsk_syllabus.py (levels 1-6 are committed)")
    ap.add_argument("--drk", required=True)
    ap.add_argument("--cedict", required=True, help="full CC-CEDICT text file (second dictionary source)")
    args = ap.parse_args()

    rows = [r for r in json.load(open(args.syllabus, encoding="utf-8")) if re.match(r"[1-6]", r["level"])]
    drk = json.load(open(args.drk, encoding="utf-8"))
    by_s = defaultdict(list)
    for e in drk:
        by_s[e["s"]].append(e)

    by_c = defaultdict(list)   # full CC-CEDICT, shaped like drkameleon entries (one form per line)
    for line in open(args.cedict, encoding="utf-8"):
        m = re.match(r"^(\S+)\s+(\S+)\s+\[([^\]]+)\]\s+/(.+)/\s*$", line)
        if m:
            by_c[m.group(2)].append({"s": m.group(2), "q": None, "f": [
                {"t": m.group(1), "i": {"n": m.group(3)}, "m": [d for d in m.group(4).split("/") if d.strip()], "c": []}]})

    manual = _norm_manual()
    stats = Counter()
    report = defaultdict(list)
    out, seen = [], {}

    def key(simplified: str, numeric: str):
        """(letters, tones) of a numeric pinyin string; erhua 'r'/'er' normalised."""
        n = re.sub(r"\s", "", numeric.lower().replace("u:", "ü").replace("v", "ü"))
        letters, tones = re.sub(r"\d", "", n), re.sub(r"\D", "", n)
        if simplified.endswith("儿"):
            letters = re.sub(r"(er|r)$", "", letters)
        return letters, tones

    def tone_distance(a: str, b: str) -> float:
        if len(a) != len(b):
            return 99
        return sum(0 if x == y else 0.5 if "5" in (x, y) else 1 for x, y in zip(a, b))

    def definitions_for(simplified: str, toned: str, src=None):
        """Meanings for the form whose LETTERS match the official reading (so 行 xíng never
        gets háng's meaning); tones only break ties. Returns (meanings, entry, quality)."""
        forms = [(f, e) for e in (src if src is not None else by_s).get(simplified, []) for f in e["f"] if f["m"]]
        if not forms:
            return [], None, "missing", None
        w_letters, w_tones = key(simplified, tone_marks_to_numeric(norm_toned(toned)))
        same = [(f, e) for f, e in forms if key(simplified, f["i"]["n"])[0] == w_letters]
        if not same:
            return [], None, "unmatched", None
        exact = [(f, e) for f, e in same if key(simplified, f["i"]["n"])[1] == w_tones]
        if len(exact) >= 1:
            # several CEDICT entries can share one reading (也 "also" + 也 "surname Ye"): merge them
            merged = list(dict.fromkeys(m for f, _ in exact for m in f["m"]))
            return merged, exact[0][1], "match", exact[0][0]
        scored = sorted(same, key=lambda fe: tone_distance(key(simplified, fe[0]["i"]["n"])[1], w_tones))
        best = tone_distance(key(simplified, scored[0][0]["i"]["n"])[1], w_tones)
        ties = [fe for fe in scored if tone_distance(key(simplified, fe[0]["i"]["n"])[1], w_tones) == best]
        if len(ties) == 1 and best < 99:
            return ties[0][0]["m"], ties[0][1], "match_tone_variant", ties[0][0]
        return [], None, "ambiguous", None

    for r in rows:  # already in syllabus order (seq); lowest level/seq wins on duplicates
        level = int(re.match(r"\d", r["level"]).group(0))
        simp = re.sub(r"\d+$", "", r["word"]).strip()          # 本1 / 本2 are homograph markers
        raw = r["pinyin"].replace("’", "'").strip()
        if "/" in raw:                                          # 谁 shéi/shuí: keep the first reading
            stats["alt_reading_first_kept"] += 1
            raw = raw.split("/")[0]
        official = re.sub(r"\s+", " ", raw)
        base = re.sub(r"[\s'\-]", "", official)                 # unspaced, for matching
        defs, e, how, form = definitions_for(simp, base)
        if how in ("ambiguous", "unmatched", "missing"):          # second source: the full dictionary
            cdefs, ce, chow, cform = definitions_for(simp, base, by_c)
            if cdefs:
                defs, e, how, form = cdefs, None, "cedict", cform
        if how in ("ambiguous", "unmatched", "missing") and simp.endswith("儿"):
            bdefs, be, bhow, bform = definitions_for(simp[:-1], re.sub(r"r$", "", base))
            if bdefs:
                defs, e, how, form = bdefs, be, "erhua_base", None
        if (simp, norm_toned(base)) in manual:                   # hand-checked entries always win
            defs, e, how, form = manual[(simp, norm_toned(base))], None, "manual", None
        stats[f"defs_{how}"] += 1
        # Display pinyin: syllable-spaced. Prefer the dictionary's spacing when it agrees with the
        # official reading; otherwise split the official reading into syllables.
        display = None
        if form is not None:
            spaced = numeric_to_tone_marks(form["i"]["n"])
            if norm_toned(spaced) == norm_toned(base):
                display = (spaced[0].upper() if base[:1].isupper() else spaced[0].lower()) + spaced[1:]   # case follows the syllabus
                stats["pinyin_spaced_from_cedict"] += 1
        if display is None:
            erhua = simp.endswith("儿") and base.endswith("r")
            core = base[:-1] if erhua else base
            parts = [m.group(0) for m in SYL.finditer(core)]
            if parts and "".join(parts) == core and (len(parts) > 1 or erhua):
                display = " ".join(parts) + (" r" if erhua else "")     # erhua: hǎo wán r
                stats["pinyin_spaced_erhua" if erhua else "pinyin_spaced_by_syllables"] += 1
            else:
                display = official; stats["pinyin_kept_as_official"] += 1
                report["pinyin_kept"].append((simp, official))
        if simp == "嗯":
            display = "ǹg"        # the PDF prints "ǹ g" (n + g with a tone mark); one syllable
        trad = (form or {}).get("t") or (e["f"][0]["t"] if e else None) or simp
        dkey = (simp, display)
        if dkey in seen:
            stats["duplicate_dropped_later_entry"] += 1
            report["duplicates"].append((simp, display, level, seen[dkey]))
            continue
        seen[dkey] = level
        out.append({
            "simplified": simp,
            "traditional": trad,
            "pinyin": display,
            "pos": r["pos"],
            "definitions": (defs if how == "manual" else clean_meanings(defs))[:MAX_DEFS],
            "hsk_level": f"HSK{level}",
            "syllabus_seq": r["seq"],
            "frequency_rank": (e or {}).get("q"),
            "definition_quality": how,
        })

    out.sort(key=lambda w: w["syllabus_seq"])   # keep the official order
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0), encoding="utf-8")
    per = Counter(w["hsk_level"] for w in out)
    meta, cum = {}, 0
    for n in range(1, 7):
        cum += per[f"HSK{n}"]
        meta[f"HSK{n}"] = {"new_words": per[f"HSK{n}"], "cumulative_words": cum,
                           "band": ["beginner", "beginner", "beginner", "intermediate", "intermediate", "intermediate"][n - 1]}
    (OUT.parent / "hsk_levels.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    Path("/tmp/hsk_build_report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {len(out)} entries -> {OUT}")
    print("per level:", dict(sorted(Counter(w["hsk_level"] for w in out).items())))
    for k, v in sorted(stats.items()):
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
