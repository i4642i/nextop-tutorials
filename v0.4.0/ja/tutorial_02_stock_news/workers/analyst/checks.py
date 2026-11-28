import re

from nextop.file_server import normalize_address

# A Japanese sentence has kana, and its kanji are the ones Japanese writes (JIS X 0208). A model sometimes slips into
# Chinese (simplified characters, which are mostly outside JIS X 0208), Korean or Russian letters; the cited paragraph
# is English and is not checked. SIMPLIFIED lists Chinese-only characters that JIS X 0208 does have.
KANA = re.compile("[\u3040-\u30ff]")                                             # hiragana, katakana
HAN = re.compile("[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")                    # CJK ideographs
OTHER_LETTERS = re.compile("[\u0400-\u04ff\u1100-\u11ff\u3131-\u318e\uac00-\ud7a3]")      # Cyrillic, Hangul
SIMPLIFIED = set("价后么")
# An English word written in lower case (chip, overhang, foldable) is not a name; names stay English (NVIDIA, iPhone, HBM)
ENGLISH_WORD = re.compile("(?<![A-Za-z])[a-z]{3,}(?![A-Za-z])")
BLANK_LINE = re.compile(r"\n\s*\n")          # paragraphs are cut at blank lines (\r\n ones too): a paragraph has none


def _not_japanese_kanji(ch: str) -> bool:
    if ch in SIMPLIFIED:
        return True
    try:
        ch.encode("shift_jis")
        return False
    except UnicodeEncodeError:
        return True


RULES = {
    "scan": ["scan には計画のすべての会社がちょうど一回ずつ入っています。",
             "focus は日本語の文です（かなを含み、中国語の簡体字、韓国語やロシア語の文字を含みません。英語は会社名と製品名だけです）。"],
    "judge": [
        "理由の source は、このワーカーが読める記事の本文の段落1つのアドレス（fs://news/003#1.2）です。記事全体やセクション、日付とURLの行ではありません。",
        "理由の point は日本語の文です（かなを含み、中国語の簡体字、韓国語やロシア語の文字を含みません。英語は会社名と製品名だけです）。",
        "理由の数: 会社の状態が ok なら2〜3個、thin なら1〜2個、none なら0個（そのとき direction は flat）。",
    ],
}
NEEDED = {"ok": (2, 3), "thin": (1, 2), "none": (0, 0)}


def check_scan(report, inputs):
    names = [c["name"] for c in inputs["brief"]["companies"]]
    got = [c["company"] for c in report["scan"]["companies"]]
    errors = [f"scan.companies には「{n}」をちょうど一回入れてください" for n in names if got.count(n) != 1]
    errors += [f"「{g}」は計画の会社ではありません。次のどれかを使ってください: {', '.join(names)}" for g in got if g not in names]
    for c in report["scan"]["companies"]:
        errors += language_errors(c["company"], "focus", c["focus"])
    return errors


def language_errors(company, field, text):
    """Sent back when the sentence is not Japanese: no kana at all, or letters Japanese does not write."""
    foreign = "".join(dict.fromkeys(OTHER_LETTERS.findall(text) + [ch for ch in HAN.findall(text) if _not_japanese_kanji(ch)]))
    if foreign:
        return [f"{company}: {field}「{text[:40]}…」に日本語でない文字があります（{foreign}）。日本語だけで書き直してください"]
    if not KANA.search(text):
        return [f"{company}: {field}「{text[:40]}…」が日本語の文になっていません。日本語の文で書き直してください"]
    words = ", ".join(dict.fromkeys(ENGLISH_WORD.findall(text)))
    if words:
        return [f"{company}: {field}「{text[:40]}…」に英語の言葉があります（{words}）。日本語で書き直してください"
                "（英語のままでよいのは会社名や製品名だけです）"]
    return []


def check_judge(report, inputs, sources):
    status = {c["company"]: c["status"] for c in inputs["coverage"]["items"]}
    errors = []
    for item in report["outlook"]["items"]:
        low, high = NEEDED.get(status.get(item["company"], "ok"), (1, 3))
        n = len(item["reasons"])
        if not low <= n <= high:
            errors.append(f"{item['company']}: 理由が{n}個です。この会社のニュースの状態は「{status.get(item['company'])}」"
                          f"なので、{low}〜{high}個にしてください")
        for r in item["reasons"]:
            errors += language_errors(item["company"], "point", r["point"])
            errors += paragraph_errors(item["company"], r["source"], sources)
        if status.get(item["company"]) == "none" and item["direction"] != "flat":
            errors.append(f"{item['company']}: 記事が一本も集まっていないので、direction は \"flat\" にしてください")
    return errors


def paragraph_errors(company, source, sources):
    """The program attaches the cited paragraph to the mail, so the address must be one body paragraph: a part address
    (with #) whose text has no blank line inside (the paragraphs splitter cuts at blank lines)."""
    address = normalize_address(source)
    if "#" not in str(address):
        return [f"{company}: source「{source}」は記事全体です。記事の段落を1つ選んでください（query や get の結果にある "
                f"fs://news/003#1.2 のようなアドレスです）"]
    text = sources.text(address)
    if text is None:
        return [f"{company}: source「{source}」は読める記事の段落ではありません。query や get の結果にある "
                f"fs://news/003#1.2 のような段落のアドレスをそのまま写してください"]
    if BLANK_LINE.search(text.strip()):
        return [f"{company}: source「{source}」は記事全体かセクションです。段落を1つ選んでください（get で開くと段落のアドレスが見えます）"]
    if text.lstrip().startswith(("Date:", "URL:")):
        return [f"{company}: source「{source}」は日付とURLの行です。記事の本文の段落を選んでください"]
    return []


def check(outputs):
    return []
