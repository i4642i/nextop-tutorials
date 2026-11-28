"""Example splitter part "paragraphs": a text -> sections (at Markdown headings) -> paragraphs, a tree of two levels (plan
2026-11-26, phase 3; plan Q3: a worker cites one paragraph, fs://law/003#2.3). It is an example, not part of the
nextop wheel: where a text is cut depends on the texts a project keeps, so the platform gives the slot (the splitter
contract, the numbering and the spans) and each project keeps its own part. Copy this file to
<project>/parts/splitter/paragraphs.py and change the rules to your texts.

Use it on a data type (file_servers/<server>/types/<type>/type.json):  {"type": "text", "extensions": ["md", "txt"],
"splitter": "paragraphs"}, or copy it into the type folder as splitter.py

split(text, settings) -> [{"kind": "text", "title": <heading or "">, "text": <the section>,
                           "children": [{"kind": "text", "title": "", "text": <one paragraph>}, ...]}, ...]
  A section starts at every Markdown heading (# ... ######, a line of at most HEADING_CHARS characters: a news page
  stored as one line that starts with "#" is text); the text before the first heading is a section with no title. A paragraph is a block between blank lines; a heading line is the section's title, not a paragraph; a table
  (lines starting with "|") has no blank line inside, so it is one paragraph; a page mark (<!-- page 3 -->) goes with
  the paragraph after it. A section of one paragraph has no children (the section is the paragraph).
  A long block (more than LONG_BLOCK characters; a news page stored without blank lines is one block, phase 10) is cut
  into paragraphs of a few sentences: at sentence ends, a paragraph closes once it has PARAGRAPH_CHARS characters, and
  a short rest joins the paragraph before it. A sentence ends at . ! ? followed by a space and a new sentence (a capital,
  a digit, a quote, a letter without case such as Hangul) and at the Japanese and Chinese 。！？ (with any closing
  quote or bracket after them); never inside a number (3.5), after a single letter (U.S., J. Smith), after a word
  with a period inside it (e.g.) or after one of ABBREVIATIONS. A sentence is never cut, however long; a table is never
  cut. A fragment (a block of fewer than TINY_CHARS characters that ends no sentence, such as "(equation)" or a stray
  symbol) joins the paragraph before it in its section (the one after it when it comes first).
  Every text is a piece of the original word for word, so the platform finds it (span) and numbers it: #1 a section,
  #1.2 its second paragraph. settings are not used.
"""

from __future__ import annotations

import re

LONG_BLOCK = 800          # characters; a longer block is cut into paragraphs at sentence ends
PARAGRAPH_CHARS = 400     # characters; a cut paragraph closes at the first sentence end after this many
TINY_CHARS = 15           # characters; a shorter block that ends no sentence is no paragraph ("(equation)", "2")
HEADING_CHARS = 200       # characters; a longer line that starts like a heading ("# ...") is text, not a heading
# words a period follows without ending the sentence (lower case, without the period); change it to your texts
ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "prof", "st", "jr", "sr", "inc", "ltd", "co", "corp", "vs", "etc", "no",
                 "fig", "figs", "eq", "eqs", "sec", "approx", "al", "jan", "feb", "mar", "apr", "jun", "jul", "aug",
                 "sep", "sept", "oct", "nov", "dec"}

_HEADING = re.compile(r"^#{1,6}\s+\S")
_PAGE_MARK = re.compile(r"^\s*<!--\s*page\s+[^\s>]+\s*-->\s*$", re.I)
_BLANK = re.compile(r"\n[ \t\r]*(?:\n[ \t\r]*)+")
_CLOSE = "\"'’”)\\]」』）】"           # quotes and brackets that may close a sentence
# a sentence end: 。！？ (no space needed), or . ! ? and then white space; both with closing quotes or brackets
_END = re.compile(r"[。！？][" + _CLOSE + r"]*\s*|[.!?][" + _CLOSE + r"]*\s+")


def _blocks(text: str) -> list[tuple[int, int]]:
    """(start, end) of every block between blank lines, without the white space around it."""
    out, pos = [], 0
    for m in list(_BLANK.finditer(text)) + [None]:
        end = m.start() if m else len(text)
        piece = text[pos:end]
        if piece.strip():
            lead = len(piece) - len(piece.lstrip())
            out.append((pos + lead, pos + len(piece.rstrip())))
        pos = m.end() if m else end
    return out


