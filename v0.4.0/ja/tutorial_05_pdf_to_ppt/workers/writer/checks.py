from nextop.file_server import normalize_address
from nextop.parts import check_part

from functions._common import double_term_errors, language_errors
from functions._deck import CONTENT, LAYOUTS, WHERE, fit_problems, piece_deck

RULES = [
    "The writing is one slide: the slide of the piece (slide). Its layout decides the bullets: the number "
    "slide.bullets gives; a comparison has two columns; cover, agenda and section have none.",
    "Every bullet cites one paragraph of the slide's parts (slide.parts[].paragraphs), and its quote is in that "
    "paragraph word for word.",
    "The written text is Japanese: kana in every longer text, no Korean letters, no Chinese-only characters, "
    "no term written twice with parentheses.",
    "Every text fits its box in every theme; the check says how many characters to cut.",
]


def _addr(a: str) -> str:
    return normalize_address(a or "")


def check(outputs, inputs, sources):
    w, piece = outputs["writing"], inputs["slide"]
    lay = piece["layout"]
    low, high = LAYOUTS[lay]["bullets"]
    name = f"{lay} ({LAYOUTS[lay]['name']})"
    errors = []
    if not w["title"].strip():
        errors.append(f"{WHERE}.title is empty")
    if lay == "comparison":
        if w["bullets"]:
            errors.append(f"this slide is {name}: put the bullets in its two columns and leave bullets []")
        if len(w["columns"]) != 2:
            errors.append(f"this slide is {name}: give exactly 2 columns (left and right), not {len(w['columns'])}")
        groups = [(f"{WHERE}.columns[{c}].bullets", col["bullets"]) for c, col in enumerate(w["columns"])]
    else:
        if w["columns"]:
            errors.append(f"this slide is {name}: only a comparison has columns; leave columns []")
        groups = [(f"{WHERE}.bullets", w["bullets"])]
    paragraphs = [a for part in piece["parts"] for a in part["paragraphs"]]
    whole = {part["address"] for part in piece["parts"]}
    for where, bullets in groups:
        if not low <= len(bullets) <= high:
            want = "no bullets" if high == 0 else f"{low} to {high} bullets"
            errors.append(f"{where} has {len(bullets)}; this slide is {name} and takes {want}")
        for k, b in enumerate(bullets):
            if lay not in CONTENT or _addr(b["source"]) in paragraphs:
                continue
            if _addr(b["source"]) in whole:
                errors.append(f"{where}[{k}].source {b['source']!r} is a whole part; cite the paragraph the quote is in, "
                              f"one of {paragraphs}")
            else:
                errors.append(f"{where}[{k}].source {b['source']!r} is not a paragraph of this slide's parts; "
                              f"use one of {paragraphs}")
    for where, text in texts_of(w):
        errors += language_errors(where, text) + double_term_errors(where, text)
    errors += check_part("quotes")(outputs, sources, fields={"address": "source", "quote": "quote"})
    if errors:                                         # measure only a slide whose shape is right
        return errors
    return fit_problems(piece_deck(piece, w))


def texts_of(w):
    """Every text the slide shows, with its place (for the Japanese and parentheses checks)."""
    yield f"{WHERE}.title", w["title"]
    for k, b in enumerate(w["bullets"]):
        yield f"{WHERE}.bullets[{k}].text", b["text"]
    for c, col in enumerate(w["columns"]):
        yield f"{WHERE}.columns[{c}].heading", col["heading"]
        for k, b in enumerate(col["bullets"]):
            yield f"{WHERE}.columns[{c}].bullets[{k}].text", b["text"]
