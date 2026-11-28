"""Shared helpers: settings (.env), Korean fonts, the classification report, text checks and mail.

Everything here is plain program work (no model). Settings come from the environment or .env; nothing prints a key.
"""
import os
import pathlib
import re
import smtplib
import ssl
from email.message import EmailMessage

from nextop.adapters.openai_compat import read_env

ROOT = pathlib.Path(__file__).resolve().parent.parent
HAN = re.compile("[㐀-䶿一-鿿]")                     # Chinese characters: a model sometimes slips them into Korean text
# "용어(term)" or "term(용어)": a word written twice, in Korean and in English, inside parentheses
DOUBLE_TERM = re.compile(r"[가-힣]\s*\(\s*[A-Za-z]|[A-Za-z]\s*\(\s*[가-힣]")

# A Korean TrueType font. KOREAN_FONT (and KOREAN_FONT_BOLD) in .env or the environment come first. No font file is
# shipped with this tutorial: the slides are drawn with a font that is already on your computer.
FONT_CANDIDATES = [
    ("C:/Windows/Fonts/malgun.ttf", "C:/Windows/Fonts/malgunbd.ttf"),                              # Windows: Malgun Gothic
    ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"),   # Linux
    ("/Library/Fonts/NanumGothic.ttf", "/Library/Fonts/NanumGothicBold.ttf"),                      # macOS, if installed
    ("/usr/share/fonts/nanum/NanumGothic.ttf", "/usr/share/fonts/nanum/NanumGothicBold.ttf"),
]
# A Korean serif font for the academic theme's titles; when none is found that theme uses the sans font
SERIF_CANDIDATES = ["C:/Windows/Fonts/batang.ttc", "/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf",
                    "/Library/Fonts/NanumMyeongjo.ttf", "/usr/share/fonts/nanum/NanumMyeongjo.ttf"]


def setting(name: str, default: str = "") -> str:
    env = ROOT / ".env"
    return os.environ.get(name) or (read_env(env) if env.exists() else {}).get(name) or default


def data_dir() -> pathlib.Path:
    """Where output/ is written (DECK_DATA_DIR lets tests use a private folder)."""
    return pathlib.Path(os.environ.get("DECK_DATA_DIR") or ROOT)


def find_font() -> tuple[str, str]:
    """(regular, bold) font file paths. Raises OSError saying what to do when no Korean font is found."""
    own = setting("KOREAN_FONT")
    if own:
        if not pathlib.Path(own).is_file():
            raise OSError(f"KOREAN_FONT points to {own}, which is not a file")
        bold = setting("KOREAN_FONT_BOLD")
        return own, bold if bold and pathlib.Path(bold).is_file() else own
    for regular, bold in FONT_CANDIDATES:
        if pathlib.Path(regular).is_file():
            return regular, bold if pathlib.Path(bold).is_file() else regular
    raise OSError("no Korean TrueType font found: install one (for example NanumGothic) or set KOREAN_FONT=<path of a .ttf file> in .env")


def find_serif_font() -> str | None:
    return next((f for f in SERIF_CANDIDATES if pathlib.Path(f).is_file()), None)


