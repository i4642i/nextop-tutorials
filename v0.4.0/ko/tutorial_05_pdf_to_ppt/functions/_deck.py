"""The slide deck: themes, the 8 layouts, text measuring, and where every box goes (program only, no model).

One set of boxes drives everything: the .pptx writer (_pptx.py), the PNG previews (_preview.py) and the fit check
(checks.py of the writer). A box is a plain dict in points on a 960 x 540 slide (16:9, 13.333 x 7.5 inches):

  {"kind": "rect" | "oval", x, y, w, h, "fill", "radius"}
  {"kind": "text", x, y, w, h, "text", "lines", "size", "bold", "font" ("title" | "body"), "color", "align", "anchor", "lh"}
  {"kind": "image", x, y, w, h, "path"}
  {"kind": "table", x, y, w, h, "widths", "rows": [{"cells", "lines", "h", "header"}], "size", "lh", ...colours}

Text is wrapped here, by measuring every word with the theme's font, so the previews show the same lines the fit
check counted. Font sizes are fixed (no shrinking): text that does not fit is reported, never cut.
"""
import functools
import math
import pathlib
import re

from nextop.file_server import normalize_address

from functions._common import find_font, find_serif_font

SLIDE_W, SLIDE_H = 960, 540               # points
M = 56                                    # side margin
TOP, BOTTOM = 104, 482                    # content area of a content slide
FIT = 0.94                                # wrap at 94% of a box: PowerPoint and LibreOffice measure a little differently
MAX_TABLE_COLS = 7
MAX_TABLE_ROWS = 8                        # header row included
MAX_TABLE_HEIGHT = 200                    # points; the rest of the slide is for the caption and the bullets

# The 8 layouts. bullets: how many the writer gives (columns: per column). lines: lines one bullet may take.
LAYOUTS = {
    "cover":      {"name": "표지", "bullets": (0, 0)},
    "agenda":     {"name": "목차", "bullets": (0, 0)},
    "section":    {"name": "구역 표지", "bullets": (0, 0)},
    "bullets":    {"name": "글머리표", "bullets": (3, 5), "style": "bullet"},
    "figure":     {"name": "그림과 설명", "bullets": (2, 3), "style": "side_bullet", "figure": True},
    "table":      {"name": "표와 설명", "bullets": (2, 3), "style": "table_bullet", "table": True},
    "comparison": {"name": "두 단 비교", "bullets": (2, 3), "style": "col_bullet", "columns": 2},
    "closing":    {"name": "핵심 정리", "bullets": (3, 5), "style": "takeaway"},
}
LAYOUT_ORDER = list(LAYOUTS)
CONTENT = ("bullets", "figure", "table", "comparison", "closing")       # slides with bullets that cite the document

# Text styles: size (pt), bold, font role, the most lines the text may take
STYLES = {
    "title":        {"size": 28, "bold": True, "font": "title", "lines": 1},
    "cover_title":  {"size": 44, "bold": True, "font": "title", "lines": 3},
    "cover_sub":    {"size": 22, "bold": False, "font": "body", "lines": 2},
    "cover_label":  {"size": 15, "bold": True, "font": "body", "lines": 1},
    "meta":         {"size": 12, "bold": False, "font": "body", "lines": 2},
    "section_no":   {"size": 72, "bold": True, "font": "title", "lines": 1},
    "section_title": {"size": 36, "bold": True, "font": "title", "lines": 2},
    "agenda_no":    {"size": 28, "bold": True, "font": "title", "lines": 1},
    "agenda_item":  {"size": 24, "bold": False, "font": "body", "lines": 1},
    "bullet":       {"size": 22, "bold": False, "font": "body", "lines": 2},
    "side_bullet":  {"size": 18, "bold": False, "font": "body", "lines": 3},
    "table_bullet": {"size": 18, "bold": False, "font": "body", "lines": 2},
    "col_heading":  {"size": 22, "bold": True, "font": "body", "lines": 1},
    "col_bullet":   {"size": 18, "bold": False, "font": "body", "lines": 3},
    "takeaway":     {"size": 21, "bold": False, "font": "body", "lines": 2},
    "takeaway_no":  {"size": 16, "bold": True, "font": "body", "lines": 1},
    "caption":      {"size": 12, "bold": False, "font": "body", "lines": 2},
    "footer":       {"size": 10.5, "bold": False, "font": "body", "lines": 1},
}
LEAD = 1.22                               # line height = size x LEAD

