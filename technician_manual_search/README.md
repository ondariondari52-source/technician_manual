# Software Engineering EEE 2026: Technician Manual Search

A web app for field technicians. They search a network operations manual and get the best sections with section references,
a short AI answer written only from those sections (with citations, and a refusal when the manual does not cover the question),
or, as a separate and clearly labelled option, general AI guidance that is not taken from the manual.

Only the standard Python library is used. Needs Python 3.8 or newer.

## Run it

1. Open a terminal in this folder and run `python app.py` (on Windows you can double-click `start_app.bat`).
2. Open http://127.0.0.1:8000
3. Log in as the administrator. With no settings the app prints a one-time admin password in the terminal.

## Where to read next

| File | What it is for |
|---|---|
| `DEPLOY.md` | Settings, email, Gemini, hosting online |
| `CODE_GUIDE.md` | How the code works, for the exam and the presentation |
| `VALIDATION.md` | The project checked against your lecturer's brief, with evidence and honest gaps |
| `eval/` | The 50 evaluation questions and the results |

## Test it

```
python tests/unit_tests.py
python tests/run_tests.py
python evaluate.py --offline
python evaluate.py
```

The last command needs `GEMINI_API_KEY` and fills in the answer-quality results.
