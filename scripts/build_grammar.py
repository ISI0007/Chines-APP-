"""
Build grammar lessons aligned to the official HSK grammar outline, validating every example
sentence against the word list (same checker as the reading builder) and generating its pinyin
from the vocabulary. Each lesson records the official syllabus category it comes from.

    python scripts/build_grammar.py          # writes backend/data/grammar/hsk{N}_grammar.json
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend" if (ROOT / "backend").exists() else ROOT
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_level as cl  # noqa: E402
from build_reading import NAME_PINYIN, pinyin_map, to_pinyin  # noqa: E402

OUT = BACKEND / "data" / "grammar"

# HSK1 lessons. Categories/labels quote the official syllabus (HSK 考试大纲, 语法大纲, HSK（一级）).
HSK1 = [
    {"title": "是 — to be (A 是 B)", "pattern": "Subject + 是 + Noun",
     "ref": "句型·特殊句型「是」字句1（表示等同或类属）",
     "explain": "是 (shì) links a subject to a noun to say what someone or something is. It is NOT used before an adjective — for adjectives use 很 (see the 很 lesson). Negate with 不是.",
     "ex": [("我是学生。", "I am a student."), ("他是老师。", "He is a teacher."),
            ("这是我的书。", "This is my book."), ("我不是医生。", "I am not a doctor.")]},
    {"title": "有 — to have / there is", "pattern": "Subject + 有 + Object",
     "ref": "句型·特殊句型「有」字句1（表示领有）",
     "explain": "有 (yǒu) means 'to have' or 'there is/are'. Its negative is 没有 (méiyǒu) — never 不有.",
     "ex": [("我有一个妹妹。", "I have a younger sister."), ("家里有一只猫。", "There is a cat at home."),
            ("我没有钱。", "I don't have money."), ("你有没有问题？", "Do you have a question?")]},
    {"title": "很 — adjectives (no 是)", "pattern": "Subject + 很 + Adjective",
     "ref": "副词·程度副词：很、非常、太、真",
     "explain": "A Chinese adjective is a complete predicate, so you do NOT add 是 before it. 很 (hěn) 'very' is the default link; 非常 'extremely' and 太…了 'too…' are stronger.",
     "ex": [("我很好。", "I am well."), ("今天很冷。", "Today is cold."),
            ("这个很贵。", "This is expensive."), ("太好了！", "Great! / Wonderful!")]},
    {"title": "吗 — yes/no questions", "pattern": "Statement + 吗？",
     "ref": "句类·疑问句（1）是非问句",
     "explain": "Add 吗 (ma) to the end of a statement to make a yes/no question. The word order does not change.",
     "ex": [("你是老师吗？", "Are you a teacher?"), ("你忙吗？", "Are you busy?"),
            ("他喝茶吗？", "Does he drink tea?"), ("你好吗？", "How are you?")]},
    {"title": "Question words (什么 / 谁 / 哪儿 …)", "pattern": "replace the unknown with a question word",
     "ref": "句类·疑问句（2）特指问句；代词·疑问代词",
     "explain": "For a specific question, put a question word where the answer would go; the word order stays the same. 什么 what, 谁 who, 哪儿 where, 几/多少 how many.",
     "ex": [("你叫什么名字？", "What is your name?"), ("他是谁？", "Who is he?"),
            ("你去哪儿？", "Where are you going?"), ("现在几点？", "What time is it now?")]},
    {"title": "的 — 's / linking", "pattern": "Owner + 的 + Noun",
     "ref": "短语·「的」字短语；句子成分·定语",
     "explain": "的 (de) shows possession (like 's) and links a modifier to a noun. Between close relations it is often dropped: 我妈妈.",
     "ex": [("我的手机", "my phone"), ("老师的书", "the teacher's book"),
            ("这是谁的车？", "Whose car is this?"), ("漂亮的衣服", "pretty clothes")]},
    {"title": "了 — completed action / change", "pattern": "Verb + 了",
     "ref": "动作的态·完成态「了1」；变化态「了2」",
     "explain": "了 after a verb marks a completed action (not past tense — it marks completion). 了 at the end of a sentence can mark a new situation / change of state.",
     "ex": [("我吃了饭。", "I have eaten."), ("他买了一件衣服。", "He bought a piece of clothing."),
            ("下雨了。", "It's raining now (it started)."), ("我知道了。", "I see / Got it now.")]},
    {"title": "想 / 要 / 会 / 能 — modal verbs", "pattern": "Subject + 想/要/会/能 + Verb",
     "ref": "动词·能愿动词：会、能、想、要、可以",
     "explain": "Modal verbs go before the main verb. 想 want to, 要 want / be going to, 会 can (learned skill) / will, 能 can (be able to), 可以 may.",
     "ex": [("我想喝茶。", "I want to drink tea."), ("我要去学校。", "I am going to school."),
            ("我会说汉语。", "I can speak Chinese."), ("你能来吗？", "Can you come?")]},
]


def main():
    levels = cl.load_levels()
    allwords = json.loads(cl.HSK.read_text(encoding="utf-8"))
    failures = 0
    for level, lessons in [("HSK1", HSK1)]:
        target = int(level[3:])
        words_set, _ = cl.allowed_sets(levels, target)
        pin = pinyin_map(allwords, target)
        rows = []
        for i, l in enumerate(lessons, 1):
            examples = []
            for zh, en in l["ex"]:
                bad = cl.check(zh, target, levels)
                if bad:
                    failures += 1
                    print(f"[{level}] {l['title']}: '{zh}' OUT OF LEVEL -> {[b['token'] for b in bad]}")
                    continue
                examples.append({"zh": zh, "pinyin": to_pinyin(zh, words_set, pin), "en": en})
            rows.append({"title": l["title"], "hsk_level": level, "pattern": l["pattern"],
                         "explanation": l["explain"], "syllabus_ref": l["ref"],
                         "order_index": i, "examples": examples})
        out = OUT / f"{level.lower()}_grammar.json"
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{level}: wrote {len(rows)} lessons -> {out.name}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
