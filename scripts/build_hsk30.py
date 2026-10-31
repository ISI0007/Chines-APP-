"""
Build backend/data/hsk/hsk30.json (official HSK 3.0, levels 1-6) from two open datasets.

Sources (both MIT; definitions originate from CC-CEDICT, CC BY-SA 4.0 -- see NOTICE.md):
  * ivankra/hsk30 `hsk30.csv`   -> official level, pinyin, traditional, POS, variants
  * drkameleon/complete-hsk-vocabulary `complete.min.json` -> English meanings, frequency rank

Usage:
    python scripts/build_hsk30.py --csv /path/hsk30.csv --drk /path/complete.min.json
(Run once; the generated JSON is committed so the app needs no network at import time.)
The 7-9 "advanced" band is intentionally excluded (product scope = HSK 1-6).
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


def clean_meanings(meanings):
    """Drop dictionary noise (surnames, variant notes, internet slang) unless nothing else remains."""
    good = [m for m in meanings if not _JUNK.match(m.strip())]
    return good or list(meanings)


def _norm_manual():
    return {(w, norm_toned(p)): v for (w, p), v in MANUAL.items()}


def cedict_numeric(field: str):
    m = re.search(r"\[([^\]]+)\]", field or "")
    return m.group(1) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--drk", required=True)
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(open(args.csv, encoding="utf-8")) if r["Level"] in "123456" and r["Level"]]
    drk = json.load(open(args.drk, encoding="utf-8"))
    by_s = defaultdict(list)
    for e in drk:
        by_s[e["s"]].append(e)

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

    def definitions_for(simplified: str, toned: str):
        """Meanings for the form whose LETTERS match the official reading (so 行 xíng never
        gets háng's meaning); tones only break ties. Returns (meanings, entry, quality)."""
        forms = [(f, e) for e in by_s.get(simplified, []) for f in e["f"] if f["m"]]
        if not forms:
            return [], None, "missing"
        w_letters, w_tones = key(simplified, tone_marks_to_numeric(norm_toned(toned)))
        same = [(f, e) for f, e in forms if key(simplified, f["i"]["n"])[0] == w_letters]
        if not same:
            return [], None, "unmatched"
        exact = [(f, e) for f, e in same if key(simplified, f["i"]["n"])[1] == w_tones]
        if len(exact) >= 1:
            # several CEDICT entries can share one reading (也 "also" + 也 "surname Ye"): merge them
            merged = list(dict.fromkeys(m for f, _ in exact for m in f["m"]))
            return merged, exact[0][1], "match"
        scored = sorted(same, key=lambda fe: tone_distance(key(simplified, fe[0]["i"]["n"])[1], w_tones))
        best = tone_distance(key(simplified, scored[0][0]["i"]["n"])[1], w_tones)
        ties = [fe for fe in scored if tone_distance(key(simplified, fe[0]["i"]["n"])[1], w_tones) == best]
        if len(ties) == 1 and best < 99:
            return ties[0][0]["m"], ties[0][1], "match_tone_variant"
        return [], None, "ambiguous"

    for r in rows:
        level = int(r["Level"])
        variants = json.loads(r["Variants"]) if r["Variants"] else None
        if variants:
            # "Example" variants only illustrate an affix (第 -> 第二); they are not syllabus entries.
            stats["example_variants_skipped"] += sum(1 for v in variants if v.get("Example"))
            items = [{"s": v["Simplified"], "t": v["Traditional"], "p": v["Pinyin"],
                      "pos": v.get("POS", r["POS"]), "c": v.get("CEDICT", "")}
                     for v in variants if not v.get("Example")]
        else:
            items = [{"s": re.sub(r"\d+$", "", r["Simplified"]), "t": re.sub(r"\d+$", "", r["Traditional"]),
                      "p": r["Pinyin"], "pos": r["POS"], "c": r["CEDICT"]}]
        for it in items:
            simp, official = it["s"].strip(), it["p"].strip()
            if not simp or "|" in simp or "|" in official:
                stats["skipped_malformed"] += 1
                continue
            # Display pinyin: syllable-spaced form from CEDICT when it agrees with the official reading.
            num = cedict_numeric(it["c"])
            display = re.sub(r"[-]", " ", official)
            if " " not in display and "'" not in display:
                parts = [m.group(0) for m in SYL.finditer(display)]
                if len(parts) > 1 and "".join(parts) == display:
                    display = " ".join(parts)
            if num:
                spaced = numeric_to_tone_marks(num)
                if norm_toned(spaced) == norm_toned(official):
                    display = spaced[0].upper() + spaced[1:] if official[:1].isupper() else spaced
                    stats["pinyin_spaced_from_cedict"] += 1
                else:
                    stats["pinyin_cedict_disagrees_kept_official"] += 1
                    report["pinyin_disagree"].append((simp, official, spaced))
            defs, e, how = definitions_for(simp, official)
            if how in ("ambiguous", "unmatched", "missing") and simp.endswith("儿"):
                base_py = re.sub(r"r$", "", norm_toned(official))
                bdefs, be, bhow = definitions_for(simp[:-1], base_py)
                if bdefs:
                    defs, e, how = bdefs, be, "erhua_base"
            if (simp, norm_toned(official)) in manual:  # hand-checked entries always win
                defs, e, how = manual[(simp, norm_toned(official))], None, "manual"
            stats[f"defs_{how}"] += 1
            # cross-check level against the other dataset
            if e is not None:
                codes = {c for c in e.get("l", []) if c.startswith("n")}
                if codes and f"n{level}" not in codes:
                    stats["level_disagrees_with_drk"] += 1
                    report["level_disagree"].append((simp, official, level, sorted(codes)))
            dkey = (simp, display)
            if dkey in seen:
                stats["duplicate_dropped_higher_level"] += 1
                continue
            seen[dkey] = True
            out.append({
                "simplified": simp,
                "traditional": (it["t"] or simp).strip(),
                "pinyin": display,
                "pos": it["pos"],
                "definitions": (defs if how == "manual" else clean_meanings(defs))[:MAX_DEFS],
                "hsk_level": f"HSK{level}",
                "frequency_rank": (e or {}).get("q"),
                "definition_quality": how,
            })

    out.sort(key=lambda w: (w["hsk_level"], w["frequency_rank"] is None, w["frequency_rank"] or 0))
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
