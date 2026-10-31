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


HSK2 = [
    {"title": "虽然…但是 — although…", "pattern": "虽然 + A，但是 + B",
     "ref": "复句·转折复句：虽然……，但是……",
     "explain": "虽然 (suīrán) … 但是 (dànshì) … expresses contrast: 'although A, (but) B'. Unlike English, Chinese keeps 但是 in the second clause.",
     "ex": [("虽然很累，但是我很快乐。", "Although I'm tired, I'm happy."),
            ("虽然下雨，但是我们去了。", "Although it rained, we went."),
            ("这件衣服虽然贵，但是很好看。", "Although this clothing is expensive, it looks nice."),
            ("他虽然忙，但是每天运动。", "Although he's busy, he exercises every day.")]},
    {"title": "因为…所以 — because…", "pattern": "因为 + cause，所以 + result",
     "ref": "复句·因果复句：因为……，所以……",
     "explain": "因为 (yīnwèi) gives the reason, 所以 (suǒyǐ) gives the result. Both halves are usually kept.",
     "ex": [("因为下雨，所以我在家。", "Because it rained, I stayed home."),
            ("因为他病了，所以没来上课。", "Because he was sick, he didn't come to class."),
            ("我喜欢运动，因为对身体好。", "I like sports, because it's good for the body."),
            ("因为累，所以她想休息。", "Because she's tired, she wants to rest.")]},
    {"title": "V 得 + adjective — how an action is done", "pattern": "Verb + 得 + Adjective",
     "ref": "补语·状态补语1：动词 + 得 + 形容词性短语",
     "explain": "To describe HOW an action is done, use Verb + 得 (de) + adjective. If there's an object, repeat the verb: 他说汉语说得很好.",
     "ex": [("他跑得很快。", "He runs fast."), ("你来得很早。", "You came early."),
            ("她唱得很好。", "She sings well."), ("我吃得太多了。", "I ate too much.")]},
    {"title": "过 — have done before", "pattern": "Verb + 过",
     "ref": "动作的态·经历态：用动态助词「过」表示",
     "explain": "过 (guo) after a verb marks an experience — something you have done at least once. Negate with 没 + Verb + 过.",
     "ex": [("我去过中国。", "I have been to China."), ("你吃过饺子吗？", "Have you eaten dumplings?"),
            ("他没看过这个电影。", "He hasn't seen this movie."), ("我学过汉语。", "I have studied Chinese.")]},
    {"title": "着 — ongoing state", "pattern": "Verb + 着",
     "ref": "补语/动作的态：动词 + 着（表示状态的持续）",
     "explain": "着 (zhe) after a verb shows a continuing state. 门开着 = the door is (standing) open.",
     "ex": [("门开着。", "The door is open."), ("他手里拿着书。", "He's holding a book in his hand."),
            ("外面下着雨。", "It's raining outside."), ("她笑着说。", "She said with a smile.")]},
    {"title": "还是 — A or B? (choice question)", "pattern": "A + 还是 + B？",
     "ref": "句类·疑问句：用「还是」连接的选择问句",
     "explain": "还是 (háishi) offers a choice in a question: 'A or B?'. (In a statement, 'or' is 或者.)",
     "ex": [("你喝茶还是咖啡？", "Do you want tea or coffee?"),
            ("今天去还是明天去？", "Go today or tomorrow?"),
            ("你坐公交车还是坐地铁？", "Do you take the bus or the subway?"),
            ("他是老师还是学生？", "Is he a teacher or a student?")]},
    {"title": "让 / 叫 — make / let someone do", "pattern": "Subject + 让/叫 + Person + Verb",
     "ref": "句型·兼语句1（表使令）：主语 + 请/叫/让 + 宾语 + 动词",
     "explain": "让 (ràng) and 叫 (jiào) mean to make / let / ask someone do something. The person comes between the two verbs.",
     "ex": [("妈妈让我买东西。", "Mom asked me to buy things."),
            ("老师让我们读书。", "The teacher had us read."),
            ("他叫我等一下。", "He told me to wait a moment."),
            ("请让我看看。", "Please let me take a look.")]},
    {"title": "一…就… — as soon as", "pattern": "一 + V1，就 + V2",
     "ref": "复句·紧缩复句：一……就……",
     "explain": "一 (yī) … 就 (jiù) … links two actions: as soon as the first happens, the second follows.",
     "ex": [("我一到家就吃饭。", "As soon as I get home, I eat."),
            ("他一下课就回家。", "As soon as class ends, he goes home."),
            ("我一看就懂了。", "I understood as soon as I looked."),
            ("她一高兴就唱歌。", "As soon as she's happy, she sings.")]},
]

