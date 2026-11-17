# Validation against your requests and the lecturer's brief

Status words: **Met** (built and tested here), **Built, check it yourself** (built and tested as far as this environment allows, but needs your eyes or accounts),
**Not measured yet** (needs a Gemini key or a live service), **Gap** (not done or only partly done).

Tests run here: 23 unit tests and 62 end-to-end checks, all passing (`tests/unit_tests.py`, `tests/run_tests.py`). The end-to-end tests run the real server
against a fake Gemini, so they prove the logic and the wiring, not the quality of real Gemini answers.

## 1. Your six requests

| # | Request | Status | Evidence and notes |
|---|---|---|---|
| 1 | Two options: from the manual, and AI-generated not from the manual | **Met** | `pages.search_form` has two options. Manual mode: `ai.answer_from_manual`. AI mode: `ai.general_answer`, which never sends manual text (tested: "AI guidance prompt contains no manual text"). The AI page shows a warning banner and the answer starts with "General AI guidance (not from the manual)". |
| 2 | Landing page animation of how a technician accesses information, with people and devices | **Built, check it yourself** | `art.hero_scene`: a technician with a phone asks a question, the search finds sections 3 and 6, the answer returns, an access point goes from red to green, a resident gets Wi-Fi. `art.step_icons`: four animated steps (administrator hands over a number, technician signs up, email code arrives, lock opens). All SVG parses, every animation is defined, there are no inline styles. **I could not open a browser here, so I have not seen it move.** Open the landing page in Chrome or Edge and on a phone before presenting. |
| 3 | Remove comments, keep it simple for the exam and presentation | **Met** | Unit tests fail if any Python file has a comment or docstring, or the CSS/JS has comments. The code is 11 small modules instead of one 1,700-line file. `CODE_GUIDE.md` replaces the comments with an explanation, likely questions and a demo script. |
| 4 | OTP to the technician's email, technician number from the admin required, no access without one, password recovery by emailed link | **Met in tests; live email not tested** | Number is checked at signup before any email is sent. No number means no account and no access (`require` in `app.py`; tested for signup, dashboard, search and the answer API). Removing a number removes access at once (tested). Reset: single-use link, 30 minutes, same message for known and unknown emails, ends existing logins, clears lockout (all tested). **Real Gmail or Brevo delivery was not tested.** The administrator is the one account that needs no number, because it issues them. |
| 5 | Images and ports for guidance, and an animation for each search | **Built, check it yourself** | `art.guide_figure` draws an access point, switch, fiber ONT, ticket, phone or box. Ports are highlighted when the section or answer mentions them (`art.ports_mentioned`), with a legend. Every search shows an animated loader (a signal travelling along a cable, cycling captions), then the answer is revealed line by line and the diagram pops in. The diagrams are generic and say "Illustration only". They are not photos of your equipment. Not seen in a browser. |
| 6 | Validate against the lecturer's guidelines | This document | Section 2 below. |

## 2. The lecturer's brief: "Maintenance-manual question answering with retrieval"