# ---- themes ---------------------------------------------------------------------------------------------------------
# A theme = colours, fonts, background and accent shapes; the same 8 layouts take any theme.
THEMES = {
    "basic": {
        "name": "기본", "title_font": "sans",
        "bg": "FFFFFF", "text": "1F2937", "title": "0F2847", "accent": "2563EB", "accent2": "93C5FD", "panel": "EEF3FB",
        "muted": "6B7280", "rule": "D5DCE8", "card": "FFFFFF", "card_line": "D5DCE8",
        "section_bg": "0F2847", "section_text": "FFFFFF", "section_accent": "60A5FA",
        "head_bg": "0F2847", "head_text": "FFFFFF", "row_bg": "FFFFFF", "row_alt": "F1F5FB", "row_text": "1F2937",
        "marker": "square", "title_x": M + 20,
    },
    "dark": {
        "name": "다크", "title_font": "sans",
        "bg": "0F141C", "text": "D9DEE7", "title": "FFFFFF", "accent": "2DD4BF", "accent2": "F5B94A", "panel": "182130",
        "muted": "8B95A7", "rule": "263041", "card": "FFFFFF", "card_line": "FFFFFF",
        "section_bg": "0B2A2E", "section_text": "FFFFFF", "section_accent": "2DD4BF",
        "head_bg": "2DD4BF", "head_text": "0F141C", "row_bg": "182130", "row_alt": "1F2A3C", "row_text": "E6EAF0",
        "marker": "dot", "title_x": M,
    },
    "academic": {
        "name": "학술", "title_font": "serif",
        "bg": "FBF8F1", "text": "2B2522", "title": "6B1D1D", "accent": "8C2F2F", "accent2": "C9A227", "panel": "F3ECDF",
        "muted": "7A6E62", "rule": "D9CDB6", "card": "FFFFFF", "card_line": "D9CDB6",
        "section_bg": "6B1D1D", "section_text": "FBF8F1", "section_accent": "E3C46F",
        "head_bg": "6B1D1D", "head_text": "FBF8F1", "row_bg": "FFFDF8", "row_alt": "F4EEE2", "row_text": "2B2522",
        "marker": "dash", "title_x": M,
    },
}
THEME_NAMES = {v["name"]: k for k, v in THEMES.items()}       # 기본 -> basic, ...


def theme_code(value: str) -> str | None:
    """'basic' / 'dark' / 'academic' or the Korean name (기본 / 다크 / 학술) -> the code; None when unknown."""
    v = (value or "").strip()
    return v if v in THEMES else THEME_NAMES.get(v)


# ---- fonts and measuring ------------------------------------------------------------------------------------------

@functools.lru_cache(maxsize=None)
def theme_fonts(code: str) -> dict:
    """{"title"|"body": {"regular": (path, index), "bold": (path, index), "name": family name}} for a theme."""
    from PIL import ImageFont
    regular, bold = find_font()
    sans = {"regular": (regular, 0), "bold": (bold, 0), "name": ImageFont.truetype(regular, 10).getname()[0]}
    fonts = {"body": sans, "title": sans}
    if THEMES[code]["title_font"] == "serif":
        serif = find_serif_font()
        if serif:
            name = ImageFont.truetype(serif, 10, index=0).getname()[0]
            fonts["title"] = {"regular": (serif, 0), "bold": (serif, 0), "name": name, "no_bold": True}
    return fonts


SCALE = 8                                  # measure at 8x the point size for precise widths


@functools.lru_cache(maxsize=None)
def _pil_font(path: str, index: int, size: float):
    from PIL import ImageFont
    return ImageFont.truetype(path, max(1, round(size * SCALE)), index=index)


def font_file(code: str, role: str, bold: bool) -> tuple[str, int]:
    f = theme_fonts(code)[role]
    return f["bold"] if bold and not f.get("no_bold") else f["regular"]


def text_width(code: str, role: str, bold: bool, size: float, text: str) -> float:
    path, index = font_file(code, role, bold)
    return _pil_font(path, index, size).getlength(text) / SCALE


@functools.lru_cache(maxsize=None)
def font_chars(path: str, index: int) -> frozenset | None:
    """The characters a font file has (None when fontTools is missing: then nothing is reported)."""
    try:
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    with TTFont(path, fontNumber=index, lazy=True) as f:
        return frozenset(f.getBestCmap())


def missing_glyphs(code: str, role: str, bold: bool, text: str) -> str:
    """Characters of text the theme's font cannot draw (a slide would show them in another font, or as boxes)."""
    cmap = font_chars(*font_file(code, role, bold))
    if cmap is None:
        return ""
    return "".join(dict.fromkeys(c for c in text if not c.isspace() and ord(c) not in cmap))


def wrap(code: str, role: str, bold: bool, size: float, text: str, width: float) -> list[str]:
    """Lines of text in a box `width` points wide (words kept whole; a word longer than a line is split)."""
    room = width * FIT
    measure = functools.partial(text_width, code, role, bold, size)
    lines: list[str] = []
    for para in str(text).split("\n"):
        line = ""
        for word in para.split(" "):
            trial = f"{line} {word}" if line else word
            if measure(trial) <= room:
                line = trial
                continue
            if line:
                lines.append(line)
            while measure(word) > room:                   # a very long word: split it by characters
                cut = len(word)
                while cut > 1 and measure(word[:cut]) > room:
                    cut -= 1
                lines.append(word[:cut])
                word = word[cut:]
            line = word
        lines.append(line)
    return lines