def _ends_sentence(text: str, m: re.Match) -> bool:
    """Is the end _END found at m a sentence end? 。！？ always; . ! ? only before a new sentence and not after an
    abbreviation (see the module text)."""
    if text[m.start()] in "。！？":
        return True
    after = text[m.end():m.end() + 1]
    if not after or not (after.isupper() or after.isdigit() or after in "\"'“‘(「『[#*-"
                         or (after.isalpha() and not after.islower())):
        return False                    # a lower case word follows: no new sentence ("approx. five")
    if text[m.start()] != ".":
        return True
    before = text[max(0, m.start() - 40):m.start()].split()
    if not before or text[m.start() - 1].isspace():
        return True
    w = before[-1].lstrip("(\"'“‘[")
    letters = re.sub(r"[^A-Za-z]", "", w)
    if "." in w or (len(letters) == 1 and len(w) == 1) or w.lower() in ABBREVIATIONS:
        return False                    # U.S. / e.g. / J. Smith / Mr. Lee
    return True


def _sentences(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """(start, end) of the sentences of text[start:end], without the white space between them."""
    out, pos = [], start
    for m in _END.finditer(text, start, end):
        if m.end() >= end or not _ends_sentence(text, m):
            continue
        stop = m.end()
        while stop > pos and text[stop - 1].isspace():
            stop -= 1
        out.append((pos, stop))
        pos = m.end()
    if text[pos:end].strip():
        out.append((pos, end))
    return out


def _cut_long(text: str, start: int, end: int) -> list[tuple[int, int]]:
    """A long block cut into paragraphs of a few sentences (see LONG_BLOCK); a table or a short block stays whole."""
    if end - start <= LONG_BLOCK or text[start:end].lstrip().startswith("|"):
        return [(start, end)]
    out: list[tuple[int, int]] = []
    first = None
    for a, b in _sentences(text, start, end):
        first = a if first is None else first
        if b - first >= PARAGRAPH_CHARS:
            out.append((first, b))
            first = None
    if first is not None:
        if out and end - first < PARAGRAPH_CHARS // 2:
            out[-1] = (out[-1][0], end)          # a short rest joins the paragraph before it
        else:
            out.append((first, end))
    return out


def _tiny(text: str, a: int, b: int) -> bool:
    """A fragment, no paragraph: shorter than TINY_CHARS and not a sentence ("(equation)", "2"; "Copper stayed." is one)."""
    return b - a < TINY_CHARS and not text[a:b].rstrip(_CLOSE).endswith((".", "!", "?", "。", "！", "？"))


def _join_tiny(text: str, paragraphs: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """A fragment (_tiny) joins the paragraph before it (the first one joins the one after it)."""
    out: list[tuple[int, int]] = []
    for a, b in paragraphs:
        if out and (_tiny(text, a, b) or _tiny(text, *out[-1])):
            out[-1] = (out[-1][0], b)
        else:
            out.append((a, b))
    return out


def split(text: str, settings: dict | None = None) -> list[dict]:
    sections: list[dict] = []
    marks: int | None = None                  # start of page marks waiting for the paragraph after them
    for start, end in _blocks(text):
        block = text[start:end]
        first, _, rest = block.partition("\n")
        if _PAGE_MARK.match(block) and all(_PAGE_MARK.match(x) for x in block.splitlines()):
            marks = start if marks is None else marks
            continue
        at = start if marks is None else marks
        marks = None
        if _HEADING.match(first) and len(first) <= HEADING_CHARS:
            sections.append({"title": first.lstrip("#").strip(), "start": at, "end": end, "paragraphs": []})
            body = rest.strip()
            if body:
                b = start + len(first) + 1 + (len(rest) - len(rest.lstrip()))
                sections[-1]["paragraphs"].extend(_cut_long(text, b, end))
            continue
        if not sections:
            sections.append({"title": "", "start": at, "end": end, "paragraphs": []})
        sections[-1]["end"] = end
        pieces = _cut_long(text, start, end)
        sections[-1]["paragraphs"].extend([(at, pieces[0][1])] + pieces[1:])
    out = []
    for s in sections:
        node = {"kind": "text", "title": s["title"], "text": text[s["start"]:s["end"]]}
        paragraphs = _join_tiny(text, s["paragraphs"])
        if len(paragraphs) > 1:
            node["children"] = [{"kind": "text", "title": "", "text": text[a:b]} for a, b in paragraphs]
        out.append(node)
    return out
