import re

from nextop.file_server import normalize_address

BLANK_LINE = re.compile(r"\n\s*\n")          # paragraphs are cut at blank lines (\r\n ones too): a paragraph has none

# Letters of Chinese, Japanese and Korean: a model sometimes slips them into English text
CJK = re.compile("[\u3040-\u30ff\u3131-\u318e\uac00-\ud7a3\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]")

RULES = {
    "scan": ["scan holds every company of the brief exactly once.",
             "A focus sentence is English: no Chinese, Japanese or Korean letters."],
    "judge": [
        "Every reason's source is the address of one body paragraph of an article this worker may read "
        "(fs://news/003#1.2), not a whole article or section and not the date and URL lines.",
        "A reason's point sentence is English: no Chinese, Japanese or Korean letters.",
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
        errors += cjk_errors(c["company"], "focus", c["focus"])
    return errors


def cjk_errors(company, field, text):
    found = "".join(dict.fromkeys(CJK.findall(text)))
    return [f'{company}: {field} "{text[:40]}..." has Chinese, Japanese or Korean letters ({found}); '
            "write it again in English only"] if found else []


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
            errors += cjk_errors(item["company"], "point", r["point"])
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
    if text.lstrip().startswith(("Date:", "URL:")):
        return [f'{company}: source "{source}" is the date and URL lines; cite a body paragraph of the article']
    return []


def check(outputs):
    return []
