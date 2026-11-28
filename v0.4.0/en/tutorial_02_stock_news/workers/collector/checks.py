RULES = [
    "coverage holds every company of the brief exactly once.",
    "A company's status is ok, thin or none.",
]


def check(outputs, inputs):
    names = [c["name"] for c in inputs["brief"]["companies"]]
    got = [x["company"] for x in outputs["coverage"]["items"]]
    errors = []
    for n in names:
        if got.count(n) != 1:
            errors.append(f'coverage must hold "{n}" exactly once; it holds it {got.count(n)} times')
    for g in got:
        if g not in names:
            errors.append(f'"{g}" is not a company of the brief; use one of: {", ".join(names)}')
    return errors
