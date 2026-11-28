"""Shared helpers: settings (.env), the font, the classification report, the one-page A4 summary and mail.

Everything here is plain program work (no model). Settings come from the environment or .env; nothing prints a key.
"""
import html
import io
import os
import pathlib
import re
import smtplib
import ssl
from email.message import EmailMessage

from nextop.adapters.openai_compat import read_env
from nextop.file_server import normalize_address

ROOT = pathlib.Path(__file__).resolve().parent.parent
MAX_COLS = 10        # a wider table cannot be drawn readably on a quarter of an A4 page
MAX_ROWS = 14        # more rows than this: the summary says which rows to show (the page then says "part of the table")
# Letters of Chinese, Japanese and Korean: a model sometimes slips them into English text
CJK = re.compile("[\u3040-\u30ff\u3131-\u318e\uac00-\ud7a3\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]")

# A TrueType font with the Latin letters and the usual symbols (· — “ ” √ × ≈ → α). PDF_FONT (and PDF_FONT_BOLD) in
# .env or the environment come first. No font file is shipped with this tutorial: the PDF is drawn with a font that
# is already on your computer.
FONT_CANDIDATES = [
    ("C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf"),                             # Windows: Segoe UI
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),   # Linux
    ("/usr/share/fonts/dejavu/DejaVuSans.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"),   # macOS
    ("/Library/Fonts/Arial.ttf", "/Library/Fonts/Arial Bold.ttf"),
]


def setting(name: str, default: str = "") -> str:
    env = ROOT / ".env"
    return os.environ.get(name) or (read_env(env) if env.exists() else {}).get(name) or default


def data_dir() -> pathlib.Path:
    """Where summaries/ is written (PDF_DATA_DIR lets tests use a private folder)."""
    return pathlib.Path(os.environ.get("PDF_DATA_DIR") or ROOT)


def find_font() -> tuple[str, str]:
    """(regular, bold) font file paths. Raises OSError saying what to do when no font is found."""
    own = setting("PDF_FONT")
    if own:
        if not pathlib.Path(own).is_file():
            raise OSError(f"PDF_FONT points to {own}, which is not a file")
        bold = setting("PDF_FONT_BOLD")
        return own, bold if bold and pathlib.Path(bold).is_file() else own
    for regular, bold in FONT_CANDIDATES:
        if pathlib.Path(regular).is_file():
            return regular, bold if pathlib.Path(bold).is_file() else regular
    raise OSError("no TrueType font found: install one (for example DejaVu Sans) or set PDF_FONT=<path of a .ttf file> in .env")