HSK3 = [
    {"title": "把字句 — do something to an object", "pattern": "Subject + 把 + Object + Verb + …",
     "ref": "句型·「把」字句1",
     "explain": "把 (bǎ) moves the object before the verb to stress what happens TO it. The verb needs an extra element after it (result, location, 了…).",
     "ex": [("请把门关上。", "Please close the door."), ("我把作业做完了。", "I finished the homework."),
            ("他把书放在桌子上。", "He put the book on the table."), ("请把名字写在这里。", "Please write your name here.")]},
    {"title": "被 — passive", "pattern": "Subject + 被 + (doer) + Verb + …",
     "ref": "句型·被动句1",
     "explain": "被 (bèi) marks the passive: the subject receives the action. The doer can be left out.",
     "ex": [("我的自行车被人借走了。", "My bike was borrowed by someone."),
            ("蛋糕被弟弟吃了。", "The cake was eaten by my brother."),
            ("杯子被打坏了。", "The cup was broken."),
            ("他被老师叫去了。", "He was called away by the teacher.")]},
    {"title": "比 — comparison", "pattern": "A + 比 + B + Adjective",
     "ref": "句型·比较句2：A 比 B + 更/还 + 形容词；A 跟 B 一样",
     "explain": "A 比 (bǐ) B + adjective says A is more … than B. Use 更/还 for 'even more'. A 跟 B 一样 = A is the same as B.",
     "ex": [("今天比昨天冷。", "Today is colder than yesterday."),
            ("他比我高。", "He is taller than me."),
            ("高铁比汽车快得多。", "The high-speed train is much faster than a car."),
            ("我的手机跟你的一样。", "My phone is the same as yours.")]},
    {"title": "如果…就… — if…then", "pattern": "如果 + condition，就 + result",
     "ref": "复句·假设复句：如果……，就……",
     "explain": "如果 (rúguǒ) states a condition; 就 (jiù) introduces the result. 如果 can be dropped in casual speech.",
     "ex": [("如果下雨，我就不去了。", "If it rains, I won't go."),
            ("如果你有时间，就来我家。", "If you have time, come to my place."),
            ("如果不懂，就问老师。", "If you don't understand, ask the teacher."),
            ("如果便宜，我就买。", "If it's cheap, I'll buy it.")]},
    {"title": "不但…而且… — not only…but also", "pattern": "不但 + A，而且 + B",
     "ref": "复句·递进复句：不但……，而且……",
     "explain": "不但 (búdàn) … 而且 (érqiě) … adds a stronger point: 'not only A, but also B'.",
     "ex": [("她不但聪明，而且很努力。", "She is not only clever but also hardworking."),
            ("这里不但方便，而且便宜。", "Here is not only convenient but also cheap."),
            ("他不但会说汉语，而且写得很好。", "He not only speaks Chinese but also writes it well."),
            ("这个菜不但好吃，而且健康。", "This dish is not only tasty but also healthy.")]},
    {"title": "除了…还/也… — besides", "pattern": "除了 + A（以外），还/也 + B",
     "ref": "固定格式：除了……（以外），……还/也/都……",
     "explain": "除了 (chúle) … 还/也 … means 'besides A, also B'. With 都 it means 'except A, all …'.",
     "ex": [("除了汉语，我还学数学。", "Besides Chinese, I also study math."),
            ("除了跑步，他也喜欢游泳。", "Besides running, he also likes swimming."),
            ("除了周末，我每天都上班。", "Except weekends, I work every day."),
            ("除了他，大家都来了。", "Except for him, everyone came.")]},
    {"title": "先…然后… — first…then", "pattern": "先 + A，然后 + B",
     "ref": "复句·承接复句：先……，再/然后……",
     "explain": "先 (xiān) … 然后 (ránhòu) … puts actions in order: first do A, then do B. 再 can replace 然后.",
     "ex": [("我先洗澡，然后睡觉。", "I shower first, then sleep."),
            ("先做作业，然后看电视。", "Do homework first, then watch TV."),
            ("我们先吃饭，然后去公园。", "We eat first, then go to the park."),
            ("先想清楚，再决定。", "Think it over first, then decide.")]},
    {"title": "V 得/不 + 补语 — can / cannot (potential)", "pattern": "Verb + 得/不 + result",
     "ref": "补语·可能补语1：动词 + 得/不 + 动词/形容词",
     "explain": "Insert 得 (de) for 'able to' or 不 (bu) for 'unable to' between a verb and its result: 看得懂 = can understand (by reading), 看不懂 = cannot.",
     "ex": [("这本书我看得懂。", "I can understand this book."),
            ("东西太多，我拿不了。", "There are too many things; I can't carry them."),
            ("老师说的话你听得懂吗？", "Can you understand what the teacher says?"),
            ("今天的作业做得完。", "Today's homework can be finished.")]},
]


def main():
    levels = cl.load_levels()
    allwords = json.loads(cl.HSK.read_text(encoding="utf-8"))
    failures = 0
    for level, lessons in [("HSK1", HSK1), ("HSK2", HSK2), ("HSK3", HSK3)]:
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
