from functions._links import cjk_errors

RULES = [
    "notes holds every page of the request exactly once, by its number.",
    "A page that was read has a title and 3 key points; a page that was not read says why.",
    "The key points and the reason are English: no Chinese, Japanese or Korean letters.",
]


def check(outputs, inputs):
    wanted = [p["page"] for p in inputs["request"]["pages"]]
    got = [p["page"] for p in outputs["notes"]["pages"]]
    errors = []
    for n in wanted:
        if got.count(n) != 1:
            errors.append(f"notes.pages must hold page {n} exactly once; it holds it {got.count(n)} times")
    for g in got:
        if g not in wanted:
            errors.append(f"page {g} is not in the request; use one of {wanted}")
    for i, p in enumerate(outputs["notes"]["pages"]):
        at = f"notes.pages[{i}]"
        if p["read"]:
            if not p["title"].strip():
                errors.append(f"{at}.title is empty; write the page's title")
            if len([x for x in p["points"] if x.strip()]) != 3:
                errors.append(f"{at}.points has {len(p['points'])} points; write 3")
        elif not p["problem"].strip():
            errors.append(f"{at} was not read; write why in problem")
        for k, x in enumerate(p["points"]):
            errors += cjk_errors(f"{at}.points[{k}]", x)
        errors += cjk_errors(f"{at}.problem", p["problem"])
    return errors
