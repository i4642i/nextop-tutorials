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

DISCLAIMER = "Not investment advice · an outlook made from the news"
WORDS = {True: {"up": "Up", "flat": "Flat", "down": "Down"},
         False: {"up": "Mostly good news", "flat": "Mixed or quiet", "down": "Mostly bad news"}}
ARROW = {"up": "▲", "flat": "▶", "down": "▼"}
COLOR = {"up": "#2e7d32", "flat": "#616161", "down": "#c62828"}      # US convention: green up, red down
UNLISTED_NOTE = "Not a listed company, so there is no share price. This outlook only looks at the news mood (good and bad news)."
SOURCE_NOTE = "The cited paragraphs are the article paragraphs the worker chose, copied word for word by the program."


def article(address: str, files: dict) -> dict:
    """title, date and url of the article a cited paragraph (fs://news/003#1.2) belongs to, and the paragraph's text."""
    row = files.get(record_address(address) or "")
    if row is None:
        return {"title": "(article not found)", "date": "", "url": address, "quote": ""}
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
    lines = [f"* {DISCLAIMER}", "", f"Stock outlook for {brief['target_day']} (news collected {brief['today']})", ""]
    lines += [f"{ARROW[s['direction']]} {s['name']}: {s['word']}" for s in secs]
    for s in secs:
        head = f"{s['name']} ({s['ticker']})" if s["ticker"] else s["name"]
        lines += ["", f"## {head} · {s['word']}"]
        if not s["listed"]:
            lines.append(UNLISTED_NOTE)
        lines.append(f"In the news: {s['focus']}")
        if not s["reasons"]:
            lines.append(f"No articles were found, so this is left at {WORDS[s['listed']]['flat']} with no reasons.")
        for n, r in enumerate(s["reasons"], 1):
            lines += [f"{n}. {r['point']}", f"   Article: {r['title']} ({r['date']})", f"   {r['url']}", f"   Cited paragraph: \"{r['quote']}\""]
    lines += ["", f"* {DISCLAIMER}. {SOURCE_NOTE}"]
    return "\n".join(lines) + "\n"


def build_html(brief: dict, secs: list[dict]) -> str:
    e = html.escape
    parts = [f'<div style="font-family:sans-serif;max-width:640px;line-height:1.5">',
             f'<p style="background:#fff3cd;padding:8px 12px;border-radius:6px"><b>{e(DISCLAIMER)}</b></p>',
             f'<h2 style="margin-bottom:4px">Stock outlook for {e(brief["target_day"])}</h2>',
             f'<p style="color:#666;margin-top:0">News collected {e(brief["today"])}</p>', "<p>"]
    parts += [f'<span style="color:{COLOR[s["direction"]]}"><b>{ARROW[s["direction"]]} {e(s["name"])} {e(s["word"])}</b></span>'
              + ("<br>" if i < len(secs) - 1 else "") for i, s in enumerate(secs)]
    parts.append("</p>")
    for s in secs:
        head = f'{s["name"]} ({s["ticker"]})' if s["ticker"] else s["name"]
        parts.append(f'<h3 style="border-top:1px solid #ddd;padding-top:10px">{e(head)} · '
                     f'<span style="color:{COLOR[s["direction"]]}">{ARROW[s["direction"]]} {e(s["word"])}</span></h3>')
        if not s["listed"]:
            parts.append(f'<p style="color:#8a6d3b">{e(UNLISTED_NOTE)}</p>')
        parts.append(f'<p>In the news: {e(s["focus"])}</p>')
        if not s["reasons"]:
            parts.append(f"<p>No articles were found, so this is left at {e(WORDS[s['listed']]['flat'])} with no reasons.</p>")
        parts.append("<ol>")
        for r in s["reasons"]:
            parts.append(f'<li>{e(r["point"])}<br><small>Article: <a href="{e(r["url"])}">{e(r["title"])}</a> ({e(r["date"])})</small>'
                         f'<br><small style="color:#555">Cited paragraph: "{e(r["quote"])}"</small></li>')
        parts.append("</ol>")
    parts.append(f'<p style="color:#666"><small>{e(DISCLAIMER)}. {e(SOURCE_NOTE)}</small></p></div>')
    return "\n".join(parts)


def run(ctx, inputs):
    failed = search_problems()                     # "the search could not be asked" is not "no news": never mail it as flat
    if failed:
        return {"error": "no outlook mail was made because the news search could not be made: "
                + "; ".join(f"{r['company']} - {r['problem']}" for r in failed)}
    brief = inputs["plan/brief"]
    secs = sections(inputs)
    text, page = build_text(brief, secs), build_html(brief, secs)
    folder = data_dir() / "outlooks"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = brief["target_day"].split(" ")[0]
    (folder / f"{stamp}.txt").write_text(text, encoding="utf-8")
    (folder / f"{stamp}.html").write_text(page, encoding="utf-8")
    test = "[Stock outlook TEST] " if setting("MAIL_TEST_MODE", "1") == "1" else "[Stock outlook] "
    subject = test + f"{brief['target_day']} " + ", ".join(f"{s['name']} {s['word']}" for s in secs)      # plain ASCII subject
    ok, note = send_mail(recipients(), subject, text, page)
    if not ok:
        return {"error": f"the outlook mail was not sent ({note}); the outlook is in outlooks/{stamp}.txt"}
    return {}
