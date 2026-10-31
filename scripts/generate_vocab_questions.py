"""
Generate HSK 1-6 mock-test questions from backend/data/hsk/hsk30.json.

Every answer is derived from the official word data, so correctness is checkable by code
(see backend/tests/test_generated_questions.py). Deterministic: same input -> same output.

    python scripts/generate_vocab_questions.py

Writes backend/data/tests/hsk{N}_vocab.json. Question types:
  * meaning  : 学生 (xué sheng) -> pick the English meaning        (type "vocabulary")
  * reverse  : "student" -> pick the word                          (type "vocabulary")
  * pinyin   : 学生 -> pick the correct pinyin (tone-changed foils) (type "pinyin")
"""
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT
sys.path.insert(0, str(BACKEND))
from services.pinyin_service import numeric_to_tone_marks, split_pinyin  # noqa: E402

DATA = BACKEND / "data"
N_MEANING, N_REVERSE, N_PINYIN = 100, 50, 50
STOP = {"the", "and", "for", "with", "from", "one", "someone", "something", "person", "thing", "etc"}


def tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z]+", text.lower()) if len(t) > 2 and t not in STOP}


def short_def(w: dict) -> str | None:
    """First meaning that is short, plain English (no notes, hanzi, brackets)."""
    for d in w["definitions"]:
        d0 = d.split(";")[0].strip()
        if 2 <= len(d0) <= 45 and not re.search(r"[()\[\]一-鿿…]|CL:|\.\.\.", d0):
            return d0
    return None


def pos_key(w: dict) -> str:
    return (w.get("pos") or "?").split("/")[0]


def all_tokens(w: dict) -> set[str]:
    return set().union(*(tokens(d) for d in w["definitions"])) if w["definitions"] else set()


def main() -> None:
    words = json.loads((DATA / "hsk" / "hsk30.json").read_text(encoding="utf-8"))
    readings = Counter(w["simplified"] for w in words)
    inventory = {s for w in words for s in split_pinyin(w["pinyin"])}  # real (syllable, tone) pairs
    by_level = defaultdict(list)
    for w in words:
        by_level[w["hsk_level"]].append(w)

    total = 0
    for level, ws in sorted(by_level.items()):
        rng = random.Random(f"hsk-vocab-{level}")
        valid = [w for w in ws if short_def(w)]
        questions, seen = [], set()

        def pick_foils(w, pool, n, text_of):
            """Foils with the same POS, no shared meaning-words with w, distinct text."""
            same = [x for x in pool if x is not w and pos_key(x) == pos_key(w)]
            rest = [x for x in pool if x is not w and pos_key(x) != pos_key(w)]
            rng.shuffle(same), rng.shuffle(rest)
            foils, used = [], {text_of(w).lower()}
            for x in same + rest:
                t = text_of(x)
                if t.lower() in used or x["simplified"] == w["simplified"]:
                    continue
                # a foil must not also be a correct answer for w
                if tokens(short_def(x) or "") & all_tokens(w) or tokens(short_def(w)) & all_tokens(x):
                    continue
                foils.append(t)
                used.add(t.lower())
                if len(foils) == n:
                    return foils
            return None

        def add(qtype, text, correct, foils, expl, w):
            if text in seen or foils is None or len(set(foils + [correct])) != 4:
                return False
            seen.add(text)
            opts = foils + [correct]
            rng.shuffle(opts)
            questions.append({
                "question_type": qtype, "question_text": text,
                "option_a": opts[0], "option_b": opts[1], "option_c": opts[2], "option_d": opts[3],
                "correct_option": "ABCD"[opts.index(correct)], "explanation": expl,
                "source_word": w["simplified"], "source_pinyin": w["pinyin"],
            })
            return True

        def explain(w):
            return f"{w['simplified']} ({w['pinyin']}) = " + "; ".join(w["definitions"][:3])

        # Ask only about words with few senses: polysemous words (总, 面, 打...) make ambiguous questions.
        cand = [w for w in valid if len(w["definitions"]) <= 4]
        rng.shuffle(cand)
        # 1) meaning: hanzi -> English
        n = 0
        for w in cand:
            if n >= N_MEANING:
                break
            correct = short_def(w)
            q = f"What does {w['simplified']} ({w['pinyin']}) mean?"
            n += add("vocabulary", q, correct, pick_foils(w, valid, 3, short_def), explain(w), w)
        # 2) reverse: English -> word
        label = lambda x: f"{x['simplified']} ({x['pinyin']})"  # noqa: E731
        n = 0
        for w in cand[::-1]:
            if n >= N_REVERSE:
                break
            q = f"Which word means \"{short_def(w)}\"?"
            n += add("vocabulary", q, label(w), pick_foils(w, valid, 3, label), explain(w), w)
        # 3) pinyin: tone-changed foils built only from real syllable+tone pairs
        n = 0
        cand_py = [w for w in cand if readings[w["simplified"]] == 1 and not w["simplified"].endswith("儿")
                   and len(w["simplified"]) <= 4]
        for w in cand_py:
            if n >= N_PINYIN:
                break
            syl = split_pinyin(w["pinyin"])
            movable = [i for i, (_, t) in enumerate(syl) if t != 5]
            back = numeric_to_tone_marks(" ".join(f"{p}{t}" for p, t in syl))
            if not movable or back.lower() != w["pinyin"].lower():
                continue
            foils, tries = set(), 0
            while len(foils) < 3 and tries < 60:
                tries += 1
                new = list(syl)
                for i in rng.sample(movable, rng.randint(1, min(2, len(movable)))):
                    new[i] = (syl[i][0], rng.choice([t for t in (1, 2, 3, 4) if t != syl[i][1]]))
                if not all(s in inventory for s in new):
                    continue
                f = numeric_to_tone_marks(" ".join(f"{p}{t}" for p, t in new))
                if f.lower() != w["pinyin"].lower():
                    foils.add(f)
            if len(foils) == 3:
                n += add("pinyin", f"Which is the correct pinyin for {w['simplified']}?", w["pinyin"],
                         sorted(foils), explain(w), w)

        out = DATA / "tests" / f"{level.lower()}_vocab.json"
        out.write_text(json.dumps(questions, ensure_ascii=False, indent=1), encoding="utf-8")
        kinds = Counter("pinyin" if q["question_type"] == "pinyin" else
                        "reverse" if q["question_text"].startswith("Which word") else "meaning" for q in questions)
        print(f"{level}: {len(questions)} questions {dict(kinds)} -> {out.name}")
        total += len(questions)
    print("total generated:", total)


if __name__ == "__main__":
    main()
