"""End of the flow: builds the outlook mail (text and HTML) from the analyst's result and sends it.

Every title, date and page address in the mail is read by the program from the stored article file, and every quoted
paragraph is the article's own paragraph at the address the worker cited (from the file server's part tree), never
what a worker typed. The mail is also saved in outlooks/ next to the project.
"""
import html
import pathlib

from nextop.file_server import normalize_address, record_address

from functions._news import article_parts, data_dir, recipients, search_problems, send_mail, setting

NAME = "mail_outlook"
FILES_IN = True                       # the flow hands it the articles (share line analyst -> mail_outlook)
DESC = "Build the stock outlook mail and send it"
OUTPUTS = []

DISCLAIMER = "투자 권유가 아닙니다 · 뉴스로 만든 전망입니다"
WORDS = {True: {"up": "상승", "flat": "보합", "down": "하락"}, False: {"up": "호재 중심", "flat": "섞임·잠잠", "down": "악재 중심"}}
ARROW = {"up": "▲", "flat": "▶", "down": "▼"}
COLOR = {"up": "#c62828", "flat": "#616161", "down": "#1565c0"}      # Korean convention: red up, blue down
UNLISTED_NOTE = "비상장 회사라 주가가 없습니다. 이 전망은 뉴스 분위기(호재와 악재)만 본 것입니다."


def article(address: str, files: dict) -> dict:
    """title, date and url of the article a cited paragraph (fs://news/003#1.2) belongs to, and the paragraph's text."""
    row = files.get(record_address(address) or "")
    if row is None:
        return {"title": "(기사를 찾지 못했습니다)", "date": "", "url": address, "quote": ""}
    out = article_parts(pathlib.Path(row["path"]).read_text(encoding="utf-8", errors="replace"))
    cited = normalize_address(address)
    out["quote"] = next((p.get("text", "") for p in row.get("parts") or [] if p["address"] == cited and p.get("leaf")), "")
    return out


def sections(inputs: dict) -> list[dict]:
    brief, coverage = inputs["plan/brief"], inputs["collector/coverage"]
    focus = {c["company"]: c["focus"] for c in inputs["analyst/scan"]["companies"]}
    status = {c["company"]: c["status"] for c in coverage["items"]}
    outlook = {o["company"]: o for o in inputs["analyst/outlook"]["items"]}
    files = {r["address"]: r for r in inputs.get("files/news", [])}
    out = []
    for c in brief["companies"]:
        o = outlook.get(c["name"], {"direction": "flat", "reasons": []})
        out.append({
            "name": c["name"], "ticker": c["ticker"], "listed": c["listed"], "direction": o["direction"],
            "word": WORDS[c["listed"]][o["direction"]], "focus": focus.get(c["name"], ""),
            "status": status.get(c["name"], "none"),
            "reasons": [{"point": r["point"], **article(r["source"], files)} for r in o["reasons"]]})
    return out


def build_text(brief: dict, secs: list[dict]) -> str:
    lines = [f"※ {DISCLAIMER}", "", f"{brief['target_day']} 주가 전망 (뉴스 수집일 {brief['today']})", ""]
    lines += [f"{ARROW[s['direction']]} {s['name']}: {s['word']}" for s in secs]
    for s in secs:
        head = f"{s['name']} ({s['ticker']})" if s["ticker"] else s["name"]
        lines += ["", f"## {head} · {s['word']}"]
        if not s["listed"]:
            lines.append(UNLISTED_NOTE)
        lines.append(f"뉴스 흐름: {s['focus']}")
        if not s["reasons"]:
            lines.append("관련 기사를 찾지 못해 근거 없이 '보합'으로 둡니다.")
        for n, r in enumerate(s["reasons"], 1):
            lines += [f"{n}. {r['point']}", f"   기사: {r['title']} ({r['date']})", f"   {r['url']}", f"   근거 문단: \"{r['quote']}\""]
    lines += ["", f"※ {DISCLAIMER}. 근거 문단은 직원이 고른 기사 문단을 프로그램이 원문 그대로 옮긴 것입니다."]
    return "\n".join(lines) + "\n"


def build_html(brief: dict, secs: list[dict]) -> str:
    e = html.escape
    parts = [f'<div style="font-family:sans-serif;max-width:640px;line-height:1.5">',
             f'<p style="background:#fff3cd;padding:8px 12px;border-radius:6px"><b>{e(DISCLAIMER)}</b></p>',
             f'<h2 style="margin-bottom:4px">{e(brief["target_day"])} 주가 전망</h2>',
             f'<p style="color:#666;margin-top:0">뉴스 수집일 {e(brief["today"])}</p>', "<p>"]
    parts += [f'<span style="color:{COLOR[s["direction"]]}"><b>{ARROW[s["direction"]]} {e(s["name"])} {e(s["word"])}</b></span>'
              + ("<br>" if i < len(secs) - 1 else "") for i, s in enumerate(secs)]
    parts.append("</p>")
    for s in secs:
        head = f'{s["name"]} ({s["ticker"]})' if s["ticker"] else s["name"]
        parts.append(f'<h3 style="border-top:1px solid #ddd;padding-top:10px">{e(head)} · '
                     f'<span style="color:{COLOR[s["direction"]]}">{ARROW[s["direction"]]} {e(s["word"])}</span></h3>')
        if not s["listed"]:
            parts.append(f'<p style="color:#8a6d3b">{e(UNLISTED_NOTE)}</p>')
        parts.append(f'<p>뉴스 흐름: {e(s["focus"])}</p>')
        if not s["reasons"]:
            parts.append("<p>관련 기사를 찾지 못해 근거 없이 '보합'으로 둡니다.</p>")
        parts.append("<ol>")
        for r in s["reasons"]:
            parts.append(f'<li>{e(r["point"])}<br><small>기사: <a href="{e(r["url"])}">{e(r["title"])}</a> ({e(r["date"])})</small>'
                         f'<br><small style="color:#555">근거 문단: "{e(r["quote"])}"</small></li>')
        parts.append("</ol>")
    parts.append(f'<p style="color:#666"><small>{e(DISCLAIMER)}. 근거 문단은 직원이 고른 기사 문단을 프로그램이 원문 그대로 옮긴 것입니다.</small></p></div>')
    return "\n".join(parts)


def run(ctx, inputs):
    failed = search_problems()                     # "the search could not be asked" is not "no news": never mail it as flat
    if failed:
        return {"error": "뉴스 검색을 하지 못해 전망 메일을 만들지 않았습니다: "
                + "; ".join(f"{r['company']} - {r['problem']}" for r in failed)}
    brief = inputs["plan/brief"]
    secs = sections(inputs)
    text, page = build_text(brief, secs), build_html(brief, secs)
    folder = data_dir() / "outlooks"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = brief["target_day"].split(" ")[0]
    (folder / f"{stamp}.txt").write_text(text, encoding="utf-8")
    (folder / f"{stamp}.html").write_text(page, encoding="utf-8")
    test = "[주가 전망·시험] " if setting("MAIL_TEST_MODE", "1") == "1" else "[주가 전망] "
    short = brief["target_day"].replace(" ", "")
    subject = test + f"{short} " + " · ".join(f"{s['name']} {s['word']}" for s in secs)
    ok, note = send_mail(recipients(), subject, text, page)
    if not ok:
        return {"error": f"전망 메일을 보내지 못했습니다 ({note}). 전망은 outlooks/{stamp}.txt 에 있습니다"}
    return {}