def overflow_chars(code: str, role: str, bold: bool, size: float, text: str, width: float, max_lines: int) -> int:
    """How many characters at the end do not fit in max_lines (0: it fits)."""
    if len(wrap(code, role, bold, size, text, width)) <= max_lines:
        return 0
    lo, hi = 0, len(text)
    while lo < hi:                                         # longest prefix that fits
        mid = (lo + hi + 1) // 2
        if len(wrap(code, role, bold, size, text[:mid], width)) <= max_lines:
            lo = mid
        else:
            hi = mid - 1
    return len(text) - lo


def chars_per_line(code: str, style: str, width: float) -> int:
    """About how many Korean characters one line of a style holds in a box (for the writer's brief)."""
    s = STYLES[style]
    sample = "가나다라마 바사아자차 카타파하가 나다라마바"
    return int(len(sample) * width * FIT / text_width(code, s["font"], s["bold"], s["size"], sample))


# ---- the deck (program: every value placed from the report, the outline and the writing) ---------------------------

def first_sentence(text: str) -> str:
    """The caption shown on a slide: up to the end of its first sentence (the whole caption goes to the notes)."""
    m = re.search(r"(?<=[.!?])\s+(?=[A-Z가-힣])", text)
    return text[:m.start()] if m and m.start() > 12 else text


def header_count(cells: list[list[str]]) -> int:
    """Leading rows drawn as header: row 1, and the rows right after it that hold no number."""
    n = 1
    while n < len(cells) and not any(re.search(r"\d", c or "") for c in cells[n]):
        n += 1
    return n


def chosen_rows(table: dict, wanted: list | None) -> list[int]:
    """The 1-based rows drawn for a table: its header rows first (row 1 and the rows right under it with no number),
    then the chosen rows (all rows when none are chosen)."""
    n = table["rows"]
    picked = [r for r in (wanted or []) if isinstance(r, int) and 1 <= r <= n]
    if not picked:
        return list(range(1, n + 1))
    head = list(range(1, header_count(table["cells"]) + 1))
    return head + sorted(set(picked) - set(head))


def _find(report: dict, key: str, address: str):
    want = normalize_address(address or "")
    return next((x for x in report[key] if x["address"] == want), None)


def compose(brief: dict, report: dict, outline: dict, writing: dict) -> dict:
    """The deck: per slide its layout and every value it shows. Text from the writer, everything else from the report.
    writing["slides"] holds one written slide per outline slide, in outline order (the program put them in order)."""
    plan, written = outline["slides"], writing["slides"]
    of_paragraph = {a: s for s in report["sections"] for a in s.get("paragraphs", [])}      # paragraph -> its section
    section_titles = [w["title"] for p, w in zip(plan, written) if p["layout"] == "section"]
    deck = {"file": report["file"], "pages": report["pages"], "today": brief["today"],
            "doc_title": document_title(report, plan), "slides": []}
    section_no = 0
    for i, (p, w) in enumerate(zip(plan, written)):
        section_no += p["layout"] == "section"
        deck["slides"].append(slide_entry(i, p["layout"], w, of_paragraph, deck["doc_title"], section_titles, section_no,
                                          table_view(report, p), figure_view(report, p)))
    return deck


def document_title(report: dict, plan: list[dict]) -> str:
    """The document's title: the heading of the text part the cover names (else the file name)."""
    sections = {s["address"]: s for s in report["sections"]}
    cover_parts = plan[0].get("parts") or [] if plan else []
    title_part = sections.get(normalize_address(cover_parts[0])) if cover_parts else None
    return (title_part or {}).get("title") or pathlib.Path(report["file"]).stem


def table_view(report: dict, p: dict) -> dict | None:
    """What a table slide shows of its table: the chosen rows' cells, the caption and the pages (program values)."""
    if p["layout"] != "table":
        return None
    t = _find(report, "tables", p.get("table", ""))
    rows = chosen_rows(t, p.get("rows"))
    cells = [t["cells"][r - 1] for r in rows]
    part = f"표 일부: 전체 {t['rows']}행 중 {len(rows)}행" if len(rows) < t["rows"] else ""
    return {"address": t["address"], "caption": first_sentence(t["caption"] or t["label"]),
            "caption_full": t["caption"] or t["label"], "pages": t["pages"], "cells": cells,
            "header_rows": header_count(cells), "part": part}


def figure_view(report: dict, p: dict) -> dict | None:
    if p["layout"] != "figure":
        return None
    f = _find(report, "figures", p.get("figure", ""))
    return {"address": f["address"], "caption": first_sentence(f["caption"] or f["label"]),
            "caption_full": f["caption"] or f["label"], "pages": f["pages"], "image": f["image"],
            "width": f["width"], "height": f["height"]}


