import re

INVISIBLE = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff\u00ad"), None)
HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
HTML_TAG = re.compile(r"<[^>]+>")
LINK = re.compile(r"https?://\S+|www\.\S+", re.I)
EMAIL_ADDRESS = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

INJECTION_PATTERNS = [
    r"ignore (all |any |the |your )?(previous|prior|above|earlier|other)",
    r"disregard (all |any |the |your )?(previous|prior|above|earlier|other)",
    r"forget (everything|all|what|the)",
    r"you are (now|actually)",
    r"new (instructions?|rules?|task)",
    r"system (prompt|message|instruction)",
    r"(reveal|show|print|repeat) (the |your )?(prompt|instructions|api key|password|secret)",
    r"(always|only|just|instead) (answer|respond|reply|say|output|write)",
    r"(answer|respond to|reply to) (every|all|each|any) (question|query|request)",
    r"do not (cite|mention|reveal|follow|use) ",
    r"\boverride\b",
    r"jailbreak",
    r"sources:",
    r"not in manual",
    r"</?manual_section",
    r"\bas an ai\b",
    r"important:?\s*(instruction|note to (the )?(ai|assistant|model))",
]
REMOVED_NOTE = "[removed: instruction-like text]"


def strip_hidden(text):
    text = HTML_COMMENT.sub(" ", text)
    text = text.translate(INVISIBLE)
    return HTML_TAG.sub(" ", text)


def looks_like_instruction(sentence):
    lowered = sentence.lower()
    if LINK.search(sentence) or EMAIL_ADDRESS.search(sentence):
        return True
    return any(re.search(pattern, lowered) for pattern in INJECTION_PATTERNS)


def neutralize(text):
    removed = []
    paragraphs = []
    for paragraph in re.split(r"\n\s*\n", text):
        flat = " ".join(paragraph.split())
        sentences = re.split(r"(?<=[.!?])\s+", flat)
        if any(looks_like_instruction(sentence) for sentence in sentences):
            removed.append(flat)
            paragraphs.append(REMOVED_NOTE)
        else:
            paragraphs.append(flat)
    return "\n\n".join(paragraphs), removed
