import math
import re
from collections import Counter

import safety
import settings

STOPWORDS = set("""a an the this that these those is are was were be been in on at for to of from by as with and or but if
then so do does did how what when where who which why i you we they he she it my your our their can should would could about
there here also just""".split())

TITLE_WEIGHT = 3
K1 = 1.5
B = 0.75


def stem(word):
    if len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 4 and re.search(r"(ch|sh|x|z|ss)es$", word):
        word = word[:-2]
    elif len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        word = word[:-1]
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 4 and word.endswith("ed"):
        word = word[:-2]
    if len(word) > 3 and word.endswith("e"):
        word = word[:-1]
    return word


def tokenize(text):
    return [stem(word) for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOPWORDS]


def load_sections(path):
    with open(path, encoding="utf-8") as f:
        text = safety.strip_hidden(f.read())
    headings = list(re.finditer(r"^## Section (\d+): (.+)$", text, re.MULTILINE))
    sections = []
    for i, heading in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(text)
        sections.append({
            "number": int(heading.group(1)),
            "title": heading.group(2).strip(),
            "text": text[heading.end():end].strip(),
        })
    return sections


def reference(section):
    return f"Section {section['number']}"


class Index:
    def __init__(self, sections):
        self.sections = sections
        self.counts = []
        self.lengths = []
        for section in sections:
            words = tokenize(section["title"]) * TITLE_WEIGHT + tokenize(section["text"])
            self.counts.append(Counter(words))
            self.lengths.append(len(words))
        self.average_length = sum(self.lengths) / max(1, len(sections))
        self.document_frequency = Counter()
        for counts in self.counts:
            self.document_frequency.update(counts.keys())

    def idf(self, term):
        n = len(self.sections)
        df = self.document_frequency.get(term, 0)
        return math.log(1 + (n - df + 0.5) / (df + 0.5))

    def score(self, position, terms):
        total = 0.0
        counts = self.counts[position]
        for term in terms:
            frequency = counts.get(term, 0)
            if frequency:
                length_norm = 1 - B + B * self.lengths[position] / self.average_length
                total += self.idf(term) * frequency * (K1 + 1) / (frequency + K1 * length_norm)
        return total

    def search(self, question, top=3):
        terms = list(dict.fromkeys(tokenize(question)))
        if not terms:
            return []
        hits = []
        for position, section in enumerate(self.sections):
            score = self.score(position, terms)
            if score > 0:
                matched = [t for t in terms if t in self.counts[position]]
                hits.append({"section": section, "score": score, "matched": matched,
                             "coverage": len(matched) / len(terms)})
        hits.sort(key=lambda hit: hit["score"], reverse=True)
        return hits[:top]


def enough_evidence(hits):
    return bool(hits) and hits[0]["coverage"] >= settings.MIN_COVERAGE