def slide_entry(i: int, layout: str, w: dict, of_paragraph: dict, doc_title: str, section_titles: list[str],
                section_no: int, table: dict | None, figure: dict | None, where: str | None = None) -> dict:
    """One slide of the deck from its layout, the written text and the values the program places."""
    def cite(b):
        part = of_paragraph.get(normalize_address(b.get("source", "")), {})
        return {"text": b["text"], "source": b.get("source", ""), "quote": b.get("quote", ""),
                "page": part.get("pages", ""), "part": part.get("title", "")}

    s = {"no": i + 1, "layout": layout, "title": w.get("title", ""), "where": where or f"slides[{i}]"}
    if layout == "cover":
        s.update(title=doc_title, subtitle=w.get("title", ""))
    elif layout == "agenda":
        s["items"] = section_titles
    elif layout == "section":
        s["number"] = section_no
    if layout in CONTENT:
        if layout == "comparison":
            s["columns"] = [{"heading": c.get("heading", ""), "bullets": [cite(b) for b in c.get("bullets", [])]}
                            for c in w.get("columns", [])]
        else:
            s["bullets"] = [cite(b) for b in w.get("bullets", [])]
    if table:
        s["table"] = table
    if figure:
        s["figure"] = figure
    return s


# ---- one slide at a time: the writer's piece and the deck its check measures -----------------------------------------

def slide_pieces(brief: dict, report: dict, outline: dict) -> list[dict]:
    """One piece per outline slide, in outline order: what the writer needs to write that one slide (the program
    cuts the outline; the writer never counts slides)."""
    plan = outline["slides"]
    sections = {s["address"]: s for s in report["sections"]}
    guide = brief["layouts"]
    doc = {"file": report["file"], "pages": report["pages"], "today": brief["today"],
           "title": document_title(report, plan)}
    pieces, section_no = [], 0
    for i, p in enumerate(plan):
        lay = p["layout"]
        section_no += lay == "section"
        g = guide[lay]
        piece = {"no": i + 1, "of": len(plan), "layout": lay, "topic": p["topic"],
                 "title_chars": guide["title_chars"], "bullets": g["bullets"], "bullet_chars": g.get("bullet_chars", 0),
                 "parts": [{k: sections[a][k] for k in ("address", "title", "pages", "paragraphs")}
                           for a in whole_sections(p["parts"], sections)],
                 "table": table_view(report, p) or {}, "figure": figure_view(report, p) or {},
                 "section_no": section_no if lay == "section" else 0, "document": doc}
        if lay == "section":                   # what the section holds: the topics of its slides, up to the next one
            piece["covers"] = []
            for q in plan[i + 1:]:
                if q["layout"] not in CONTENT[:-1]:          # the next section or the closing ends it
                    break
                piece["covers"].append(q["topic"])
        if piece["figure"]:
            piece["figure"] = {k: v for k, v in piece["figure"].items() if k != "image"}    # the picture stays a file
        pieces.append(piece)
    return pieces


def whole_sections(parts: list[str], sections: dict) -> list[str]:
    """The text parts a slide rests on: the ones it names, each with all the pieces of its section (a section cut at a
    page break, a table or a figure is several parts; the planner may name one piece, the slide gets the whole
    section), in document order, each once."""
    named = {normalize_address(x) for x in parts}
    out = {a for a in named if a in sections}
    for a in list(out):
        out.update(sections[a].get("pieces") or [])
    return [a for a in sections if a in out]


WHERE = "writing"                         # a one-slide writing: its fields are writing.title, writing.bullets[0].text, ...


def piece_deck(piece: dict, w: dict) -> dict:
    """The deck the writer's check measures for one slide: the slide itself, and for a section slide also the agenda
    line that shows its title (the agenda is drawn from the section titles)."""
    of_paragraph = {a: s for s in piece["parts"] for a in s["paragraphs"]}
    doc = piece["document"]
    figure = dict(piece["figure"], image="", width=piece["figure"].get("width", 0),
                  height=piece["figure"].get("height", 0)) if piece["figure"] else None
    s = slide_entry(piece["no"] - 1, piece["layout"], w, of_paragraph, doc["title"], [], piece["section_no"],
                    piece["table"] or None, figure, where=WHERE)
    deck = {"file": doc["file"], "pages": doc["pages"], "today": doc["today"], "doc_title": doc["title"], "slides": [s]}
    if piece["layout"] == "section":           # the agenda line of this section (first in the list: the widest number)
        deck["slides"].insert(0, {"no": 1, "layout": "agenda", "title": "", "items": [w.get("title", "")], "where": "agenda"})
    return deck


def slide_bullets(s: dict) -> list[dict]:
    return list(s.get("bullets", [])) + [b for c in s.get("columns", []) for b in c["bullets"]]


def slide_pages(s: dict) -> list[str]:
    """The pages the slide rests on: its bullets' parts and its table or figure (read from the report)."""
    pages = [b["page"] for b in slide_bullets(s)] + [x["pages"] for x in (s.get("table"), s.get("figure")) if x]
    out: list[int] = []
    for p in pages:
        for n in re.findall(r"\d+", str(p)):
            if int(n) not in out:
                out.append(int(n))
    return [str(n) for n in sorted(out)]


def notes(s: dict) -> str:
    """Speaker notes: the quote behind every bullet, with its page and part, and the full caption."""
    lines = []
    for n, b in enumerate(slide_bullets(s), 1):
        lines.append(f"{n}. {b['text']}\n   근거: 쪽 {b['page']} · {b['part']} — “{b['quote']}”")
    for key, name in (("table", "표"), ("figure", "그림")):
        if s.get(key):
            lines.append(f"{name} (쪽 {s[key]['pages']}): {s[key]['caption_full']}")
    return "\n".join(lines)


