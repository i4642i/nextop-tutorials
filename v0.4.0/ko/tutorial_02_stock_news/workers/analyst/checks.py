import re

from nextop.file_server import normalize_address

HAN = re.compile("[㐀-䶿一-鿿]")          # Chinese characters: a model sometimes slips them into Korean text
BLANK_LINE = re.compile(r"\n\s*\n")          # paragraphs are cut at blank lines (\r\n ones too): a paragraph has none

RULES = {
    "scan": ["scan holds every company of the brief exactly once.", "A focus sentence has no Chinese characters."],
    "judge": [
        "Every reason's source is the address of one body paragraph of an article this worker may read "
        "(fs://news/003#1.2), not a whole article or section and not the date and address lines.",
        "A reason's point sentence has no Chinese characters (the quote may).",
        "Reasons: 2-3 when the company's status is ok, 1-2 when thin, none when none (then direction is flat).",
    ],
}
NEEDED = {"ok": (2, 3), "thin": (1, 2), "none": (0, 0)}


def check_scan(report, inputs):
    names = [c["name"] for c in inputs["brief"]["companies"]]
    got = [c["company"] for c in report["scan"]["companies"]]
    errors = [f'scan.companies must hold "{n}" exactly once' for n in names if got.count(n) != 1]
    errors += [f'"{g}" is not a company of the brief; use one of: {", ".join(names)}' for g in got if g not in names]
    for c in report["scan"]["companies"]:
        errors += han_errors(c["company"], "focus", c["focus"])
    return errors


def han_errors(company, field, text):
    found = "".join(dict.fromkeys(HAN.findall(text)))
    return [f'{company}: {field} "{text[:40]}..." has Chinese characters ({found}); write it again in Korean only'] if found else []


def check_judge(report, inputs, sources):
    status = {c["company"]: c["status"] for c in inputs["coverage"]["items"]}
    errors = []
    for item in report["outlook"]["items"]:
        low, high = NEEDED.get(status.get(item["company"], "ok"), (1, 3))
        n = len(item["reasons"])
        if not low <= n <= high:
            errors.append(f'{item["company"]}: {n} reasons; this company\'s news status is '
                          f'"{status.get(item["company"])}", so write {low} to {high}')
        for r in item["reasons"]:
            errors += han_errors(item["company"], "point", r["point"])
            errors += paragraph_errors(item["company"], r["source"], sources)
        if status.get(item["company"]) == "none" and item["direction"] != "flat":
            errors.append(f'{item["company"]}: no articles were collected, so direction must be "flat"')
    return errors


def paragraph_errors(company, source, sources):
    """The program attaches the cited paragraph to the mail, so the address must be one body paragraph: a part address
    (with #) whose text has no blank line inside (the paragraphs splitter cuts at blank lines)."""
    address = normalize_address(source)
    if "#" not in str(address):
        return [f'{company}: source "{source}" is a whole article; cite one of its paragraphs (an address like '
                f'fs://news/003#1.2 from a query or get result)']
    text = sources.text(address)
    if text is None:
        return [f'{company}: source "{source}" is not a paragraph of an article you can read; copy a paragraph address '
                f'like fs://news/003#1.2 from a query or get result']
    if BLANK_LINE.search(text.strip()):
        return [f'{company}: source "{source}" is a whole article or section; cite one of its paragraphs (open it with '
                f'get to see their addresses)']
    if text.lstrip().startswith(("날짜:", "주소:")):
        return [f'{company}: source "{source}" is the date and address lines; cite a body paragraph of the article']
    return []


def check(outputs):
    return []
