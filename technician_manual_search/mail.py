import html
import smtplib
import urllib.error
from email.message import EmailMessage

import settings
from net import post_json


def email_ready():
    return bool(settings.EMAIL_ADDRESS and (settings.BREVO_API_KEY or settings.EMAIL_PASSWORD))


def send_email(to, subject, text, page_html):
    if not email_ready():
        print(f"\n[DEMO MODE] Email to {to}\nSubject: {subject}\n{text}\n")
        return True, "Demo mode: the email was printed in the terminal running the app."
    try:
        if settings.BREVO_API_KEY:
            post_json(
                settings.BREVO_API_URL,
                {"sender": {"name": settings.COMPANY_NAME, "email": settings.EMAIL_ADDRESS}, "to": [{"email": to}],
                 "subject": subject, "htmlContent": page_html, "textContent": text},
                {"api-key": settings.BREVO_API_KEY, "accept": "application/json"},
                timeout=20,
            )
        else:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = f"{settings.COMPANY_NAME} <{settings.EMAIL_ADDRESS}>"
            message["To"] = to
            message.set_content(text)
            message.add_alternative(page_html, subtype="html")
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=20) as server:
                server.starttls()
                server.login(settings.EMAIL_ADDRESS, settings.EMAIL_PASSWORD)
                server.send_message(message)
    except urllib.error.HTTPError as problem:
        print(f"[EMAIL ERROR] HTTP {problem.code}: {problem.read()[:300]!r}")
        return False, "The email service refused the message."
    except Exception as problem:
        print(f"[EMAIL ERROR] {problem}")
        return False, "The email could not be sent. Try again shortly."
    return True, "Email sent."


def wrap(body):
    return ("<div style='font-family:Segoe UI,Arial,sans-serif;max-width:440px'>"
            f"<h2 style='margin:0 0 12px'>{html.escape(settings.COMPANY_NAME)}</h2>{body}</div>")


def send_code_email(to, code):
    text = (f"Your verification code is {code}\n\nIt expires in {settings.CODE_MINUTES} minutes. "
            f"If you did not create an account with {settings.COMPANY_NAME}, ignore this email.")
    page_html = wrap(f"<p>Your verification code is</p>"
                     f"<p style='font-size:32px;font-weight:700;letter-spacing:8px;margin:8px 0'>{code}</p>"
                     f"<p>It expires in {settings.CODE_MINUTES} minutes. If you did not create an account, ignore this email.</p>")
    return send_email(to, f"{code} is your {settings.COMPANY_NAME} verification code", text, page_html)


def send_reset_email(to, link):
    text = (f"Someone asked to reset the password for your {settings.COMPANY_NAME} account.\n\n"
            f"Open this link within {settings.RESET_MINUTES} minutes to choose a new password:\n{link}\n\n"
            "If you did not ask for this, ignore this email. Your password stays the same.")
    page_html = wrap(f"<p>Someone asked to reset the password for your account.</p>"
                     f"<p><a href='{html.escape(link)}' style='background:#0B5C8E;color:#fff;padding:10px 18px;border-radius:6px;text-decoration:none'>Choose a new password</a></p>"
                     f"<p>The link works for {settings.RESET_MINUTES} minutes. If you did not ask for this, ignore this email.</p>")
    return send_email(to, f"Reset your {settings.COMPANY_NAME} password", text, page_html)
