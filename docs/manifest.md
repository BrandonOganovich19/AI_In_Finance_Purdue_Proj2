# Submission manifest

Replace every `____` with the GitHub link (videos: YouTube link). Attach `decision-memo.md` and `validation-and-ai-use.md` to Brightspace as well.

| Item | Location |
|---|---|
| Repository | ____ |
| README | ____/README.md |
| App | ____/app.py |
| Engine | ____/engine.py |
| Helper | ____/coach.py |
| Tests | ____/tests/test_engine.py |
| Data and sources | ____/data/SOURCES.md |
| Decision memo | ____/docs/decision-memo.md |
| Validation and AI use, with the Locked Changed-Input Record | ____/docs/validation-and-ai-use.md |
| Commit holding my AI-off prediction (before the run) | ____ |
| Video 1 (3:00 max): how my system and thinking changed, one AI output I checked | YouTube ____ , duration ____ |
| Video 2 (5:00 max): code walkthrough | YouTube ____ , duration ____ |
| Video 3 (5:00 max): committee presentation, opens with the app running live | YouTube ____ , duration ____ |
| Transcripts | ____/docs/transcript-video-1.txt, -2.txt, -3.txt |
| Video scripts (drafted with Claude) | ____/docs/video-scripts.md |

Before submitting:

- [x] Both statements open the README and the memo (the videos still need them)
- [x] Draft box removed from the memo; "Who decided what" table filled in (re-read it so you can stand behind it)
- [ ] Locked Changed-Input Record: prediction committed before the run, result added after
- [x] Three DGS10 values checked against FRED by me, Brandon Oganovich (2026-11-20)
- [x] README run in a fresh Python environment (Claude, 2026-11-20: installed streamlit 1.67.0, pandas 3.1.1, numpy 2.5.5; 23 tests pass; app loads with no errors); [ ] someone else ran the app from the README
- [ ] No API key or `.env` in the repository
- [ ] Videos unlisted, viewable logged out, captions on