# ---- boxes ----------------------------------------------------------------------------------------------------------

class Slide:
    """Collects the boxes of one slide and the text that does not fit (with the writer's field it belongs to)."""

    def __init__(self, code: str):
        self.code, self.theme = code, THEMES[code]
        self.decor: list[dict] = []
        self.boxes: list[dict] = []
        self.problems: list[dict] = []          # {"where", "text", "lines", "max", "over"}

    def shape(self, kind, x, y, w, h, fill, radius=0, decor=False):
        (self.decor if decor else self.boxes).append({"kind": kind, "x": x, "y": y, "w": w, "h": h, "fill": fill, "radius": radius})

    def para(self, w, text, style, color, align="left", where=None, max_lines=None) -> dict:
        """One paragraph wrapped for a box `w` wide. where: the writer's field (text that does not fit is a problem);
        None: program text, which is shortened with … to its lines."""
        st = STYLES[style]
        lines_max = max_lines or st["lines"]
        bold = st["bold"] and not theme_fonts(self.code)[st["font"]].get("no_bold")
        lines = wrap(self.code, st["font"], bold, st["size"], text, w)
        shown = text
        lost = missing_glyphs(self.code, st["font"], bold, text) if where else ""
        if lost:
            self.problems.append({"where": where, "text": text, "missing": lost})
        if len(lines) > lines_max:
            if where:
                self.problems.append({"where": where, "text": text, "lines": len(lines), "max": lines_max,
                                      "over": overflow_chars(self.code, st["font"], bold, st["size"], text, w, lines_max)})
            else:
                lines = lines[:lines_max]
                while lines[-1] and text_width(self.code, st["font"], bold, st["size"], lines[-1] + "…") > w * FIT:
                    lines[-1] = lines[-1][:-1]
                lines[-1] += "…"
                shown = " ".join(lines)
        return {"text": shown, "lines": lines, "size": st["size"], "bold": bold, "font": st["font"], "color": color,
                "align": align, "lh": st["size"] * LEAD, "before": 0}

    def text(self, x, y, w, text, style, color, align="left", anchor="top", h=None, where=None, decor=False, max_lines=None):
        """A text box of one paragraph; returns the height of its lines."""
        p = self.para(w, text, style, color, align, where, max_lines)
        used = len(p["lines"]) * p["lh"]
        (self.decor if decor else self.boxes).append(
            {"kind": "text", "x": x, "y": y, "w": w, "h": h if h is not None else used, "anchor": anchor, **p})
        return used

    def group(self, x, y, w, paras: list[dict], marker: bool = False, indent: float = 0) -> float:
        """One text box of several paragraphs (each with its space before), so PowerPoint flows them as one block;
        marker: a bullet mark in front of each. Returns the height."""
        height = sum(p["before"] + len(p["lines"]) * p["lh"] for p in paras)
        self.boxes.append({"kind": "paras", "x": x, "y": y, "w": w, "h": height, "paras": paras, "indent": indent,
                           "marker": {"shape": self.theme["marker"], "color": self.theme["accent"]} if marker else None})
        return height


def decor(code: str, layout: str) -> tuple[str, list[dict]]:
    """(background colour, accent shapes) of a layout in a theme: what the .pptx keeps in its slide layout."""
    t, sl = THEMES[code], Slide(code)
    bg = t["section_bg"] if layout == "section" else t["bg"]
    W, H = SLIDE_W, SLIDE_H
    if layout == "cover":
        if code == "basic":
            sl.shape("rect", 0, 0, 22, H, t["accent"], decor=True)
            sl.shape("rect", W - 300, 0, 300, H, t["panel"], decor=True)
            sl.shape("oval", W - 250, 96, 190, 190, t["accent2"], decor=True)
            sl.shape("oval", W - 165, 250, 120, 120, t["accent"], decor=True)
            sl.shape("rect", W - 260, 420, 200, 6, t["title"], decor=True)
        elif code == "dark":
            sl.shape("oval", W - 330, -170, 500, 500, "13343A", decor=True)
            sl.shape("oval", W - 190, 300, 260, 260, "2A2418", decor=True)
            sl.shape("oval", W - 300, 330, 22, 22, t["accent2"], decor=True)
            sl.shape("rect", M, 138, 64, 5, t["accent"], decor=True)
        else:
            for y in (40, 46, H - 46, H - 40):
                sl.shape("rect", M, y, W - 2 * M, 2 if y in (40, H - 40) else 0.8, t["accent"], decor=True)
    elif layout == "section":
        if code == "basic":
            sl.shape("rect", 0, 0, 22, H, t["section_accent"], decor=True)
            sl.shape("oval", W - 260, H - 240, 360, 360, "16386A", decor=True)
        elif code == "dark":
            sl.shape("oval", W - 300, -120, 420, 420, "0F3A3E", decor=True)
            sl.shape("rect", 0, H - 8, W, 8, t["accent"], decor=True)
        else:
            sl.shape("rect", M, 40, W - 2 * M, 1.5, t["section_accent"], decor=True)
            sl.shape("rect", M, H - 42, W - 2 * M, 1.5, t["section_accent"], decor=True)
    else:                                          # agenda and every content layout
        if code == "basic":
            sl.shape("rect", M, 38, 6, 32, t["accent"], decor=True)
            sl.shape("rect", M, 498, W - 2 * M, 1, t["rule"], decor=True)
        elif code == "dark":
            sl.shape("rect", M, 80, 56, 4, t["accent"], decor=True)
            sl.shape("rect", M, 498, W - 2 * M, 1, t["rule"], decor=True)
        else:
            sl.shape("rect", M, 20, W - 2 * M, 2, t["accent"], decor=True)
            sl.shape("rect", M, 25, W - 2 * M, 0.8, t["accent"], decor=True)
            sl.shape("rect", M, 84, W - 2 * M, 0.8, t["rule"], decor=True)
            sl.shape("rect", M, 498, W - 2 * M, 0.8, t["accent"], decor=True)
    return bg, sl.decor


