import os
import secrets

HERE = os.path.dirname(os.path.abspath(__file__))


def read_env_file(path):
    values = {}
    if os.path.exists(path):
        with open(path, "rb") as f:
            text = f.read().decode("utf-8-sig", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, _, value = line.partition("=")
                values[name.strip()] = value.strip().strip('"').strip("'")
    return values


for name, value in read_env_file(os.path.join(HERE, ".env")).items():
    if value and not os.environ.get(name):
        os.environ[name] = value


def get(name, default=""):
    return os.environ.get(name, default).strip()


COMPANY_NAME = get("COMPANY_NAME", "Software Engineering EEE 2026")
PRODUCT_NAME = "Technician Manual Search"

ADMIN_USERNAME = get("ADMIN_USERNAME", "Johnson")
ADMIN_PASSWORD = get("ADMIN_PASSWORD")
GENERATED_ADMIN_PASSWORD = ""
if not ADMIN_PASSWORD:
    GENERATED_ADMIN_PASSWORD = secrets.token_urlsafe(9)
    ADMIN_PASSWORD = GENERATED_ADMIN_PASSWORD

GEMINI_API_KEY = get("GEMINI_API_KEY")
GEMINI_MODEL = get("GEMINI_MODEL")
GEMINI_BASE_URL = get("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/models")

EMAIL_ADDRESS = get("EMAIL_ADDRESS")
EMAIL_PASSWORD = get("EMAIL_PASSWORD").replace(" ", "")
EMAIL_HOST = get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(get("EMAIL_PORT", "587"))
BREVO_API_KEY = get("BREVO_API_KEY")
BREVO_API_URL = get("BREVO_API_URL", "https://api.brevo.com/v3/smtp/email")

REMOTE_URL = get("UPSTASH_REDIS_REST_URL").rstrip("/")
REMOTE_TOKEN = get("UPSTASH_REDIS_REST_TOKEN")
if not (REMOTE_URL and REMOTE_TOKEN):
    REMOTE_URL = ""

PORT = int(get("PORT", "8000"))
PUBLIC_URL = get("PUBLIC_URL").rstrip("/")
DATA_DIR = get("DATA_DIR", HERE)
MANUAL_FILE = get("MANUAL_FILE", os.path.join(HERE, "manual", "technician_manual_sanitized.md"))

CODE_MINUTES = 10
MAX_CODE_TRIES = 5
RESEND_SECONDS = 60
RESET_MINUTES = 30
SESSION_HOURS = 8
MIN_PASSWORD_LENGTH = 8
MIN_COVERAGE = 0.4


def public_url():
    return PUBLIC_URL or f"http://127.0.0.1:{PORT}"
