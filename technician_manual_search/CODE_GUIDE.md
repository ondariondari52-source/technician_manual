# Code guide for the exam and the presentation

The code has no comments, so this guide explains it. Read sections 1 to 4 for the overview, section 5 for the ideas an examiner will probe,
section 7 for likely questions, and section 8 for a five-minute demonstration.

## 1. The idea in one paragraph

A technician asks a question. The app splits the manual into 13 sections, ranks them with BM25 keyword search, and returns the best three with their
section numbers. Optionally an AI writes a short answer **only from those sections**. The app checks that the answer cites sections that were really
retrieved and is supported by their text, and refuses otherwise. A second, clearly labelled option asks the AI for general guidance that is **not** from the manual.
Only registered technicians with an administrator-issued number can use any of it.

## 2. The files

| File | Job | Lines |
|---|---|---|
| `app.py` | Web server, routes, cookies, security headers | 386 |
| `settings.py` | Reads settings from `.env` and the environment | 70 |
| `search.py` | Splits the manual, BM25 search, the "enough evidence" rule | 101 |
| `ai.py` | Gemini calls, the grounded answer, refusals, general guidance | 146 |
| `safety.py` | Prompt-injection defence: hidden text removal, instruction detection | 55 |
| `auth.py` | Accounts, passwords, OTP, technician numbers, password reset, sessions, rate limits | 390 |
| `mail.py`, `net.py`, `store.py` | Sending email, one web-request helper, saving data | 68, 12, 63 |
| `pages.py` | Builds every HTML page | 378 |
| `art.py` | The SVG animations and device diagrams | 264 |
| `static/style.css`, `static/app.js` | Look, animations, the loader-to-answer script | 337, 106 |
| `evaluate.py` | The evaluation for the lecturer's evidence | 246 |
| `tests/` | Unit tests, end-to-end tests, a fake Gemini | 489 |

Data flows one way: `app.py` calls `auth`, `search`, `ai`, `pages`. `ai` calls `search` and `safety`. Nothing calls `app.py`.

## 3. Three journeys

**Sign up.** `pages.signup_page` form -> `app.route_post("/signup")` -> `auth.start_signup`: checks username, email, password, then that the technician number exists
and is unused, then emails a six-digit code (`mail.send_code_email`) and stores a hashed copy in `PENDING`. -> `/verify` -> `auth.finish_signup`: compares the code,
then, under a lock, marks the number as used and creates the account. No account exists until the code is right.

**Ask the manual.** `/search?mode=manual&q=...` -> `search.Index.search` returns the top 3 sections -> `pages.manual_results` draws the loader, the matching sections and a device diagram.
The browser script then calls `/api/answer` -> `ai.answer_from_manual` -> answer and sources come back and are revealed line by line.

**Ask the AI (general).** `/api/answer?mode=ai` -> `ai.general_answer` (no manual text in the prompt) -> the server picks a diagram from the words in the question and answer
(`art.kind_for_text`) and highlights ports that the answer mentions (`art.ports_mentioned`).

## 4. Search: BM25 in pure Python (`search.py`)

1. `tokenize` lowercases, removes stop words and trims endings (`stem`), so "switches" matches "switch".
2. For each section we count term frequencies. The title words are repeated three times so a title match counts more.
3. BM25 score for one term: `idf * f * (k1 + 1) / (f + k1 * (1 - b + b * length / average_length))`, with `k1 = 1.5`, `b = 0.75`.
   `idf = log(1 + (N - df + 0.5) / (df + 0.5))` makes rare words worth more. Scores of all question terms are added.
4. `coverage` = the share of the question's words found in a section. `enough_evidence` requires the best section to reach `MIN_COVERAGE = 0.4`, otherwise the app refuses before calling any AI.
5. The reference shown to the user is the section number (the manual has no page numbers).

## 5. The ideas an examiner will probe

**Retrieval before generation.** The AI only ever sees the retrieved sections. If retrieval fails, the AI cannot fix it. That is why retrieval and answers are measured separately.

