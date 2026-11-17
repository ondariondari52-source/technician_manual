import hmac
import json
import os
import re
import secrets
import socket
import sys
import traceback
import urllib.parse
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import ai
import art
import auth
import mail
import pages
import search
import settings
import store

STATIC_FILES = {"style.css": "text/css; charset=utf-8", "app.js": "application/javascript; charset=utf-8", "icon.svg": "image/svg+xml"}
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": ("default-src 'self'; img-src 'self' data:; form-action 'self'; "
                                "frame-ancestors 'none'; base-uri 'none'; object-src 'none'"),
}


class Handler(BaseHTTPRequestHandler):
    sections = []
    index = None
    server_version = "EEE2026"
    sys_version = ""
    timeout = 20

    def log_message(self, *args):
        pass

    def ip(self):
        forwarded = self.headers.get("CF-Connecting-IP") or self.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        return forwarded or self.client_address[0]

    def https(self):
        return self.headers.get("X-Forwarded-Proto", "").lower() == "https"

    def cookie_value(self, name):
        try:
            morsel = SimpleCookie(self.headers.get("Cookie", "")).get(name)
        except Exception:
            return ""
        return morsel.value if morsel else ""

    def secure_flag(self):
        return "; Secure" if self.https() else ""

    def csrf_token(self):
        if not hasattr(self, "token"):
            current = self.cookie_value("csrf")
            self.token_is_new = not re.fullmatch(r"[A-Za-z0-9_\-]{20,64}", current)
            self.token = secrets.token_urlsafe(24) if self.token_is_new else current
        return self.token

    def csrf_ok(self, form):
        have = self.cookie_value("csrf")
        return bool(have) and hmac.compare_digest(form.get("csrf", "").encode(), have.encode())

    def read_form(self):
        length = min(int(self.headers.get("Content-Length") or 0), 10_000)
        raw = self.rfile.read(length).decode("utf-8", errors="replace")
        return {key: values[0] for key, values in parse_qs(raw).items()}

    def send_data(self, status, headers, data=b""):
        self.send_response(status)
        for name, value in headers:
            self.send_header(name, value)
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        if self.https():
            self.send_header("Strict-Transport-Security", "max-age=31536000")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def reply(self, text, status=200, cookies=()):
        token = self.csrf_token()
        headers = [("Content-Type", "text/html; charset=utf-8"), ("Cache-Control", "no-store")]
        headers += [("Set-Cookie", cookie) for cookie in cookies]
        if self.token_is_new:
            headers.append(("Set-Cookie", f"csrf={token}; Path=/; SameSite=Lax{self.secure_flag()}"))
        self.send_data(status, headers, text.replace("%%CSRF%%", token).encode("utf-8"))

    def send_json(self, payload, status=200):
        self.send_data(status, [("Content-Type", "application/json"), ("Cache-Control", "no-store")],
                       json.dumps(payload).encode("utf-8"))

    def redirect(self, where, cookies=()):
        self.send_data(303, [("Location", where)] + [("Set-Cookie", cookie) for cookie in cookies])

    def session_cookie(self, token):
        return f"session={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age={settings.SESSION_HOURS * 3600}{self.secure_flag()}"

    def current_session(self):
        return auth.session_for(self.cookie_value("session"))

    def current_profile(self):
        session = self.current_session()
        return auth.profile(session["user"]) if session else None

    def set_flash(self, text, kind="ok"):
        session = self.current_session()
        if session:
            session["flash"] = (text, kind)

    def take_flash(self):
        session = self.current_session()
        if session and session["flash"]:
            flash, session["flash"] = session["flash"], None
            return flash
        return None

    def require(self, level="access"):
        profile = self.current_profile()
        if not profile:
            self.redirect("/login")
            return None
        if level == "login":
            return profile
        if not profile["access"]:
            self.redirect("/activate")
            return None
        if level == "admin" and not profile["admin"]:
            self.reply(pages.message_page(profile, "Administrators only", "Your account cannot open this page."), 403)
            return None
        return profile

    def landing_path(self, username):
        profile = auth.profile(username)
        return "/dashboard" if profile and profile["access"] else "/activate"

    def do_GET(self):
        try:
            self.route_get()
        except Exception:
            traceback.print_exc()
            self.reply(pages.message_page(None, "Something went wrong", "The page could not be shown. Please try again."), 500)

    def do_POST(self):
        try:
            self.route_post()
        except Exception:
            traceback.print_exc()
            self.reply(pages.message_page(None, "Something went wrong", "That could not be completed. Please try again."), 500)

    def route_get(self):
        url = urlparse(self.path)
        path, query = url.path, parse_qs(url.query)
        first = lambda name: query.get(name, [""])[0]

        if path == "/healthz":
            return self.send_data(200, [("Content-Type", "text/plain"), ("Cache-Control", "no-store")], b"ok")
        if path.startswith("/assets/") and path[8:] in STATIC_FILES:
            with open(os.path.join(settings.HERE, "static", path[8:]), "rb") as f:
                return self.send_data(200, [("Content-Type", STATIC_FILES[path[8:]]), ("Cache-Control", "public, max-age=600")], f.read())

        if path == "/":
            return self.reply(pages.landing(self.current_profile(), len(self.sections)))
        if path == "/login":
            profile = self.current_profile()
            return self.redirect(self.landing_path(profile["name"])) if profile else self.reply(pages.login_page())
        if path == "/signup":
            return self.reply(pages.signup_page())
        if path == "/verify":
            item = auth.PENDING.get(first("id"))
            if not item:
                return self.redirect("/signup")
            flash, item["flash"] = item["flash"], None
            return self.reply(pages.verify_page(first("id"), auth.mask_email(item["email"]), flash))
        if path == "/forgot":
            return self.reply(pages.forgot_page())
        if path == "/reset":
            if not auth.reset_token_valid(first("token")):
                return self.reply(pages.reset_invalid_page(), 400)
            return self.reply(pages.reset_page(first("token")))
        if path == "/logout":
            return self.redirect("/")

        if path == "/activate":
            profile = self.require("login")
            if not profile:
                return
            if profile["access"]:
                return self.redirect("/dashboard")
            return self.reply(pages.activate_page(profile, self.take_flash()))
        if path == "/dashboard":
            profile = self.require()
            if profile:
                label = "Gemini" if ai.ai_ready() else ""
                self.reply(pages.dashboard_page(profile, self.sections, label, self.take_flash()))
            return
        if path == "/search":
            profile = self.require()
            if profile:
                question = first("q").strip()[:300]
                mode = "ai" if first("mode") == "ai" else "manual"
                hits = self.index.search(question) if question and mode == "manual" else []
                self.reply(pages.search_page(profile, question, mode, hits, search.enough_evidence(hits), ai.ai_ready()))
            return
        if path == "/manual":
            profile = self.require()
            if profile:
                self.reply(pages.manual_page(profile, self.sections))
            return
        if path == "/section":
            profile = self.require()
            if profile:
                number = first("n")
                self.reply(pages.section_page(profile, self.sections, int(number) if number.isdigit() else -1))
            return
        if path == "/admin":
            profile = self.require("admin")
            if profile:
                self.reply(pages.admin_page(profile, auth.technicians(), auth.accounts(), self.take_flash()))
            return
        if path == "/api/answer":
            return self.answer_api(first("mode"), first("q").strip()[:300])

        self.reply(pages.message_page(self.current_profile(), "Page not found", "That page does not exist."), 404)

    def answer_api(self, mode, question):
        profile = self.require()
        if not profile:
            return
        if not question or not ai.ai_ready():
            return self.send_json({"answer": "", "reason": ai.MESSAGES["ai_off"]})
        if auth.AI_USER.blocked(profile["name"].lower()):
            return self.send_json({"answer": "", "reason": "Too many questions. Wait a minute and try again."})
        auth.AI_USER.hit(profile["name"].lower())
        if mode == "ai":
            outcome = ai.general_answer(question)
            payload = {"answer": outcome["answer"], "reason": outcome["reason"], "sources": [], "flagged": []}
            kind = art.kind_for_text(question + " " + outcome["answer"], default=None) if outcome["answer"] else None
            if kind:
                ports = art.ports_mentioned(kind, question + " " + outcome["answer"])
                payload.update(figure=art.guide_figure(kind, ports), figure_title=art.FIGURE_TITLES[kind],
                               ports=art.port_labels(kind, ports))
            return self.send_json(payload)
        outcome = ai.answer_from_manual(question, self.index.search(question))
        return self.send_json({"answer": outcome["answer"], "reason": outcome["reason"], "sources": outcome["sources"],
                               "flagged": outcome["flagged"]})

    def route_post(self):
        path = urlparse(self.path).path
        form = self.read_form()
        if not self.csrf_ok(form):
            return self.reply(pages.message_page(None, "Please try again",
                                                 "That form had expired. Go back, reload the page and send it again."), 403)

        if path == "/login":
            user, why = auth.login(form.get("username", ""), form.get("password", ""), self.ip())
            if not user:
                return self.reply(pages.login_page((why, "error")))
            return self.redirect(self.landing_path(user), [self.session_cookie(auth.start_session(user))])

        if path == "/signup":
            username, email = form.get("username", "").strip(), form.get("email", "").strip()
            pending_id, message = auth.start_signup(username, email, form.get("password", ""), form.get("number", ""), self.ip())
            if not pending_id:
                return self.reply(pages.signup_page((message, "error"), username, email))
            return self.redirect(f"/verify?id={urllib.parse.quote(pending_id)}")

        if path == "/verify":
            pending_id = form.get("id", "")
            username, message = auth.finish_signup(pending_id, form.get("code", ""))
            if username:
                token = auth.start_session(username)
                auth.SESSIONS[token]["flash"] = ("Your account is ready.", "ok")
                return self.redirect("/dashboard", [self.session_cookie(token)])
            item = auth.PENDING.get(pending_id)
            if item:
                return self.reply(pages.verify_page(pending_id, auth.mask_email(item["email"]), (message, "error")))
            return self.reply(pages.signup_page((message, "error")))

        if path == "/resend":
            pending_id = form.get("id", "")
            sent, message = auth.resend_code(pending_id, self.ip())
            item = auth.PENDING.get(pending_id)
            if not item:
                return self.reply(pages.signup_page((message, "error")))
            return self.reply(pages.verify_page(pending_id, auth.mask_email(item["email"]), (message, "ok" if sent else "error")))

        if path == "/forgot":
            done, message = auth.request_reset(form.get("email", ""), self.ip())
            return self.reply(pages.forgot_page((message, "ok" if done else "error")))

        if path == "/reset":
            token = form.get("token", "")
            done, message = auth.reset_password(token, form.get("password", ""), form.get("confirm", ""))
            if done:
                return self.reply(pages.login_page((message, "ok")))
            if auth.reset_token_valid(token):
                return self.reply(pages.reset_page(token, (message, "error")))
            return self.reply(pages.reset_invalid_page(), 400)

        if path == "/logout":
            auth.end_session(self.cookie_value("session"))
            return self.redirect("/", ["session=; Path=/; Max-Age=0"])

        if path == "/activate":
            profile = self.require("login")
            if not profile:
                return
            done, message = auth.claim_number(profile["name"], form.get("number", ""))
            if done:
                self.set_flash(message, "ok")
                return self.redirect("/dashboard")
            return self.reply(pages.activate_page(profile, (message, "error")))

        if path == "/admin/generate":
            profile = self.require("admin")
            if not profile:
                return
            number = auth.create_technician(form.get("holder", ""), profile["name"])
            self.set_flash(f"Created {number}. Give it to the technician; it works once.", "ok")
            return self.redirect("/admin")

        if path == "/admin/delete":
            profile = self.require("admin")
            if not profile:
                return
            number = auth.clean_number(form.get("number", ""))
            removed = auth.delete_technician(number)
            self.set_flash(f"Removed {number}." if removed else "That number was not found.", "ok" if removed else "error")
            return self.redirect("/admin")

        self.reply(pages.message_page(self.current_profile(), "Page not found", "That page does not exist."), 404)


