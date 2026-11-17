import http.cookiejar
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fake_gemini

APP_PORT, GEMINI_PORT = 8280, 8281
BASE = f"http://127.0.0.1:{APP_PORT}"
ADMIN_PASSWORD = "Admin-Test-Pass-77"
RESULTS = []
LOG_PATH = ""


def check(name, condition):
    RESULTS.append(bool(condition))
    print(("PASS " if condition else "FAIL ") + name)


class Client:
    def __init__(self):
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))

    def get(self, path):
        try:
            reply = self.opener.open(BASE + path)
            return reply.status, reply.read().decode(), reply
        except urllib.error.HTTPError as problem:
            return problem.code, problem.read().decode(), problem

    def csrf(self):
        return next((c.value for c in self.jar if c.name == "csrf"), "")

    def post(self, path, data, with_csrf=True):
        fields = dict(data)
        if with_csrf:
            fields["csrf"] = self.csrf()
        try:
            reply = self.opener.open(BASE + path, urllib.parse.urlencode(fields).encode())
            return reply.status, reply.read().decode(), reply
        except urllib.error.HTTPError as problem:
            return problem.code, problem.read().decode(), problem

    def api(self, mode, question):
        status, body, _ = self.get(f"/api/answer?mode={mode}&q={urllib.parse.quote(question)}")
        return json.loads(body)


def start_app(data_dir, log_path):
    env = dict(os.environ, PORT=str(APP_PORT), DATA_DIR=data_dir, ADMIN_USERNAME="Johnson", ADMIN_PASSWORD=ADMIN_PASSWORD,
               GEMINI_API_KEY="fake-key", GEMINI_BASE_URL=f"http://127.0.0.1:{GEMINI_PORT}/v1beta/models",
               PUBLIC_URL="https://manual.example.org", EMAIL_ADDRESS="", EMAIL_PASSWORD="", BREVO_API_KEY="",
               UPSTASH_REDIS_REST_URL="", UPSTASH_REDIS_REST_TOKEN="")
    log = open(log_path, "w")
    process = subprocess.Popen([sys.executable, os.path.join(ROOT, "app.py")], cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT)
    process.log_file = log
    for _ in range(40):
        try:
            urllib.request.urlopen(BASE + "/healthz", timeout=1)
            return process
        except Exception:
            time.sleep(0.25)
    raise SystemExit("The app did not start")


def last_email(log_path, address):
    with open(log_path) as f:
        text = f.read()
    blocks = [b for b in text.split("[DEMO MODE] Email to ")[1:] if b.startswith(address)]
    return blocks[-1] if blocks else ""


def run():
    data_dir = tempfile.mkdtemp()
    global LOG_PATH
    log_path = os.path.join(data_dir, "server.log")
    LOG_PATH = log_path
    fake_gemini.start(GEMINI_PORT)
    process = start_app(data_dir, log_path)
    try:
        public_pages(log_path)
        accounts_and_numbers(log_path)
        password_reset(log_path)
        answers()
        lockout()
    finally:
        process.terminate()
        process.wait(timeout=5)
        with open(log_path) as f:
            log = f.read()
        check("server log has no Traceback", "Traceback" not in log)
        shutil.rmtree(data_dir, ignore_errors=True)
    print(f"\n{sum(RESULTS)} of {len(RESULTS)} checks passed")
    return all(RESULTS)


def public_pages(log_path):
    visitor = Client()
    status, body, reply = visitor.get("/")
    check("landing page shows the company name", status == 200 and "Software Engineering EEE 2026" in body)
    check("landing page has the animated people-and-devices scene", "class=\"scene\"" in body and "technician" in body.lower())
    check("landing page has four animated access steps", body.count("step-card") >= 4 and "TECH-" in body)
    check("landing page explains both answer options", "From the manual" in body and "AI guidance" in body and "Not from the manual" in body)
    check("security headers are sent", reply.headers.get("X-Frame-Options") == "DENY" and "default-src 'self'" in reply.headers.get("Content-Security-Policy", ""))
    check("stylesheet and script are served", visitor.get("/assets/style.css")[0] == 200 and visitor.get("/assets/app.js")[0] == 200)
    check("health check answers", visitor.get("/healthz")[2].status == 200)
    check("dashboard is closed to visitors", "Welcome," not in visitor.get("/dashboard")[1])
    check("search is closed to visitors", "Log in" in visitor.get("/search?q=switch")[1] and "Matching" not in visitor.get("/search?q=switch")[1])
    check("the answer API is closed to visitors", "Log in" in visitor.get("/api/answer?mode=manual&q=switch")[1])
    check("login page links to password recovery", "/forgot" in visitor.get("/login")[1])
    check("POST without the CSRF token is refused", visitor.post("/login", {"username": "x", "password": "y"}, with_csrf=False)[0] == 403)