def register_fonts() -> tuple[str, str]:
    """Register the Korean font with reportlab (used only by make_sample_pdf.py); returns the names (regular, bold)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    regular, bold = find_font()
    if "KR" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KR", regular))
    if "KR-B" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("KR-B", bold))
    return "KR", "KR-B"


# ---- the classification report (program only) -----------------------------------------------------------------------

def build_report(rows: list[dict], file_name: str) -> dict:
    """Sort the parts of the one PDF the file server holds into text sections, tables and figures, in document order.

    rows: what a function with FILES_IN gets for the file server. The PDF's row has its part tree as data ("parts", in
    document order): the reader cut the PDF into sections, tables and figures (#1, #2, ...), and the paragraphs splitter
    cut each section into paragraphs (#3.1, #3.2, ...; a section of one paragraph is its own paragraph). A table part
    has its cells ("columns" and "rows"), a figure part its picture ("image", "width", "height"), and both their
    "caption" and "pages". The platform gives the page count (doc.pages).

    Two facts for the planner, found here by the program:
    - sections[].pieces: a section that runs over a page break, or around a table or figure, is cut into one part per
      piece; every piece lists all the pieces of its section, in order (a section of one piece has no "pieces"). A
      slide that names one piece gets the whole section (_deck.whole_sections).
    - tables[].text_parts, figures[].text_parts: the text parts that talk about the table or figure: those whose
      paragraphs name its label ("Table 1", "그림 1"), or, when no paragraph names it, the section it stands in. The
      planner's check asks a table or figure slide to rest on one of them.
    """
    doc = next((r for r in rows if r.get("parts")), None)
    if doc is None:
        raise ValueError("the file server holds no document with parts")
    parts = doc["parts"]
    report = {"file": file_name, "pages": doc["doc"].get("pages", 0), "document": doc["address"],
              "counts": {"text": 0, "table": 0, "figure": 0}, "sections": [], "tables": [], "figures": []}
    for p in parts:
        kind, address = p["kind"], p["address"]
        if "." in address.split("#", 1)[1] or kind not in report["counts"]:
            continue                                   # a paragraph: listed under its section below
        report["counts"][kind] += 1
        page, caption = str(p.get("pages") or ""), p.get("caption", "")
        if kind == "text":
            paragraphs = [q for q in parts if q["leaf"] and q["kind"] == "text"
                          and (q["address"] == address or q["address"].startswith(address + "."))]
            report["sections"].append({"address": address, "title": p["title"], "pages": page,
                                       "characters": sum(len(q.get("text", "").strip()) for q in paragraphs),
                                       "paragraphs": [q["address"] for q in paragraphs]})
        elif kind == "table":
            cells = ([list(p["columns"])] if p.get("columns") else []) + [list(r) for r in p.get("rows") or []]
            report["tables"].append({"address": address, "label": p["title"], "caption": caption, "pages": page,
                                     "rows": len(cells), "columns": max((len(r) for r in cells), default=0),
                                     "header": cells[0] if cells else [],
                                     "cells": cells})                      # the cells, drawn by the program, never retyped
        else:
            report["figures"].append({"address": address, "label": p["title"], "caption": caption, "pages": page,
                                      "width": p.get("width", 0), "height": p.get("height", 0), "image": p.get("image", "")})
    _mark_pieces(report["sections"])
    texts = {q["address"]: q.get("text", "") for q in parts if q["leaf"] and q["kind"] == "text"}
    order = [p["address"] for p in parts if "." not in p["address"].split("#", 1)[1]]
    for item in report["tables"] + report["figures"]:
        item["text_parts"] = text_parts_of(item, report["sections"], texts, order)
    return report


LABEL = re.compile(r"\s*((?:Table|Figure|Fig\.|표|그림)\s*\d+)", re.I)


def _mark_pieces(sections: list[dict]):
    """Give every piece of a section cut into several parts the list of all its pieces (neighbours with one title)."""
    run: list[dict] = []
    for s in sections + [{"title": None}]:
        if run and (s["title"] != run[0]["title"] or not s["title"]):
            if len(run) > 1:
                for r in run:
                    r["pieces"] = [x["address"] for x in run]
            run = []
        if s["title"]:
            run.append(s)


def _is_caption(text: str, item: dict) -> bool:
    """A paragraph that is the caption itself (some PDFs repeat it in the text) does not talk about the item."""
    head = (item["caption"] or item["label"] or "").strip()[:30]
    return bool(head) and text.strip().startswith(head)


def text_parts_of(item: dict, sections: list[dict], texts: dict, order: list[str]) -> list[str]:
    """The text parts that talk about a table or figure: those with a paragraph naming its label (not the caption
    itself), else the section part it stands in (the last text part before it, or the first after it)."""
    m = LABEL.match(item["label"] or item["caption"] or "")
    if m:
        name = re.compile(r"(?<![\w])" + r"\s*".join(map(re.escape, m.group(1).split())) + r"(?!\d)", re.I)
        named = [s["address"] for s in sections
                 if any(name.search(texts.get(a, "")) and not _is_caption(texts.get(a, ""), item) for a in s["paragraphs"])]
        if named:
            return named
    where = order.index(item["address"]) if item["address"] in order else len(order)
    ours = {s["address"] for s in sections}
    before = [a for a in order[:where] if a in ours]
    after = [a for a in order[where:] if a in ours]
    return before[-1:] or after[:1]


# ---- text checks ----------------------------------------------------------------------------------------------------

def han_errors(where: str, text: str) -> list[str]:
    found = "".join(dict.fromkeys(HAN.findall(text)))
    return [f'{where} "{text[:40]}" has Chinese characters ({found}); write it again in Korean only'] if found else []


def double_term_errors(where: str, text: str) -> list[str]:
    m = DOUBLE_TERM.search(text)
    if not m:
        return []
    around = text[max(0, m.start() - 12):m.end() + 12]
    return [f'{where} writes a term twice with parentheses ("...{around}..."): a slide shows a term once. '
            "Write it in Korean or in English, not both"]


# ---- mail -------------------------------------------------------------------------------------------------------

def recipients() -> str:
    """Test mode (MAIL_TEST_MODE=1): everything goes to OFFICE_EMAIL. Otherwise to MAIL_TO."""
    if setting("MAIL_TEST_MODE", "1") == "1":
        return setting("OFFICE_EMAIL")
    return setting("MAIL_TO")


MAIL_KEYS = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS")


def mail_problems() -> list[str]:
    """What is missing for sending mail, one sentence per gap; an empty list means mail can be sent."""
    out = [f"{k} 가 비어 있습니다. .env 에 {k}=... 를 넣어 주세요." for k in MAIL_KEYS if not setting(k)]
    if not recipients():
        name = "OFFICE_EMAIL" if setting("MAIL_TEST_MODE", "1") == "1" else "MAIL_TO"
        out.append(f"받는 사람이 없습니다. .env 에 {name}=... 를 넣어 주세요.")
    return out


def send_mail(to: str, subject: str, body: str, attachments: list[tuple[str, str, bytes]] | None = None) -> tuple[bool, str]:
    """Send one mail with a plain text body and attachments [(file name, mime type, bytes)]. Returns (ok, note)."""
    cfg = {k: setting(k) for k in MAIL_KEYS}
    problems = mail_problems()
    if not to or problems:
        return False, "메일 설정이 비어 있습니다: " + " ".join(problems)
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["SMTP_USER"], to
    msg.set_content(body, cte="base64")                  # base64: safe for any mail server
    for name, mime, data in attachments or []:
        maintype, subtype = mime.split("/", 1)
        msg.add_attachment(data, maintype=maintype, subtype=subtype, filename=name)   # a Korean file name is encoded for you
    try:
        port = int(cfg["SMTP_PORT"])
        if port == 465:
            smtp = smtplib.SMTP_SSL(cfg["SMTP_HOST"], port, context=ssl.create_default_context(), timeout=30)
        else:
            smtp = smtplib.SMTP(cfg["SMTP_HOST"], port, timeout=30)
            if port == 587:                       # any other port: no encryption (a local test server only)
                smtp.starttls(context=ssl.create_default_context())
        with smtp:
            smtp.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
            smtp.send_message(msg)
        return True, "sent"
    except (OSError, smtplib.SMTPException, ValueError) as e:
        return False, f"SMTP 서버 {cfg['SMTP_HOST']}:{cfg['SMTP_PORT']} 에서 메일을 보내지 못했습니다 ({type(e).__name__}: {e})"