MARKER_INDENT = 22


def _block_height(sl: Slide, items: list[dict], style: str, w: float, gap: float) -> float:
    """Height of a list of bullets (as _bullets will place them)."""
    st = STYLES[style]
    lines = [len(wrap(sl.code, st["font"], st["bold"], st["size"], b["text"], w - MARKER_INDENT)) for b in items]
    return sum(lines) * st["size"] * LEAD + gap * max(0, len(items) - 1)


def _bullets(sl: Slide, x: float, y: float, w: float, bottom: float, items: list[dict], style: str, where: str, gap: float):
    """Bullets as one text box from y; reports when they run past `bottom`. Returns the y after the last one."""
    paras = []
    for k, b in enumerate(items):
        p = sl.para(w - MARKER_INDENT, b["text"], style, sl.theme["text"], where=f"{where}[{k}].text")
        p["before"] = gap if k else 0
        paras.append(p)
    end = y + (sl.group(x, y, w, paras, marker=True, indent=MARKER_INDENT) if paras else 0)
    if end > bottom + 0.5:
        sl.problems.append({"where": where, "text": "", "lines": 0, "max": 0, "over": 0, "need": round(end - bottom, 1)})
    return end


def _title(sl: Slide, s: dict):
    x = sl.theme["title_x"]
    sl.text(x, 34, SLIDE_W - M - x, s["title"], "title", sl.theme["title"], where=f"{s['where']}.title")


def _footer(sl: Slide, deck: dict, s: dict):
    pages = slide_pages(s)
    t = sl.theme
    left = deck["doc_title"] + (f" · 근거 쪽 {', '.join(pages)}" if pages else "")
    sl.text(M, 508, 640, left, "footer", t["muted"])
    sl.text(SLIDE_W - M - 120, 508, 120, f"{s['no']} / {len(deck['slides'])}", "footer", t["muted"], align="right")


def table_layout(code: str, cells: list[list[str]], header_rows: int, width: float) -> dict:
    """Column widths, wrapped cells and row heights of a table drawn `width` points wide."""
    n = max(len(r) for r in cells)
    cells = [list(r) + [""] * (n - len(r)) for r in cells]
    size = 14 if n <= 5 else 13 if n <= 6 else 12
    lh, pad_x, pad_y = size * LEAD, 10, 6
    natural = [max(text_width(code, "body", r < header_rows, size, cells[r][c]) for r in range(len(cells))) + 2 * pad_x + 4
               for c in range(n)]
    total = sum(natural)
    widths = [width * v / total for v in natural] if total > width else [v + (width - total) / n for v in natural]
    rows = []
    for r, row in enumerate(cells):
        lines = [wrap(code, "body", r < header_rows, size, txt, widths[c] - 2 * pad_x) if txt else [""] for c, txt in enumerate(row)]
        rows.append({"cells": row, "lines": lines, "h": max(len(x) for x in lines) * lh + 2 * pad_y, "header": r < header_rows})
    return {"widths": widths, "rows": rows, "size": size, "lh": lh, "h": sum(r["h"] for r in rows), "pad_x": pad_x}