| Requirement | Status | Evidence |
|---|---|---|
| Split the manual into sections | **Met** | `search.load_sections`: 13 sections (tested). |
| Keyword (BM25-style) search in pure Python | **Met** | `search.Index`, standard library only (`requirements.txt` is empty). |
| Return the best sections with page references | **Partly: agreed substitute** | The manual file has no page numbers, so you chose section numbers as the references (`search.reference`). If the lecturer insists on page numbers, the original document with pages is needed. |
| AI generates an answer only from retrieved sections | **Met (logic); real model not measured** | The prompt allows only the supplied sections and the output is checked against them (`ai.is_grounded`). |
| With citations | **Met** | The model must end with `SOURCES:`; every cited number must be among the retrieved sections; the page links each one. |
| Refuses when no section supports an answer | **Met (logic); AI-stage rate not measured yet** | Four layers: no match, model refusal, unverifiable citation, unsupported answer. Each is tested with a fake model. |
| 40 question-answer pairs written before building | **Gap you must state honestly** | `eval/questions.json` has 40 answerable and 10 unanswerable questions, drafted from the manual text and frozen with a checksum (`eval/questions.sha256`) **before any evaluation was run**. But the app itself already existed when they were written, so they were **not literally written before building**. Review them, change what you disagree with, and say so in your report. If you edit them, the checksum check in `evaluate.py` will print `False` (re-freeze by saving the new hash). |
| Retrieval recall@3 measured separately from answer correctness | **Met for retrieval** | Recall@3 = **100%** (40 of 40), recall@1 = 90%, mean reciprocal rank 0.95 (`eval/RESULTS.md`, section A). Answer correctness is section C. |
| Answer correctness | **Not measured yet** | Needs `GEMINI_API_KEY`. Run `python evaluate.py` (about 5 minutes). It judges an answer correct only if it contains the required facts (regular expressions in the question file) and cites a correct section. This is an automatic judge: read 10 answers yourself too. |
| Refusal rate on 10 unanswerable questions | **Not measured at the AI stage; retrieval stage caught 0 of 10** | The 10 questions share words with the manual ("access point", "switch"), so the retrieval-stage rule refuses none of them. Refusal depends on the model prompt and the output checks. The report includes a sensitivity table: raising the threshold to 0.5 refuses 3 of 10 but wrongly refuses 1 of 40 answerable questions, and 0.6 refuses 6 of 10 at the cost of 6 of 40. The shipped 0.4 was fixed before evaluating and was not tuned on these questions. |
| Keyword-only baseline compared with retrieval-augmented generation | **Baseline measured; generation not yet** | Baseline: the best section alone contains the required facts for **95%** of questions, the top 3 for **100%**. This baseline is strong because the manual is short with distinctive wording. The comparison against the AI answers appears in section C once you run the full evaluation. |
| M4: retrieval before generation, evaluate retrieval and answers separately | **Met** | `evaluate.py` reports retrieval (A), baseline (B) and generation (C) separately. |
| M6: prompt injection hidden in manual text | **Met for known attack styles; one residual risk** | `eval/RESULTS.md`, section D: hidden HTML comments, zero-width characters, visible instructions, fake system messages, outside links and fake citation lines are all kept out of the prompt (6 of 6). A subtle rewrite of a procedure with no instruction-like wording reaches the prompt; only the "treat as data" rule protects against it. The test first found that a two-sentence attack slipped through; the filter now removes the whole paragraph. Model-level behaviour under attack is measured only when you run the full evaluation. |

## 3. Checks beyond the brief

| Area | Status | Notes |
|---|---|---|
| Passwords and secrets | **Met** | PBKDF2-SHA256, 600,000 rounds. Codes and reset tokens stored as hashes. No secrets in code; `.gitignore` blocks `.env` and data files (tested with a throwaway repository earlier). |
| Abuse limits | **Met** | Login attempts, emails sent, technician-number guesses and AI questions are rate limited (tested). Trade-off: someone who knows a username can lock that account for 5 minutes; a successful password reset clears it. |
| Web security | **Met** | CSRF token on every form, strict content security policy, no inline scripts or styles, secure cookie flags. |
| Accessibility | **Partly** | Keyboard focus styles, labelled form fields, text alternatives on every SVG, reduced-motion support. Not tested with a screen reader or a contrast checker. |
| Different screens | **Not tested** | The layout has phone and tablet breakpoints but was not viewed on real devices. |
| Privacy | **Note** | Questions and manual sections go to Google when AI is on, and Google may use free-tier content to improve its products. Keep confidential material out of the manual. |
| Hosting | **Not tested live** | `DEPLOY.md` covers a tunnel and Render. On Render's free plan files are erased and Gmail is blocked, so Brevo and Upstash are needed. I could not reach Render, Upstash or Brevo from here; the Upstash and Brevo code paths were tested against local fakes. |

## 4. Known limits

- One administrator, no two-factor login, and its password cannot be reset by email.
- Logins are kept in memory, so a restart signs everyone out.
- The answer judge in `evaluate.py` is regular-expression matching; it can miss a correct answer worded differently.
- The injection filter is pattern based and can be bypassed by wording it does not know.
- The diagrams are generic illustrations.

## 5. Do this before you submit

1. Put your Gemini key in `.env` and run `python evaluate.py`. If `RESULTS.md` warns about AI errors, rerun with `--delay 8`.
2. Read the 50 questions and 10 of the AI answers, and write what you disagree with.
3. Open the site in Chrome or Edge and on a phone. Watch the landing animations and run one search in each option.
4. Send a real sign-up code and a real reset link to your own email.
5. If you host it online, set `PUBLIC_URL` and test the reset link from another device.