def register_fonts() -> tuple[str, str]:
    """Register the font with reportlab; returns the names (regular, bold)."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    regular, bold = find_font()
    if "Body" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Body", regular))
    if "Body-B" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("Body-B", bold))
    return "Body", "Body-B"


# ---- the classification report (program only) -----------------------------------------------------------------------

def build_report(rows: list[dict], file_name: str) -> dict:
    """Sort the parts of the one PDF the file server holds into text sections, tables and figures, in document order.

    rows: what a function with FILES_IN gets for the file server. The PDF's row has its part tree as data ("parts", in
    document order): the reader cut the PDF into sections, tables and figures (#1, #2, ...), and the paragraphs splitter
    cut each section into paragraphs (#3.1, #3.2, ...; a section of one paragraph is its own paragraph). A table part
    has its cells ("columns" and "rows"), a figure part its picture ("image", "width", "height"), and both their
    "caption" and "pages". The platform gives the page count (doc.pages).
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
    return report


def counted(n: int, word: str) -> str:
    """3 tables, 1 figure."""
    return f"{n} {word}{'' if n == 1 else 's'}"


def parts_line(counts: dict, sep: str = " · ") -> str:
    """44 text parts · 4 tables · 2 figures"""
    return sep.join([counted(counts["text"], "text part"), counted(counts["table"], "table"), counted(counts["figure"], "figure")])


def report_text(report: dict) -> str:
    """The classification report as the plain text of the mail body."""
    c = report["counts"]
    out = [f"PDF classification: {report['file']} ({report['pages']} pages)",
           parts_line(c), "", f"[Text] {c['text']}"]
    out += [f"  {n}. {s['title'] or '(no title)'} (page {s['pages']}) · {s['characters']} characters"
            for n, s in enumerate(report["sections"], 1)]
    out += ["", f"[Tables] {c['table']}"]
    for n, t in enumerate(report["tables"], 1):
        out.append(f"  {n}. {t['caption'] or t['label']} (page {t['pages']}) · {t['rows']} rows × {t['columns']} columns · "
                   f"columns: {' | '.join(t['header'])}")
    out += ["", f"[Figures] {c['figure']}"]
    for n, f in enumerate(report["figures"], 1):
        out.append(f"  {n}. {f['caption'] or f['label']} (page {f['pages']}) · {f['width']}×{f['height']} pixels")
    return "\n".join(out) + "\n"


# ---- the one-page A4 summary ----------------------------------------------------------------------------------------

def places(report: dict) -> dict:
    """{address: (kind, name, pages)} of every section, paragraph, table and figure, for the page numbers on the summary
    (read by the program)."""
    out = {}
    for s in report["sections"]:
        for a in [s["address"]] + s.get("paragraphs", []):
            out[a] = ("text", s["title"] or "text", s["pages"])
    for t in report["tables"]:
        out[t["address"]] = ("table", t["caption"] or t["label"], t["pages"])
    for f in report["figures"]:
        out[f["address"]] = ("figure", f["caption"] or f["label"], f["pages"])
    return out


def chosen_rows(table: dict, wanted: list | None) -> list[int]:
    """The 1-based row numbers drawn for a table: the header row (1) first, then the rows the summary chose (all when it chose none)."""
    n = table["rows"]
    picked = [r for r in (wanted or []) if isinstance(r, int) and 1 <= r <= n]
    if not picked:
        return list(range(1, n + 1))
    return [1] + sorted(set(picked) - {1})


def render_summary(summary: dict, report: dict, today: str) -> bytes:
    """The summary as a PDF (A4, portrait): title, key points, the chosen tables and figures themselves, conclusion.

    Tables are drawn from the cells and figures from the picture the file server cut out (both are in the report, put
    there by classify); the model only says which ones and which rows. Page count and overflow are measured by
    page_count() and overflow_chars().
    """
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import HRFlowable, Image, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    regular, bold = register_fonts()
    where = places(report)
    tables = {t["address"]: t for t in report["tables"]}
    figures = {f["address"]: f for f in report["figures"]}
    width = A4[0] - 36 * mm - 12            # the page frame keeps 6 points free on each side

    def style(name, size, font=regular, color=colors.black, lead=None, left=0, after=0, before=0):
        return ParagraphStyle(name, fontName=font, fontSize=size, leading=lead or size * 1.4, textColor=color, alignment=TA_LEFT,
                              leftIndent=left, spaceAfter=after, spaceBefore=before)

    title_s, meta_s = style("t", 17, bold, lead=23, after=3), style("m", 8.5, color=colors.HexColor("#666666"), after=4)
    head_s = style("h", 11, bold, colors.HexColor("#1f3a68"), before=8, after=3)
    body_s, quote_s = style("b", 9.5, after=1), style("q", 8, color=colors.HexColor("#555555"), left=10, after=4)
    cap_s = style("c", 8.5, color=colors.HexColor("#333333"), before=3, after=3)
    e = html.escape

    def cite(address, quote):
        kind, name, pages = where.get(normalize_address(address), ("text", "the whole document", ""))
        return Paragraph(f"Source: page {e(pages)} · {e(name)} — “{e(quote)}”", quote_s)

    def draw_table(item):
        t = tables[normalize_address(item["source"])]
        rows = chosen_rows(t, item.get("rows"))
        size = 8.5 if t["columns"] <= 4 else 7.5 if t["columns"] <= 6 else 6.5 if t["columns"] <= 8 else 5.5
        cell_s = style(f"cell{size}", size, lead=size * 1.25)
        head_cell = style(f"head{size}", size, bold, lead=size * 1.25)
        data = [[Paragraph(e(c), head_cell if r == 1 else cell_s) for c in t["cells"][r - 1]] for r in rows]
        n_cols = max(len(r) for r in data)
        data = [r + [""] * (n_cols - len(r)) for r in data]
        grid = Table(data, colWidths=[width / n_cols] * n_cols, hAlign="LEFT")
        grid.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#777777")),
                                  ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf5")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                  ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
                                  ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]))
        part = f" · part of the table: {len(rows)} of {t['rows']} rows" if len(rows) < t["rows"] else ""
        return KeepTogether([Paragraph(f"<b>{e(t['caption'] or t['label'])}</b> (page {e(t['pages'])}{part}): {e(item['line'])}", cap_s), grid, Spacer(1, 4)])

    def draw_figure(item):
        f = figures[normalize_address(item["figure"])]
        w, h = f["width"] or 400, f["height"] or 300
        shown_w = min(width * 0.7, 62 * mm * w / h)
        picture = Image(f["image"], width=shown_w, height=shown_w * h / w, hAlign="LEFT")
        return KeepTogether([picture, Paragraph(f"<b>{e(f['caption'] or f['label'])}</b> (page {e(f['pages'])}): {e(item['line'])}", cap_s), Spacer(1, 4)])

    c = report["counts"]
    flow = [Paragraph(e(summary["title"]), title_s),
            Paragraph(e(f"Source: {report['file']} · {counted(report['pages'], 'page')} · {parts_line(c)} · summarized {today}"), meta_s),
            HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#1f3a68"), spaceAfter=2),
            Paragraph("Key points", head_s)]
    for n, k in enumerate(summary["key_points"], 1):
        flow += [Paragraph(f"{n}. {e(k['point'])}", body_s), cite(k["source"], k["quote"])]
    if summary["tables"]:
        flow.append(Paragraph("Tables", head_s))
        flow += [draw_table(t) for t in summary["tables"]]
    if summary["figures"]:
        flow.append(Paragraph("Figures", head_s))
        flow += [draw_figure(f) for f in summary["figures"]]
    flow += [Paragraph("Conclusion", head_s), Paragraph(e(summary["conclusion"]), body_s), Spacer(1, 2)]
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=16 * mm, bottomMargin=16 * mm,
                      title=summary["title"]).build(flow)
    return buf.getvalue()


