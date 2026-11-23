# Chinese language-learning app: first-party research brief

## Evidence-backed patterns

- **Use a proficiency spine, not an unstructured word list.** China’s Ministry of Education standard defines three stages/nine levels and four measurable language foundations (syllables, characters, vocabulary, grammar), evaluated through listening, speaking, reading, writing and translation. The official HSK site says its syllabus is organized around tasks, topics, vocabulary, grammar and characters. A product should therefore map lessons and progress to level, skill, topic/task and these five content dimensions. ([MOE standard](https://hudong.moe.gov.cn/jyb_xwfb/gzdt_gzdt/s5987/202103/t20210329_523304.html); [HSK](https://www.chinesetest.cn/HSK))
- **Teach the sound–script–meaning connection explicitly.** Duolingo’s official Chinese-course explanation notes that learners cannot infer a character’s pronunciation from its shape and shows Pinyin above characters; its newer component sessions teach recurring character components to make character learning more approachable. Build an early path from Pinyin/initials-finals and tones into characters, with optional Pinyin support that fades as recognition grows. ([Duolingo Chinese](https://blog.duolingo.com/chinese-languages/); [component sessions](https://blog.duolingo.com/component-sessions/))
- **Make tones and speaking a first-class loop.** Duolingo’s Chinese-tones guidance emphasizes that changing a word’s tone can change its meaning and recommends pronunciation practice in addition to listening. HelloChinese’s official product page lists speech recognition among its core features. Include listen → record → targeted feedback → retry, with tone-aware minimal pairs and intelligibility-focused scoring. ([Duolingo tones](https://blog.duolingo.com/chinese-tones/); [HelloChinese](https://www.hellochinese.cc/))
- **Cover all five practical skills with varied exercise types.** HelloChinese explicitly positions the app around reading, writing, speaking, vocabulary and grammar, and lists speech recognition and handwriting. A high-quality flow should alternate comprehension and production: listen/select, read/understand, reorder/build sentences, speak, and write/trace characters. ([HelloChinese](https://www.hellochinese.cc/))
- **Use active recall and spaced repetition for retention.** The official Anki manual identifies active recall and spaced repetition as its core principles; it schedules reviews near forgetting and supports FSRS. Add a daily review queue, learner ratings (again/hard/good/easy), adjustable retention, and separate cards for recognition, listening, production and character writing. ([Anki background](https://docs.ankiweb.net/background.html); [deck options](https://docs.ankiweb.net/deck-options.html))
- **Make dictionary lookup feed review instantly.** Pleco’s official manual says cards can be created from dictionary entries with characters, Pinyin and definitions filled automatically; its Chinese-specific tests include tone drills, character-count/Pinyin-aware multiple choice, and simplified/traditional tracking. Provide tap-to-lookup in lessons/reader, one-tap “save to review,” both script variants, and Chinese-aware distractors. ([Pleco flashcards](https://android.pleco.com/manual/240/flash.html); [Pleco product page](https://www.pleco.com/products/pleco-for-iphone-ipad/))
- **Support authentic input and just-in-time lookup.** Pleco documents dictionary search, document reader and OCR for looking up printed Chinese. A useful intermediate/advanced flow is graded reading/listening with tap lookup, sentence audio, and automatic capture of encountered words into a review deck. ([Pleco dictionary](https://android.pleco.com/manual/310/dict.html); [Pleco product page](https://www.pleco.com/products/pleco-for-iphone-ipad/))

## Suggested product loop

1. Diagnostic placement across sound/tones, characters, vocabulary, grammar and the five skills.
2. Short level-aligned lesson: contextual dialogue/task → explicit pronunciation/character note → guided exercises.
3. Production checkpoint: speak and write, with retries and specific feedback.
4. Daily SRS review, mixing recognition and recall; schedule weak tones/characters more often.
5. Graded real-world input; tap lookup saves cards and examples.
6. Progress dashboard by HSK/standard level, skill, topic/task and retention—not only streaks.

## Content requirements

Maintain canonical entries for simplified and traditional characters, Pinyin with tone marks/numbers, audio, part of speech, meanings, example sentences, stroke order, components/radicals, grammar notes, topic/task tags, and level metadata. Design assessments around communication tasks (the HSK standard’s stated purpose is using Chinese in life, study and work), not vocabulary recognition alone.

## Source note

All sources above are first-party: PRC Ministry of Education / Chinese Test Service, and official Duolingo, HelloChinese, Pleco and Anki documentation/product pages. Accessed 2026-11-01.
