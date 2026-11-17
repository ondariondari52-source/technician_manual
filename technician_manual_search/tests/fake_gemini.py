import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LAST = {"prompt": ""}


def reply_for(prompt):
    LAST["prompt"] = prompt
    if "<manual_section" not in prompt:
        return ("General AI guidance (not from the manual).\n1. Check the link light and cable.\n"
                "2. Confirm the PoE switchport and the uplink port are up.\n3. Power cycle the device.\nSafety: switch off power before touching cables.")
    question = re.search(r"QUESTION: (.*)", prompt).group(1)
    first = re.search(r'<manual_section number="(\d+)"[^>]*>\n(.*?)\n</manual_section>', prompt, re.S)
    number, text = first.group(1), first.group(2)
    if "warranty" in question.lower():
        return "NOT IN MANUAL"
    if "BAD_CITATION" in question:
        return "Check the switchport. SOURCES: 99"
    if "UNGROUNDED" in question:
        return f"Banana submarine quantum zebra xylophone galaxy. SOURCES: {number}"
    if "LINKTEST" in question:
        return f"Check the switchport and visit http://evil.example/now for details. SOURCES: {number}"
    sentences = re.split(r"(?<=[.!?])\s+", " ".join(text.split()))
    return " ".join(sentences[:2]) + f"\nSOURCES: {number}"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        body = json.dumps(LAST).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
        if self.headers.get("x-goog-api-key") != "fake-key":
            body = b"{}"
            self.send_response(403)
        else:
            prompt = payload["contents"][0]["parts"][0]["text"]
            body = json.dumps({"candidates": [{"content": {"parts": [{"text": reply_for(prompt)}]}}]}).encode()
            self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def start(port):
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    import threading
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server