def layout_slide(code: str, deck: dict, index: int) -> Slide:
    """Every box of slide `index` in theme `code` (decor of its layout included), with the text that does not fit."""
    s, t = deck["slides"][index], THEMES[code]
    sl = Slide(code)
    bg, sl.decor = decor(code, s["layout"])
    sl.bg = bg
    W, where = SLIDE_W, s["where"]
    lay = s["layout"]
    if lay == "cover":
        meta = f"원본 {deck['file']} · {deck['pages']}쪽 · {deck['today']}"
        if code == "academic":                     # centred between the double rules
            w = W - 2 * M - 80
            st = STYLES["cover_title"]
            title_h = len(wrap(code, st["font"], False, st["size"], s["title"], w)) * st["size"] * LEAD
            y = max(70, (SLIDE_H - (30 + title_h + 52 + 2 * STYLES["cover_sub"]["size"] * LEAD)) / 2 - 10)
            sl.text(M + 40, y, w, "PDF 요약 발표", "cover_label", t["accent"], align="center")
            y += 30 + sl.text(M + 40, y + 30, w, s["title"], "cover_title", t["title"], align="center") + 24
            sl.shape("rect", W / 2 - 40, y, 80, 2, t["accent2"])
            sl.text(M + 40, y + 26, w, s["subtitle"], "cover_sub", t["text"], align="center", where=f"{where}.title")
            sl.text(M + 40, 440, w, meta, "meta", t["muted"], align="center")
        else:
            x = M + 30 if code == "basic" else M
            w = W - 300 - x - 40
            label = sl.para(w, "PDF 요약 발표", "cover_label", t["accent"])
            title = dict(sl.para(w, s["title"], "cover_title", t["title"]), before=12)
            sub = dict(sl.para(w, s["subtitle"], "cover_sub", t["text"], where=f"{where}.title"), before=16)
            sl.group(x, 160 if code == "basic" else 166, w, [label, title, sub])      # one box: PowerPoint keeps them together
            sl.text(x, 452, w, meta, "meta", t["muted"])
    elif lay == "agenda":
        _title(sl, s)
        sections = [i for i, x in enumerate(deck["slides"]) if x["layout"] == "section"]
        for k, item in enumerate(s["items"]):
            y = 130 + k * 72
            sl.text(M, y - 4, 80, f"{k + 1:02d}", "agenda_no", t["accent"])
            target = f"{deck['slides'][sections[k]]['where']}.title (shown on the agenda)" if k < len(sections) else None
            sl.text(M + 96, y, W - 2 * M - 96, item, "agenda_item", t["text"], where=target)
            sl.shape("rect", M + 96, y + 46, W - 2 * M - 96, 1, t["rule"])
        _footer(sl, deck, s)
    elif lay == "section":
        x = M + 40 if code == "basic" else M
        align = "center" if code == "academic" else "left"
        w = W - 2 * M if code == "academic" else W - x - M - 160
        sl.text(x, 150, w, f"{s['number']:02d}", "section_no", t["section_accent"], align=align)
        sl.shape("rect", (W / 2 - 40) if code == "academic" else x, 252, 80, 4, t["section_accent"])
        sl.text(x, 276, w, s["title"], "section_title", t["section_text"], align=align, where=f"{where}.title")
    elif lay == "bullets":
        _title(sl, s)
        block = _block_height(sl, s["bullets"], "bullet", W - 2 * M - 4, 26)
        top = TOP + max(16, (BOTTOM - TOP - block) * 0.4)
        _bullets(sl, M + 4, top, W - 2 * M - 4, BOTTOM, s["bullets"], "bullet", f"{where}.bullets", 26)
        _footer(sl, deck, s)
    elif lay == "figure":
        _title(sl, s)
        f = s["figure"]
        cw, ch = 500, 330
        sl.shape("rect", M - 1, TOP - 1, cw + 2, ch + 2, t["card_line"], radius=7)
        sl.shape("rect", M, TOP, cw, ch, t["card"], radius=6)
        iw, ih = f["width"] or 4, f["height"] or 3
        k = min((cw - 24) / iw, (ch - 24) / ih)
        sl.boxes.append({"kind": "image", "x": M + (cw - iw * k) / 2, "y": TOP + (ch - ih * k) / 2, "w": iw * k, "h": ih * k,
                         "path": f["image"]})
        sl.text(M, TOP + ch + 8, cw, f"{f['caption']} (쪽 {f['pages']})", "caption", t["muted"])
        x = M + cw + 28
        block = _block_height(sl, s["bullets"], "side_bullet", W - M - x, 20)
        _bullets(sl, x, TOP + max(8, (ch - block) / 2), W - M - x, BOTTOM, s["bullets"], "side_bullet", f"{where}.bullets", 20)
        _footer(sl, deck, s)
    elif lay == "table":
        _title(sl, s)
        tb = s["table"]
        tl = table_layout(code, tb["cells"], tb["header_rows"], W - 2 * M)
        sl.boxes.append({"kind": "table", "x": M, "y": TOP, "w": W - 2 * M, "h": tl["h"], **tl,
                         "head_bg": t["head_bg"], "head_text": t["head_text"], "row_bg": t["row_bg"], "row_alt": t["row_alt"],
                         "row_text": t["row_text"]})
        cap = f"{tb['caption']} (쪽 {tb['pages']}{' · ' + tb['part'] if tb['part'] else ''})"
        y = TOP + tl["h"] + 8
        y += sl.text(M, y, W - 2 * M, cap, "caption", t["muted"]) + 14
        _bullets(sl, M + 4, y, W - 2 * M - 4, BOTTOM, s["bullets"], "table_bullet", f"{where}.bullets", 10)
        _footer(sl, deck, s)
    elif lay == "comparison":
        _title(sl, s)
        cw = (W - 2 * M - 24) / 2
        need = max([_block_height(sl, col["bullets"], "col_bullet", cw - 44, 14) for col in s["columns"][:2]] or [0])
        ch = min(BOTTOM - TOP, max(220, 70 + need + 30))
        for c, col in enumerate(s["columns"][:2]):
            x = M + c * (cw + 24)
            sl.shape("rect", x, TOP, cw, ch, t["panel"], radius=8)
            sl.shape("rect", x, TOP, cw, 5, t["accent"] if c == 0 else t["accent2"])
            sl.text(x + 22, TOP + 24, cw - 44, col["heading"], "col_heading", t["title"], where=f"{where}.columns[{c}].heading")
            _bullets(sl, x + 22, TOP + 70, cw - 44, BOTTOM - 16, col["bullets"], "col_bullet", f"{where}.columns[{c}].bullets", 14)
        _footer(sl, deck, s)
    elif lay == "closing":
        _title(sl, s)
        st = STYLES["takeaway"]
        heights = [max(34, len(wrap(code, st["font"], False, st["size"], b["text"], W - 2 * M - 52)) * st["size"] * LEAD)
                   for b in s["bullets"]]
        y = TOP + max(12, (BOTTOM - TOP - sum(heights) - 22 * max(0, len(heights) - 1)) * 0.4)
        for k, (b, h) in enumerate(zip(s["bullets"], heights)):
            sl.shape("oval", M, y + (h - 34) / 2, 34, 34, t["accent"])
            sl.text(M, y + (h - 34) / 2, 34, str(k + 1), "takeaway_no", t["bg"] if code != "dark" else "0F141C", align="center",
                    anchor="middle", h=34)
            sl.text(M + 52, y, W - 2 * M - 52, b["text"], "takeaway", t["text"], anchor="middle", h=h,   # centred by the circle
                    where=f"{where}.bullets[{k}].text")
            y += h + 22
        if y - 22 > BOTTOM:
            sl.problems.append({"where": f"{where}.bullets", "text": "", "lines": 0, "max": 0, "over": 0, "need": round(y - 22 - BOTTOM, 1)})
        _footer(sl, deck, s)
    return sl