def page_count(pdf: bytes) -> int:
    import pypdfium2
    with pypdfium2.PdfDocument(pdf) as doc:
        return len(doc)


def overflow_chars(pdf: bytes) -> int:
    """Characters that did not fit on the first page."""
    import pypdfium2
    with pypdfium2.PdfDocument(pdf) as doc:
        return sum(len(doc[i].get_textpage().get_text_range().strip()) for i in range(1, len(doc)))


def cjk_errors(where: str, text: str) -> list[str]:
    found = "".join(dict.fromkeys(CJK.findall(text)))
    return [f'{where} "{text[:40]}..." has Chinese, Japanese or Korean letters ({found}); write it again in English only'] if found else []


# ---- mail -------------------------------------------------------------------------------------------------------

def recipients() -> str:
    """Test mode (MAIL_TEST_MODE=1): everything goes to OFFICE_EMAIL. Otherwise to MAIL_TO."""
    if setting("MAIL_TEST_MODE", "1") == "1":
        return setting("OFFICE_EMAIL")
    return setting("MAIL_TO")


MAIL_KEYS = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS")


def mail_problems() -> list[str]:
    """What is missing for sending mail, one sentence per gap; an empty list means mail can be sent."""
    out = [f"{k} is empty. Put {k}=... in .env." for k in MAIL_KEYS if not setting(k)]
    if not recipients():
        name = "OFFICE_EMAIL" if setting("MAIL_TEST_MODE", "1") == "1" else "MAIL_TO"
        out.append(f"There is no recipient. Put {name}=... in .env.")
    return out


def send_mail(to: str, subject: str, body: str, attachments: list[tuple[str, bytes]] | None = None) -> tuple[bool, str]:
    """Send one mail with a plain text body and PDF attachments [(file name, bytes)]. Returns (ok, note)."""
    cfg = {k: setting(k) for k in MAIL_KEYS}
    problems = mail_problems()
    if not to or problems:
        return False, "Mail is not set up: " + " ".join(problems)
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["SMTP_USER"], to
    msg.set_content(body, cte="base64")                  # base64: safe for any mail server
    for name, data in attachments or []:
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=name)    # a non-ASCII file name is encoded for you
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
        return False, f"SMTP server {cfg['SMTP_HOST']}:{cfg['SMTP_PORT']} could not send the mail ({type(e).__name__}: {e})"
