# Settings, email, AI and hosting

## 1. Run on your computer

1. In this folder: `python app.py` (Windows: double-click `start_app.bat`).
2. Open http://127.0.0.1:8000
3. Copy `.env.example` to `.env` and fill in what you have. The app reads `.env` from this folder when it starts.

With no `.env` the app still starts in demo mode: emails (codes and reset links) are printed in the terminal, AI is off,
and a random administrator password is printed for that run.

## 2. Settings

| Setting | Meaning |
|---|---|
| `ADMIN_USERNAME`, `ADMIN_PASSWORD` | The one administrator. Set a long password. |
| `GEMINI_API_KEY` | Turns on both AI options. |
| `GEMINI_MODEL` | Only if the app says no model worked. Copy a model id from Google AI Studio. |
| `EMAIL_ADDRESS` | The address that sends emails. |
| `EMAIL_PASSWORD` | Gmail app password (own computer or tunnel). |
| `BREVO_API_KEY` | Sends email over HTTPS (free cloud hosts). |
| `PUBLIC_URL` | The public address of the site. Reset links in emails start with it. |
| `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Online database that keeps accounts and numbers on hosts that erase files. |
| `PORT`, `DATA_DIR`, `MANUAL_FILE` | Advanced. |

At start-up the app prints what it is using: email mode, AI, storage, the reset link address and the administrator name.

## 3. Email

Codes and reset links are only emailed when email is set up. Pick one:

**Gmail (own computer or tunnel).** Turn on 2-Step Verification, create an App password in your Google account, then set
`EMAIL_ADDRESS=you@gmail.com` and `EMAIL_PASSWORD=` the 16-character password.

**Brevo (free cloud hosting).** Make a free account at https://www.brevo.com (300 emails a day). Add and verify a sender address in Brevo,
create an API key, then set `EMAIL_ADDRESS=` the verified sender and `BREVO_API_KEY=` the key. A Gmail sender works but may land in spam.

## 4. AI (Google Gemini, free)

Get a key at https://aistudio.google.com and set `GEMINI_API_KEY`. The free tier has request limits, and Google may use free-tier content to
improve its products, so keep confidential material out of the manual. Both answer options use the same key.

## 5. Administrator, technician numbers and password recovery

1. Log in as the administrator and open **Technician numbers**.
2. Press **Generate number**. A number like `TECH-482913` is created. Give it to the technician.
3. The technician opens **Create an account**, enters the number, a username, an email address and a password, then the six-digit code emailed to that address.
4. Nobody can sign up, and nobody can open the manual, without a number. **Remove** a number to cut that person's access immediately.
5. A technician who forgets the password uses **Forgot your password?**. A single-use link is emailed to the address on the account and works for 30 minutes.
   A reset signs out every existing login for that account.

The administrator is the only account that does not need a number, because it is the account that issues them. It has no email, so its password
can only be changed in the settings.

## 6. Hosting online at a public address

Reset links and the site itself need a public address. Choose one.

**A. Cloudflare quick tunnel (free, runs on your own computer).** Best for a demonstration or marking.
1. Install once: `winget install --id Cloudflare.cloudflared`.
2. Start the tunnel: `cloudflared tunnel --url http://localhost:8000`. It prints an address like `https://something.trycloudflare.com`.
3. Put that address in `.env` as `PUBLIC_URL=...` (no slash at the end), then start the app with `python app.py`.
The computer must stay on, and the address changes every time, so repeat step 3 each time. Gmail and local files work normally.

**B. Render free plan with two free helper services (always on, no computer needed).** Checked November 2026: the free plan sleeps after 15 idle
minutes, erases files when it restarts, and blocks the ports Gmail uses. So you also need Upstash (database) and Brevo (email).
1. Put the project in a **private** GitHub repository (see section 7).
2. Create a free Upstash Redis database and copy its REST URL and token.
3. Do the Brevo steps in section 3.
4. On https://render.com choose New, Blueprint, and select the repository (it reads `render.yaml`). Enter the values it asks for.
   `PUBLIC_URL` is the address Render gives the service.
5. In the Logs you want: `Email: ON via Brevo`, `Storage: online database, connected`, `AI: Gemini`.
After 15 idle minutes the first visit takes about a minute, and everyone is logged out; accounts and numbers are kept.
Render says free instances are not for production, so use this for a demonstration.

**C. A paid host with a disk** keeps files, so you can leave out Upstash. Set `DATA_DIR` to the disk folder.

## 7. Put it on GitHub

1. Create a **private** repository on https://github.com, with no README.
2. In PowerShell, inside this folder:
   ```
   git init
   git add .
   git status
   ```
   The list must not show `.env`, `users.json` or `technicians.json`. If `.env` appears, stop.
   ```
   git commit -m "Technician manual search"
   git branch -M main
   git remote add origin https://github.com/YOUR-NAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```
3. Never put a password or API key in a file you commit. Keys go in `.env` locally and in the host's Environment page online.
   If a key was ever pasted into a chat or a commit, delete it at its provider and make a new one.

## 8. Troubleshooting

- **Codes or reset emails never arrive:** you are in demo mode (the email is printed in the terminal) or the email settings are wrong. On Render use Brevo, check the Logs for
  `[EMAIL ERROR]`, and check spam. A Brevo 400 usually means the sender address is not verified.
- **The reset link opens the wrong address:** `PUBLIC_URL` is missing or old. Set it and restart.
- **AI says no model worked:** set `GEMINI_MODEL`. **AI says the limit was reached:** wait a minute.
- **Accounts vanish after a restart:** the host erases files. Use Upstash (option B) or a disk (option C).
