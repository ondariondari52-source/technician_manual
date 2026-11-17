import hashlib
import hmac
import re
import secrets
import time
from datetime import datetime

import mail
import settings
import store
from store import LOCK

ROUNDS = 600_000
NUMBER_PATTERN = re.compile(r"TECH-\d{6}")
COMMON_PASSWORDS = {"password", "password1", "password123", "12345678", "123456789", "1234567890",
                    "qwerty123", "qwertyui", "iloveyou", "admin123", "welcome1", "letmein1"}

SESSIONS = {}
PENDING = {}
RESETS = {}


class Limiter:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.events = {}

    def recent(self, key):
        now = time.time()
        fresh = [t for t in self.events.get(key, []) if now - t < self.window]
        if fresh:
            self.events[key] = fresh
        else:
            self.events.pop(key, None)
        return fresh

    def blocked(self, key):
        with LOCK:
            return len(self.recent(key)) >= self.limit

    def hit(self, key):
        with LOCK:
            self.events[key] = self.recent(key) + [time.time()]

    def clear(self, key):
        with LOCK:
            self.events.pop(key, None)


LOGIN_USER = Limiter(5, 300)
LOGIN_IP = Limiter(30, 300)
MAIL_IP = Limiter(6, 3600)
MAIL_ADDRESS = Limiter(4, 3600)
NUMBER_IP = Limiter(8, 600)
NUMBER_USER = Limiter(5, 600)
AI_USER = Limiter(15, 60)


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ROUNDS)
    return f"{ROUNDS}${salt}${digest.hex()}"


def check_password(password, stored):
    rounds, salt, expected = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds))
    return hmac.compare_digest(digest.hex(), expected)


def password_problem(password, username, email):
    if len(password) < settings.MIN_PASSWORD_LENGTH:
        return f"Password must be at least {settings.MIN_PASSWORD_LENGTH} characters."
    if len(password) > 128:
        return "Password must be 128 characters or fewer."
    lowered = password.lower()
    if lowered in COMMON_PASSWORDS or lowered == username.lower() or lowered == email.split("@")[0]:
        return "That password is too easy to guess. Choose something less common."
    if len(set(password)) < 4:
        return "Password needs more variety than that."
    return None


def clean_email(text):
    text = text.strip().lower()
    if len(text) <= 254 and re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", text):
        return text
    return None


def clean_number(text):
    return re.sub(r"\s+", "", text).upper()


def mask_email(address):
    name, _, domain = address.partition("@")
    return (name[:1] + "***" if len(name) > 1 else name) + "@" + domain


def accounts():
    return store.read("users")


def technicians():
    return store.read("technicians")


def find_account(identifier):
    key = identifier.strip().lower()
    found = accounts()
    if key in found:
        return found[key]
    for account in found.values():
        if account["email"] == key:
            return account
    return None


def username_taken(name):
    return name.lower() == settings.ADMIN_USERNAME.lower() or name.lower() in accounts()


def email_taken(email):
    return any(account["email"] == email for account in accounts().values())


