# HSK Course Assets — Copyright Notice

## Rights holder

**Publisher:** Beijing Language and Culture University Press (北京语言大学出版社, BLCUP)  
**Series:** HSK Standard Course (HSK 标准教程)  
**Author:** Jiang Liping (姜丽萍)  
**Authorized by:** Hanban / Chinese International Chinese Education Foundation (中国国际中文教育基金会, CIEF)

## What is in this folder

| Subfolder | Contents | Status |
|-----------|----------|--------|
| `books/` | HSK 1–4 textbook PDFs | ⛔ **DO NOT COMMIT / REDISTRIBUTE** |
| `workbooks/` | HSK 3 workbook PDF | ⛔ **DO NOT COMMIT / REDISTRIBUTE** |
| `audio_archives/` | Original audio ZIP/archives | ⛔ **DO NOT COMMIT / REDISTRIBUTE** |
| `audio_extracted/` | 240 MP3 tracks | ⛔ **DO NOT COMMIT / REDISTRIBUTE** |
| `answer_keys/` | HSK 4A/4B answer PDFs | ⛔ **DO NOT COMMIT / REDISTRIBUTE** |
| `course_manifest.json` | Track metadata only (no audio content) | ✅ Safe to track in git |

## Permitted use

These files may be used **locally only**, for personal study.

- ✅ Serve audio locally to a single user running the app on their own machine
- ✅ Reference answer keys locally
- ❌ **Do not** include in any public git repository
- ❌ **Do not** redistribute, host publicly, or share with third parties
- ❌ **Do not** include in any Docker image pushed to a public registry

## If you need to deploy this app

- Remove the audio from the deployment, or
- License the content directly from BLCUP: https://www.blcup.com/
- Use freely-licensed TTS (gTTS / edge-tts) as a fallback for vocabulary audio

All subfolders except `course_manifest.json` and this file are in `.gitignore`.
