from nextop.file_server import normalize_address

from functions._deck import (CONTENT, LAYOUTS, MAX_TABLE_COLS, MAX_TABLE_HEIGHT, MAX_TABLE_ROWS, THEMES, chosen_rows,
                             table_height, whole_sections)

RULES = [
    "The outline has exactly brief.slides slides: cover first, agenda second, a section third, closing last, "
    "brief.sections section slides, each followed by at least one content slide.",
    "Every layout is one of the 8 layout codes.",
    "Every address is one of the report's: text parts in parts, a table in table, a figure in figure; each table and figure once.",
    "A table slide's table has at most 7 columns and at most 8 rows shown, and leaves room for its bullets.",
    "A table or figure slide names in parts at least one of that table's or figure's text_parts (the text that talks "
    "about it; a piece of the same section counts), so its bullets can quote that text.",
]


def _addr(a: str) -> str:
    return normalize_address(a or "")


def check(outputs, inputs):
    slides, brief, report = outputs["outline"]["slides"], inputs["brief"], inputs["report"]
    errors = []
    names = ", ".join(f"{k} ({v['name']})" for k, v in LAYOUTS.items())
    bad = [(i, s["layout"]) for i, s in enumerate(slides) if s["layout"] not in LAYOUTS]
    for i, lay in bad:
        errors.append(f"slides[{i}].layout {lay!r} is not a layout; use one of: {names}")
    if len(slides) != brief["slides"]:
        errors.append(f"the outline has {len(slides)} slides; brief.slides is {brief['slides']}: give exactly that many")
    if bad or not slides:
        return errors
    layouts = [s["layout"] for s in slides]
    for i, lay in ((0, "cover"), (1, "agenda"), (len(slides) - 1, "closing")):
        if i < len(slides) and layouts[i] != lay:
            errors.append(f"slides[{i}] must be {lay} ({LAYOUTS[lay]['name']}), not {layouts[i]}")
    for lay, place in (("cover", 0), ("agenda", 1), ("closing", len(slides) - 1)):
        extra = [i for i, x in enumerate(layouts) if x == lay and i != place]
        if extra:
            errors.append(f"{lay} ({LAYOUTS[lay]['name']}) is only slide {place + 1}; slides {extra} use it too")
    if len(slides) > 2 and layouts[2] != "section":
        errors.append(f"slides[2] must be the first section ({LAYOUTS['section']['name']}), not {layouts[2]}")
    n_sections = layouts.count("section")
    if n_sections != brief["sections"]:
        errors.append(f"the outline has {n_sections} section slides; brief.sections is {brief['sections']}")
    for i, lay in enumerate(layouts):
        if lay == "section" and (i + 1 >= len(layouts) or layouts[i + 1] not in CONTENT[:-1]):
            errors.append(f"slides[{i}] is a section; the next slide must be a content slide (bullets, figure, table or comparison)")

    sections = {s["address"]: s for s in report["sections"]}
    texts = set(sections)
    tables = {t["address"]: t for t in report["tables"]}
    figure_of = {f["address"]: f for f in report["figures"]}
    figures = set(figure_of)
    used: list[str] = []
    for i, s in enumerate(slides):
        lay, parts = s["layout"], [_addr(p) for p in s["parts"]]
        wrong = [p for p in s["parts"] if _addr(p) not in texts]
        if wrong:
            errors.append(f"slides[{i}].parts {wrong} are not text parts of the report (report.sections[].address)")
        if lay == "cover" and len(parts) != 1:
            errors.append("slides[0].parts must be the one text part that holds the document's title")
        if lay in CONTENT and not parts:
            errors.append(f"slides[{i}] ({lay}) needs at least one text part in parts: its bullets quote them")
        if lay != "table" and (s["table"] or s["rows"]):
            errors.append(f"slides[{i}] is {lay}: only a table slide has a table and rows; leave table \"\" and rows []")
        if lay != "figure" and s["figure"]:
            errors.append(f"slides[{i}] is {lay}: only a figure slide has a figure; leave figure \"\"")
        about = (tables.get(_addr(s["table"])) if lay == "table" else
                 figure_of.get(_addr(s["figure"])) if lay == "figure" else None)
        if about and about.get("text_parts") and not set(about["text_parts"]) & set(whole_sections(parts, sections)):
            errors.append(f"slides[{i}] shows {about['address']} ({about['label'][:40]}), but its parts {s['parts']} do not "
                          f"talk about it: name at least one of its text_parts {about['text_parts']} in parts")
        if lay == "figure":
            if _addr(s["figure"]) not in figures:
                errors.append(f"slides[{i}].figure {s['figure']!r} is not one of the report's figures: {sorted(figures) or 'none'}")
            elif _addr(s["figure"]) in used:
                errors.append(f"slides[{i}] shows {_addr(s['figure'])} again; show each figure once")
            else:
                used.append(_addr(s["figure"]))
        if lay == "table":
            t = tables.get(_addr(s["table"]))
            if t is None:
                errors.append(f"slides[{i}].table {s['table']!r} is not one of the report's tables: {sorted(tables) or 'none'}")
                continue
            if t["address"] in used:
                errors.append(f"slides[{i}] shows {t['address']} again; show each table once")
                continue
            used.append(t["address"])
            if t["columns"] > MAX_TABLE_COLS:
                errors.append(f"slides[{i}].table {t['address']} has {t['columns']} columns, more than {MAX_TABLE_COLS}: "
                              "it cannot be read on a slide. Choose another table or another layout.")
                continue
            outside = [r for r in s["rows"] if not 1 <= r <= t["rows"]]
            if outside:
                errors.append(f"slides[{i}].rows {outside} are outside 1..{t['rows']} (row 1 is the header row)")
                continue
            rows = chosen_rows(t, s["rows"])
            if len(rows) > MAX_TABLE_ROWS:
                errors.append(f"slides[{i}].table {t['address']} would show {len(rows)} rows; at most {MAX_TABLE_ROWS} fit "
                              "(header included). Give the numbers of the most important rows in rows.")
                continue
            height = max(table_height(code, t, rows) for code in THEMES)
            if height > MAX_TABLE_HEIGHT:
                errors.append(f"slides[{i}].table {t['address']} with these rows is {height:.0f} points tall; at most "
                              f"{MAX_TABLE_HEIGHT} leave room for the bullets. Show fewer rows.")
    return errors