def create_technician(holder, admin_name):
    holder = " ".join(holder.split())[:60]
    with LOCK:
        existing = technicians()
        number = "TECH-%06d" % secrets.randbelow(1_000_000)
        while number in existing:
            number = "TECH-%06d" % secrets.randbelow(1_000_000)
        existing[number] = {"holder": holder, "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "created_by": admin_name, "claimed_by": None}
        store.write("technicians", existing)
    return number


def delete_technician(number):
    with LOCK:
        existing = technicians()
        record = existing.pop(number, None)
        if not record:
            return False
        store.write("technicians", existing)
        owner = (record["claimed_by"] or "").lower()
        users = accounts()
        if owner in users:
            users[owner]["tech_number"] = ""
            store.write("users", users)
    return True


def number_available(number):
    record = technicians().get(number)
    return bool(NUMBER_PATTERN.fullmatch(number) and record and not record["claimed_by"])


def make_code():
    return "%06d" % secrets.randbelow(1_000_000)


def code_digest(code):
    return hashlib.sha256(code.encode()).hexdigest()


def start_signup(username, email_text, password, number_text, ip):
    number = clean_number(number_text)
    email = clean_email(email_text)
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
        return None, "Username must be 3 to 20 letters, numbers or underscores."
    if not email:
        return None, "Enter a valid email address."
    problem = password_problem(password, username, email)
    if problem:
        return None, problem
    if NUMBER_IP.blocked(ip):
        return None, "Too many wrong technician numbers. Wait ten minutes and try again."
    if not number_available(number):
        NUMBER_IP.hit(ip)
        return None, "That technician number is not valid, or it has already been used. Ask your administrator."
    if username_taken(username):
        return None, "That username is already taken."
    if email_taken(email):
        return None, "An account with that email address already exists."
    if MAIL_IP.blocked(ip) or MAIL_ADDRESS.blocked(email):
        return None, "Too many codes were requested. Wait a while and try again."
    code = make_code()
    MAIL_IP.hit(ip)
    MAIL_ADDRESS.hit(email)
    sent, message = mail.send_code_email(email, code)
    if not sent:
        return None, message
    pending_id = secrets.token_urlsafe(16)
    now = time.time()
    with LOCK:
        for old in [k for k, v in PENDING.items() if v["expires"] < now]:
            del PENDING[old]
        PENDING[pending_id] = {"username": username, "email": email, "password": hash_password(password), "number": number,
                               "code_hash": code_digest(code), "expires": now + settings.CODE_MINUTES * 60,
                               "tries": 0, "last_sent": now, "flash": (f"We emailed a code to {mask_email(email)}.", "ok")}
    return pending_id, message


def finish_signup(pending_id, typed_code):
    with LOCK:
        item = PENDING.get(pending_id)
        if not item:
            return None, "That signup has expired. Please start again."
        if time.time() > item["expires"]:
            del PENDING[pending_id]
            return None, "That code has expired. Please start again."
        item["tries"] += 1
        if item["tries"] > settings.MAX_CODE_TRIES:
            del PENDING[pending_id]
            return None, "Too many wrong codes. Please start again."
        if not hmac.compare_digest(code_digest(typed_code.strip()), item["code_hash"]):
            return None, f"That code is not correct. {settings.MAX_CODE_TRIES - item['tries']} tries left."
        del PENDING[pending_id]
        techs = technicians()
        record = techs.get(item["number"])
        if not record or record["claimed_by"]:
            return None, "That technician number was used or removed while you were signing up. Ask your administrator."
        if username_taken(item["username"]) or email_taken(item["email"]):
            return None, "That username or email address was taken while you were signing up."
        record["claimed_by"] = item["username"]
        users = accounts()
        users[item["username"].lower()] = {"username": item["username"], "email": item["email"], "password": item["password"],
                                           "tech_number": item["number"], "created": datetime.now().strftime("%Y-%m-%d %H:%M")}
        store.write("technicians", techs)
        store.write("users", users)
    return item["username"], ""


def resend_code(pending_id, ip):
    with LOCK:
        item = PENDING.get(pending_id)
    if not item:
        return False, "That signup has expired. Please start again."
    wait = settings.RESEND_SECONDS - (time.time() - item["last_sent"])
    if wait > 0:
        return False, f"Please wait {int(wait) + 1} seconds before asking again."
    if MAIL_IP.blocked(ip) or MAIL_ADDRESS.blocked(item["email"]):
        return False, "Too many codes were requested. Wait a while and try again."
    code = make_code()
    MAIL_IP.hit(ip)
    MAIL_ADDRESS.hit(item["email"])
    sent, message = mail.send_code_email(item["email"], code)
    if sent:
        with LOCK:
            item.update(code_hash=code_digest(code), tries=0, last_sent=time.time(),
                        expires=time.time() + settings.CODE_MINUTES * 60)
        return True, f"We emailed a new code to {mask_email(item['email'])}."
    return False, message


def login(identifier, password, ip):
    key = identifier.strip().lower()
    if not key or len(key) > 254 or len(password) > 200:
        return None, "Wrong username or password."
    if LOGIN_USER.blocked(key) or LOGIN_IP.blocked(ip):
        return None, "Too many attempts. Wait five minutes and try again."
    found = None
    if key == settings.ADMIN_USERNAME.lower():
        if hmac.compare_digest(password.encode(), settings.ADMIN_PASSWORD.encode()):
            found = settings.ADMIN_USERNAME
    else:
        account = find_account(key)
        if account:
            if check_password(password, account["password"]):
                found = account["username"]
        else:
            hash_password(password)
    if found is None:
        LOGIN_USER.hit(key)
        LOGIN_IP.hit(ip)
        return None, "Wrong username or password."
    LOGIN_USER.clear(key)
    return found, ""


def profile(username):
    if username.lower() == settings.ADMIN_USERNAME.lower():
        return {"name": settings.ADMIN_USERNAME, "admin": True, "email": "", "tech": "", "access": True}
    account = accounts().get(username.lower())
    if not account:
        return None
    number = account.get("tech_number") or ""
    record = technicians().get(number) if number else None
    valid = bool(record and (record["claimed_by"] or "").lower() == username.lower())
    return {"name": account["username"], "admin": False, "email": account["email"],
            "tech": number if valid else "", "access": valid}


def claim_number(username, number_text):
    number = clean_number(number_text)
    key = username.lower()
    if NUMBER_USER.blocked(key):
        return False, "Too many wrong technician numbers. Wait ten minutes, or ask your administrator."
    with LOCK:
        techs = technicians()
        record = techs.get(number)
        users = accounts()
        account = users.get(key)
        if not account or not NUMBER_PATTERN.fullmatch(number) or not record or record["claimed_by"]:
            NUMBER_USER.hit(key)
            return False, "That technician number is not valid, or it has already been used."
        record["claimed_by"] = account["username"]
        account["tech_number"] = number
        store.write("technicians", techs)
        store.write("users", users)
    return True, "Technician number accepted. The manual is unlocked."


def request_reset(email_text, ip):
    generic = "If that email address belongs to an account, we have sent a link to reset the password."
    email = clean_email(email_text)
    if not email:
        return False, "Enter a valid email address."
    if MAIL_IP.blocked(ip) or MAIL_ADDRESS.blocked(email):
        return False, "Too many requests. Wait a while and try again."
    MAIL_IP.hit(ip)
    MAIL_ADDRESS.hit(email)
    account = find_account(email)
    if account:
        token = secrets.token_urlsafe(32)
        now = time.time()
        with LOCK:
            for old in [k for k, v in RESETS.items() if v["expires"] < now or v["username"] == account["username"]]:
                del RESETS[old]
            RESETS[hashlib.sha256(token.encode()).hexdigest()] = {"username": account["username"], "expires": now + settings.RESET_MINUTES * 60}
        mail.send_reset_email(email, f"{settings.public_url()}/reset?token={token}")
    return True, generic


def reset_token_valid(token):
    item = RESETS.get(hashlib.sha256(token.encode()).hexdigest())
    return bool(item and item["expires"] > time.time())


def reset_password(token, password, confirm):
    key = hashlib.sha256(token.encode()).hexdigest()
    with LOCK:
        item = RESETS.get(key)
        if not item or item["expires"] < time.time():
            return False, "That reset link has expired or was already used. Ask for a new one."
        if password != confirm:
            return False, "The two passwords do not match."
        users = accounts()
        account = users.get(item["username"].lower())
        if not account:
            return False, "That account no longer exists."
        problem = password_problem(password, account["username"], account["email"])
        if problem:
            return False, problem
        account["password"] = hash_password(password)
        store.write("users", users)
        del RESETS[key]
    LOGIN_USER.clear(account["username"].lower())
    LOGIN_USER.clear(account["email"])
    end_sessions_for(account["username"])
    return True, "Your password was changed. You can log in now."


def start_session(username):
    now = time.time()
    for old in [t for t, s in SESSIONS.items() if s["expires"] < now]:
        del SESSIONS[old]
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = {"user": username, "expires": now + settings.SESSION_HOURS * 3600, "flash": None}
    return token


def session_for(token):
    item = SESSIONS.get(token)
    if item and item["expires"] < time.time():
        del SESSIONS[token]
        return None
    return item


def end_session(token):
    SESSIONS.pop(token, None)


def end_sessions_for(username):
    for token in [t for t, s in SESSIONS.items() if s["user"].lower() == username.lower()]:
        del SESSIONS[token]