**Refusal has four layers (`ai.answer_from_manual`).**
1. `no_match`: the best section matches too few of the question's words, so no AI call is made.
2. `model_refused`: the prompt tells the model to reply `NOT IN MANUAL` if the sections do not contain the answer.
3. `bad_citation`: the answer must end with `SOURCES:` and every cited number must be among the retrieved sections.
4. `not_grounded` (`is_grounded`): at least half of the answer's content words must appear in the cited sections, and any link or email address in the answer must appear in them too.

**Prompt injection (module M6, `safety.py`).**
- `strip_hidden` removes HTML comments, HTML tags and zero-width characters when the manual is loaded, so hidden text cannot reach the model or the screen.
- `neutralize` replaces any paragraph that contains instruction-like text (patterns such as "ignore previous instructions", "you are now", "SOURCES:", links, email addresses) with a removal note, before the prompt is built.
- The prompt wraps each section in `<manual_section>` tags and says it is untrusted data.
- The output checks above reject answers that cite sections that do not exist or contain outside links.
- Known limit: a subtle rewrite of a procedure that uses no instruction-like words is not caught. It is listed in `eval/RESULTS.md` as a residual risk.

**General AI guidance is separate on purpose.** It never uses the manual, starts with "General AI guidance (not from the manual)", and the page shows a warning banner. It is not part of the evaluation.

**Security features.** Passwords: PBKDF2-SHA256, 600,000 rounds, random salt. Codes and reset tokens are stored only as hashes. Codes expire in 10 minutes and allow 5 tries.
Reset links are single use, last 30 minutes and end all logins for that account. Rate limits cover logins, emails, technician-number guesses and AI questions.
Forms carry a CSRF token. Pages send a strict content security policy. Cookies are HttpOnly, SameSite and Secure over https. The reset request gives the same message for known and unknown emails.

**Animations.** `art.py` returns SVG text; `static/style.css` animates it. The pages use no inline styles or scripts, which the content security policy would block.
`prefers-reduced-motion` turns the movement off and shows the finished state.

## 6. Configuration and storage

`settings.py` reads `.env` and the environment once at start. `store.py` saves two JSON files (`users.json`, `technicians.json`), or, if Upstash is configured,
the same data in an online database. Writes are atomic (write a temp file, then replace).

## 7. Likely questions, with short answers

1. **Why BM25 and not plain counting?** It weights rare words more (idf) and stops long sections winning just by being long (length normalisation).
2. **Why retrieve first?** It limits what the model can say to evidence we can show and check, and lets us measure retrieval on its own.
3. **How do you stop the AI inventing things?** Four layers of refusal and checks (section 5). It can still be wrong inside the cited text, so the sources are linked.
4. **What is recall@3?** The share of questions whose correct section is among the top 3 results. Ours is 100% on 40 questions (see `eval/RESULTS.md`).
5. **Why is the keyword baseline already strong?** The manual is short and its wording is distinctive. The AI adds value by writing a direct answer and by refusing, which the baseline cannot do.
6. **How do you know refusal works?** `evaluate.py` runs 10 questions the manual does not cover. Run it with a key for the AI-stage result.
7. **What is prompt injection here?** Text inside the manual that tries to give the model orders. We strip hidden text, remove instruction-like paragraphs, mark sections as untrusted, and verify the output.
8. **Why can't anyone sign up without a number?** The signup form checks the number before sending any email, and the account only gets access while its number is still in the administrator's list.
9. **Is the administrator a weakness?** It is a single account with no recovery by email. A real system would add two-factor login and more than one administrator.
10. **What are the limits?** Sessions are kept in memory (a restart logs everyone out), accounts are stored in a JSON file or one online key, and key-fact matching in the evaluation is a simple automatic judge.

## 8. Five-minute demonstration

1. Landing page: point out the animated scene and the four access steps.
2. Log in as the administrator, generate a technician number.
3. Sign up as a technician with that number, show the code arriving, confirm it.
4. Ask the manual "access point offline what to check": show the loader, the answer, the section links, the highlighted ports.
5. Ask something the manual lacks ("warranty period for replacement switches"): show the refusal.
6. Switch to AI guidance with the same question: show the banner that it is not from the manual.
7. Show `eval/RESULTS.md` and run `python evaluate.py --offline`.
8. Show a password reset email and the single-use link.