def accounts_and_numbers(log_path):
    admin = Client()
    admin.get("/login")
    status, body, _ = admin.post("/login", {"username": "Johnson", "password": "wrong"})
    check("wrong admin password gives a generic error", "Wrong username or password" in body)
    status, body, _ = admin.post("/login", {"username": "johnson", "password": ADMIN_PASSWORD})
    check("administrator logs in and sees the dashboard", "Welcome, Johnson" in body and "Technician numbers" in body)
    status, body, _ = admin.post("/admin/generate", {"holder": "Ada Lovelace"})
    number = re.search(r"TECH-\d{6}", body).group(0)
    check("administrator generates a technician number", "Created " + number in body and "Ada Lovelace" in body)
    status, body, _ = admin.post("/admin/generate", {"holder": "Second"})
    second = [n for n in re.findall(r"TECH-\d{6}", body) if n != number][0]
    check("each generated number is different", second != number)

    tech = Client()
    tech.get("/signup")
    base = {"username": "tom_tech", "email": "tom@example.com", "password": "Tr1cky-pass-9", "number": number}
    check("signup without a technician number is refused", "not valid" in tech.post("/signup", dict(base, number=""))[1])
    check("signup with a made-up technician number is refused", "not valid" in tech.post("/signup", dict(base, number="TECH-000000"))[1])
    check("signup refuses a weak password", "too easy" in tech.post("/signup", dict(base, password="password123"))[1])
    check("signup refuses a bad email", "valid email" in tech.post("/signup", dict(base, email="nope"))[1])
    check("administrator username cannot be taken", "already taken" in tech.post("/signup", dict(base, username="Johnson"))[1])
    status, body, _ = tech.post("/signup", base)
    check("valid signup goes to the verify page with the email masked", "Check your email" in body and "t***@example.com" in body)
    pending = re.search(r"name='id' value='([^']+)'", body).group(1)
    mail = last_email(log_path, "tom@example.com")
    code = re.search(r"verification code is (\d{6})", mail).group(1)
    check("the one-time code is emailed to the signup address", len(code) == 6)
    wrong = "000000" if code != "000000" else "111111"
    check("a wrong code is refused with tries left", "4 tries left" in tech.post("/verify", {"id": pending, "code": wrong})[1])
    check("resending too quickly is throttled", "Please wait" in tech.post("/resend", {"id": pending})[1])
    probe = Client()
    probe.get("/login")
    check("the unconfirmed account cannot log in", "Wrong username or password" in probe.post("/login", {"username": "tom_tech", "password": "Tr1cky-pass-9"})[1])
    status, body, _ = tech.post("/verify", {"id": pending, "code": code})
    check("the right code creates the account and opens the dashboard", "Welcome, tom_tech" in body and number in body)
    check("technician can read the manual", "Best matching sections" in tech.get("/search?mode=manual&q=firmware")[1])
    check("technician cannot open the admin page", tech.get("/admin")[0] == 403)

    other = Client()
    other.get("/signup")
    check("a used technician number cannot be used again", "not valid" in other.post("/signup", dict(base, username="sam_two", email="sam@example.com"))[1])
    for _ in range(8):
        other.post("/signup", dict(base, username="sam_two", email="sam@example.com", number="TECH-999999"))
    check("guessing technician numbers is rate limited", "Too many wrong technician numbers" in other.post("/signup", dict(base, username="sam_two", email="sam@example.com", number="TECH-999998"))[1])

    admin.post("/admin/delete", {"number": number})
    status, body, _ = tech.get("/dashboard")
    check("removing the number removes access immediately", "Technician number needed" in body)
    check("without a number the search stays closed", "Technician number needed" in tech.get("/search?q=switch")[1])
    status, body, _ = tech.post("/activate", {"number": second})
    check("a new number from the administrator restores access", "Welcome, tom_tech" in body and second in body)



