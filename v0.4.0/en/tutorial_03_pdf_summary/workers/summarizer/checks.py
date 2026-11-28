from nextop.file_server import normalize_address
from nextop.parts import check_part

from functions._pdf import MAX_COLS, MAX_ROWS, cjk_errors, overflow_chars, page_count, render_summary

RULES = [
    "Every key point cites one paragraph (a sections[].paragraphs address of the report) or a table of the report, and "
    "a quote that is in that paragraph or table word for word.",
    "A chosen table or figure must be one of the report's, each at most once, and a table must be drawable (at most 10 columns).",
    "A table with more than 14 rows needs the numbers of the rows to show (the page then says it shows part of the table).",
    "The written sentences are English: no Chinese, Japanese or Korean letters (a quote and the title may have them).",
    "The summary must fit one A4 page; the check says how many pages and characters are too many.",
]


def _chosen(summary, report):
    """Errors about which tables and figures were chosen (the program draws them from the report, never from the model's words)."""
    errors = []
    for name, key, field in (("tables", "tables", "source"), ("figures", "figures", "figure")):
        known = {x["address"]: x for x in report[key]}
        seen = []
        for i, item in enumerate(summary[name]):
            address = normalize_address(item[field])
            if address not in known:
                errors.append(f"summary.{name}[{i}].{field} {item[field]!r} is not one of the report's {key}: {list(known) or 'none'}")
            elif address in seen:
                errors.append(f"summary.{name}[{i}] repeats {address}; choose each one once")
            else:
                seen.append(address)
        for i, item in enumerate(summary[name]):
            t = known.get(normalize_address(item[field]))
            if name != "tables" or t is None:
                continue
            wanted = item.get("rows") or []
            if t["columns"] > MAX_COLS:
                errors.append(f"summary.tables[{i}] ({t['address']}) has {t['columns']} columns, more than {MAX_COLS}: it cannot be drawn "
                              "on the page. Choose another table or none.")
            bad = [r for r in wanted if not 1 <= r <= t["rows"]]
            if bad:
                errors.append(f"summary.tables[{i}].rows {bad} are outside 1..{t['rows']} (row 1 is the header row)")
            if t["rows"] > MAX_ROWS and not 1 < len(set(wanted) | {1}) <= MAX_ROWS:
                errors.append(f"summary.tables[{i}] ({t['address']}) has {t['rows']} rows. Give the numbers of the rows to show "
                              f"(rows, 1 is the header; at most {MAX_ROWS} including it), or choose another table.")
    return errors


def _cited(summary, report):
    """Errors about the key points' sources: each is one paragraph of a section, or a table (the quote check then looks
    for the quote in that paragraph or table only)."""
    paragraphs = {a: s for s in report["sections"] for a in s["paragraphs"]}
    tables = {t["address"] for t in report["tables"]}
    errors = []
    for i, k in enumerate(summary["key_points"]):
        address = normalize_address(k["source"])
        if address in paragraphs or address in tables:
            continue
        section = next((s for s in report["sections"] if s["address"] == address), None)
        if section is not None:
            errors.append(f"summary.key_points[{i}].source {k['source']!r} is a whole section; cite the paragraph the quote "
                          f"is in, one of {section['paragraphs']} (in the order the section's text shows them)")
        else:
            errors.append(f"summary.key_points[{i}].source {k['source']!r} is not a paragraph or table of the report; "
                          "use an address from sections[].paragraphs or tables[].address")
    return errors


def check(outputs, inputs, sources):
    summary, report = outputs["summary"], inputs["report"]
    errors = _chosen(summary, report) + _cited(summary, report)
    sentences = [("conclusion", summary["conclusion"])]                  # the title is the document's own
    sentences += [(f"key_points[{i}].point", k["point"]) for i, k in enumerate(summary["key_points"])]
    sentences += [(f"{n}[{i}].line", x["line"]) for n in ("tables", "figures") for i, x in enumerate(summary[n])]
    for where, text in sentences:
        errors += cjk_errors(where, text)
    errors += check_part("quotes")(outputs, sources, fields={"address": "source", "quote": "quote"})
    if errors:                                                    # draw only a summary whose choices can be drawn
        return errors
    pdf = render_summary(summary, report, "0000-00-00")           # the same drawing the mail block uses
    if page_count(pdf) > 1:
        errors.append(f"The summary does not fit one A4 page: it runs to {page_count(pdf)} pages and about {overflow_chars(pdf)} "
                      "characters of text spill past page 1. Make it smaller by at least that much: choose fewer tables or figures, "
                      "show fewer rows of a table, or shorten the sentences (key points, lines, conclusion).")
    return errors