def local_address():
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        probe.close()


def main():
    if not os.path.exists(settings.MANUAL_FILE):
        sys.exit(f"Cannot find the manual at {settings.MANUAL_FILE}. Keep the 'manual' folder next to app.py.")
    Handler.sections = search.load_sections(settings.MANUAL_FILE)
    Handler.index = search.Index(Handler.sections)
    server = ThreadingHTTPServer(("0.0.0.0", settings.PORT), Handler)
    print(f"{settings.COMPANY_NAME}: loaded {len(Handler.sections)} manual sections")
    print(f"Open on this computer:  http://127.0.0.1:{settings.PORT}")
    print(f"Open from your network: http://{local_address()}:{settings.PORT}")
    print("Email:", "ON via Brevo" if mail.email_ready() and settings.BREVO_API_KEY else
          "ON via SMTP" if mail.email_ready() else "DEMO MODE (emails are printed here)")
    print("AI:", "Gemini" if ai.ai_ready() else "off (set GEMINI_API_KEY)")
    if settings.REMOTE_URL:
        try:
            store.remote("PING")
            print("Storage: online database, connected")
        except store.StorageError as problem:
            print(f"Storage: online database FAILED: {problem}")
    else:
        print(f"Storage: files in {settings.DATA_DIR}")
    print(f"Reset links point to: {settings.public_url()}")
    print(f"Administrator: {settings.ADMIN_USERNAME}")
    if settings.GENERATED_ADMIN_PASSWORD:
        print(f"  No ADMIN_PASSWORD was set, so this run uses: {settings.GENERATED_ADMIN_PASSWORD}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