def password_reset(log_path):
    tech = Client()
    tech.get("/login")
    status, body, _ = tech.post("/forgot", {"email": "nobody@example.com"})
    unknown = re.sub(r"\s+", " ", body)
    status, body, _ = tech.post("/forgot", {"email": "tom@example.com"})
    check("reset request gives the same message for known and unknown emails", "If that email address belongs to an account" in body and "If that email address belongs to an account" in unknown)
    mail = last_email(log_path, "tom@example.com")
    link = re.search(r"https://manual\.example\.org/reset\?token=([\w\-]+)", mail)
    check("a reset link is emailed and uses the public address", bool(link))
    check("nothing is emailed for an unknown address", last_email(log_path, "nobody@example.com") == "")
    token = link.group(1)
    local = f"/reset?token={token}"
    session = Client()
    session.get("/login")
    session.post("/login", {"username": "tom_tech", "password": "Tr1cky-pass-9"})
    check("the reset form opens from the emailed link", "Choose a new password" in session.get(local)[1])
    check("a made-up token is refused", session.get("/reset?token=not-a-real-token")[0] == 400)
    check("mismatched passwords are refused", "do not match" in session.post("/reset", {"token": token, "password": "Brand-New-pass-1", "confirm": "different"})[1])
    check("a weak new password is refused", "too easy" in session.post("/reset", {"token": token, "password": "password123", "confirm": "password123"})[1])
    status, body, _ = session.post("/reset", {"token": token, "password": "Brand-New-pass-1", "confirm": "Brand-New-pass-1"})
    check("the new password is saved", "Your password was changed" in body)
    check("the reset link works only once", session.get(local)[0] == 400)
    check("existing logins were signed out by the reset", "Welcome," not in session.get("/dashboard")[1])
    old = Client()
    old.get("/login")
    check("the old password no longer works", "Wrong username or password" in old.post("/login", {"username": "tom_tech", "password": "Tr1cky-pass-9"})[1])
    new = Client()
    new.get("/login")
    check("the new password works", "Welcome, tom_tech" in new.post("/login", {"username": "tom_tech", "password": "Brand-New-pass-1"})[1])


def lockout():
    locked = Client()
    locked.get("/login")
    for _ in range(5):
        locked.post("/login", {"username": "tom_tech", "password": "not-the-password"})
    check("five bad passwords lock the account for a while", "Too many attempts" in locked.post("/login", {"username": "tom_tech", "password": "Brand-New-pass-1"})[1])
    locked.post("/forgot", {"email": "tom@example.com"})
    token = re.search(r"https://manual\.example\.org/reset\?token=([\w\-]+)", last_email(LOG_PATH, "tom@example.com")).group(1)
    locked.post("/reset", {"token": token, "password": "Another-New-pass-2", "confirm": "Another-New-pass-2"})
    check("a successful password reset clears the lockout", "Welcome, tom_tech" in locked.post("/login", {"username": "tom_tech", "password": "Another-New-pass-2"})[1])


def answers():
    admin = Client()
    admin.get("/login")
    admin.post("/login", {"username": "Johnson", "password": ADMIN_PASSWORD})
    status, body, _ = admin.get("/search?mode=manual&q=" + urllib.parse.quote("access point offline what to check"))
    check("manual option shows the animated loader and the answer box", "id='answer-box'" in body and "class=\"loader\"" in body and "data-mode='manual'" in body)
    check("manual option shows section references", "Section 3" in body)
    check("manual option shows a device guide with highlighted ports", "port hl" in body and "legend" in body)
    status, body, _ = admin.get("/search?mode=ai&q=" + urllib.parse.quote("switch port is down"))
    check("AI option is clearly labelled as not from the manual", "not from the manual" in body.lower() and "data-mode='ai'" in body)
    result = admin.api("manual", "access point offline what to check")
    check("grounded answer is returned with verified citations", bool(result["answer"]) and 3 in result["sources"])
    result = admin.api("manual", "What is the warranty period for replacement switches?")
    check("manual answer refuses when the model says the sections do not cover it", result["answer"] == "" and "do not contain an answer" in result["reason"])
    result = admin.api("manual", "How do I train a neural network on football data?")
    check("manual answer refuses without any matching section", result["answer"] == "" and "No section" in result["reason"])
    result = admin.api("manual", "access point offline BAD_CITATION")
    check("an answer citing a section that was not retrieved is rejected", result["answer"] == "" and "could not be verified" in result["reason"])
    result = admin.api("manual", "access point offline UNGROUNDED")
    check("an answer the sections do not support is rejected", result["answer"] == "" and "did not support" in result["reason"])
    result = admin.api("manual", "access point offline LINKTEST")
    check("an answer containing an outside link is rejected", result["answer"] == "")
    result = admin.api("ai", "My switch uplink port is down, what should I check?")
    check("AI guidance is generated without the manual", result["answer"].startswith("General AI guidance (not from the manual)") and result["sources"] == [])
    check("AI guidance comes with a device image and port legend", "<svg" in result.get("figure", "") and "port hl" in result["figure"] and len(result.get("ports", [])) >= 1)
    prompt = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{GEMINI_PORT}/").read())["prompt"]
    check("AI guidance prompt contains no manual text", "<manual_section" not in prompt)


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
