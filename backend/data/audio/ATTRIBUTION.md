# Audio attribution

Pronunciation recordings are **not authored by this project**. They come from
[hugolpz/audio-cmn](https://github.com/hugolpz/audio-cmn) (pinned commit `f759a0f`), which curates and
re-encodes recordings from the Shtooka / SWAC projects, licensed **CC BY-SA**
(see that repository and https://packs.shtooka.net/cmn-caen-tan/readme.txt for the exact licence version).

| Recordings | Speaker |
|---|---|
| Word pronunciations (`<hanzi>.mp3`) | Yue Tan |
| Syllable pronunciations (`<hanzi>_<pinyin><tone>.mp3`) | Chen Wang |

The MP3 files are downloaded by `scripts/fetch_audio.py` and are not stored in git. Redistribute them under the
same licence with this attribution. `MANIFEST.json` lists exactly which recording backs which word.

The original checked-in manifest covers the official HSK levels 1–6 vocabulary only. The downloader
can be rerun against the expanded Pleco seed to extend recordings to its HSK 1–9 cards. The app groups
the source's advanced level 7–9 category under `HSK7-9`.
