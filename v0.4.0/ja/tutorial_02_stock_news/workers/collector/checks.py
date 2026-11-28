RULES = [
    "coverage には計画のすべての会社がちょうど一回ずつ入っています。",
    "会社の状態（status）は ok、thin、none のどれかです。",
]


def check(outputs, inputs):
    names = [c["name"] for c in inputs["brief"]["companies"]]
    got = [x["company"] for x in outputs["coverage"]["items"]]
    errors = []
    for n in names:
        if got.count(n) != 1:
            errors.append(f"coverage には「{n}」をちょうど一回入れてください（今は {got.count(n)} 回です）")
    for g in got:
        if g not in names:
            errors.append(f"「{g}」は計画の会社ではありません。次のどれかを使ってください: {', '.join(names)}")
    return errors