def fit_problems(deck: dict) -> list[str]:
    """Sentences for the writer: every text that does not fit its box in any theme, with how much to cut."""
    worst: dict[str, dict] = {}
    for code in THEMES:
        for i in range(len(deck["slides"])):
            for p in layout_slide(code, deck, i).problems:
                key = (p["where"], "missing" if p.get("missing") else "fit")
                if key not in worst or p.get("over", 0) > worst[key].get("over", 0) or p.get("need", 0) > worst[key].get("need", 0):
                    worst[key] = dict(p, theme=THEMES[code]["name"])
    out = []
    for (where, _), p in worst.items():
        if p.get("missing"):
            out.append(f'{where} "{p["text"][:40]}" has characters the slide font cannot draw ({p["missing"]}); '
                       "write them another way (for example - for −, or in words)")
        elif p.get("need"):
            out.append(f"{where}: the bullets run {p['need']:.0f} points past the bottom of the slide (theme {p['theme']}). "
                       "Shorten them or give fewer bullets.")
        else:
            out.append(f'{where} "{p["text"][:40]}" takes {p["lines"]} lines, its box holds {p["max"]} (theme {p["theme"]}). '
                       f"Shorten it by about {p['over']} characters.")
    return out


def table_height(code: str, table: dict, rows: list[int]) -> float:
    """Height in points of a table drawn with these rows (for the planner's check)."""
    cells = [table["cells"][r - 1] for r in rows]
    return table_layout(code, cells, header_count(cells), SLIDE_W - 2 * M)["h"]


def amounts(pages: int) -> dict:
    """How many slides and section dividers a document of `pages` pages gets (cover, agenda and closing included).
    About one section per 4 body slides, so each section has 2 or more content slides; a short document gets one."""
    body = min(14, max(4, math.ceil(pages * 0.6)))
    return {"slides": body + 3, "sections": min(4, max(1, round(body / 4)))}


def writing_guide() -> dict:
    """Per layout: its Korean name, bullets (min, max) and about how many characters one bullet may have (the
    narrowest of the themes, since the fit check measures every theme)."""
    widths = {"bullets": SLIDE_W - 2 * M - 26, "figure": SLIDE_W - M - (M + 528) - 22, "table": SLIDE_W - 2 * M - 26,
              "comparison": (SLIDE_W - 2 * M - 24) / 2 - 66, "closing": SLIDE_W - 2 * M - 52}
    out = {}
    for name, lay in LAYOUTS.items():
        item = {"name": lay["name"], "bullets": list(lay["bullets"])}
        if "style" in lay:
            st = lay["style"]
            item["bullet_chars"] = min(chars_per_line(c, st, widths[name]) for c in THEMES) * STYLES[st]["lines"]
        if lay.get("columns"):
            item["columns"] = lay["columns"]
        out[name] = item
    out["title_chars"] = min(chars_per_line(c, "title", SLIDE_W - 2 * M - 20) for c in THEMES)
    return out
