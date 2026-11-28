"""The whole flow (plan -> collector -> analyst -> mail) with a scripted model; search, store, paragraph check and mail run for real.

What is checked: the collector's uploads carry the company as a tag and an address seen before is not stored twice
(also across two runs), the analyst talks about one company at a time and sees only that company's articles, a
reason that cites a whole article instead of one of its paragraphs is refused and fixed, a listed company (SpaceX) gets a normal up/flat/down outlook,
a page outside the US news sites of stocks.json is never stored, every text the program writes is Japanese,
and the mail goes to the local mini SMTP server with the disclaimer, the exact article addresses, the cited paragraphs
(copied by the program from the article) and the test prefix.
"""
import email
import email.policy
import json
import pathlib
import re

import pytest
from conftest import ARTICLES, FakeLLM, adapters, addresses, call, last_tool_json, save, text_of, views
from nextop.runtime.flow import run_flow
from test_program import smtp_server  # noqa: F401  (the fixture)

ORDER = ["エヌビディア", "アップル", "マイクロン", "スペースX"]          # the names of stocks.json
ENGLISH = dict(zip(ORDER, ["NVIDIA", "Apple", "Micron", "SpaceX"]))     # the articles are English: so is the question


def _collector(statuses=None):
    """Search each company once, upload what the search returned (tagged with the company), then save the coverage."""
    steps = []
    for n, name in enumerate(ORDER):
        steps.append(call("news_search", {"company": name}, f"s{n}"))
        steps.append(lambda m, name=name: call("upload", {"to": "fs://news", "items": [
            {"file": a["file"], "title": a["title"], "source": a["source"], "tags": [name]}
            for a in last_tool_json(m)["articles"]]}, "u" + name))
    items = [{"company": n, "status": {"スペースX": "thin", **(statuses or {})}.get(n, "ok"), "note": f"{n}のニュースを集めました。"} for n in ORDER]
    steps.append(save(coverage={"items": items}))
    return steps


def _paragraphs(messages):
    """The paragraph addresses (fs://news/003#1.2) the last tool result gave, body paragraphs only."""
    got = last_tool_json(messages)
    return [x["address"] for x in got.get("passages") or [] if not x["text"].startswith("Date:")]


def _analyst(project_dir, bad_source_for=None, fake_holder=None):
    """scan: one save. judge: per company ask each of its first two articles with query, then save citing a body
    paragraph of each (or, once, a whole article: refused, then saved again)."""
    fake_holder = {} if fake_holder is None else fake_holder
    def scan(m):
        return save(scan={"companies": [{"company": n, "focus": f"{n}の最近のニュースです"} for n in ORDER]})

    def judge(name, direction):
        cited = []
        articles = 1 if name == "スペースX" else 2              # the fake search keeps one SpaceX article (thin)

        def ask(k):
            def run(m):
                if k:
                    cited.extend(_paragraphs(m)[:1])
                return call("query", {"question": f"{ENGLISH[name]} shares analysts", "address": addresses(m)[k]}, f"q{k}")
            return run

        def answer(m):
            if not fake_holder.get(name):                    # the paragraphs of the last query (not again on a retry)
                fake_holder[name] = True
                cited.extend(_paragraphs(m)[:1])
            reasons = [{"point": f"{name}の記事から読み取れる理由です。", "source": a} for a in dict.fromkeys(cited)]
            if name == bad_source_for and not fake_holder.get("fixed"):
                fake_holder["fixed"] = True
                reasons[0]["source"] = reasons[0]["source"].split("#")[0]          # the whole article: refused
            return save(outlook={"items": [{"company": name, "direction": direction, "reasons": reasons}]})
        return [ask(k) for k in range(articles)] + [answer] + ([answer] if name == bad_source_for else [])

    steps = [scan]
    for name, direction in zip(ORDER, ["up", "flat", "down", "up"]):
        steps += judge(name, direction)
    return steps


def _run(proj, project_dir, fake, today="2026-11-25"):
    return run_flow(proj, "daily_outlook", {"today": today}, adapters=adapters(fake))


def test_whole_flow_collects_judges_and_mails(news, proj, project_dir, smtp_server, tmp_path):
    holder = {}
    fake = FakeLLM({"collector": _collector(), "analyst": _analyst(project_dir, "アップル", holder)})
    res = _run(proj, project_dir, fake)
    assert res.ok, res.failed

    assert len(news.searches) == 4                                  # one paid search per company
    store = project_dir / "file_servers" / "news" / "store" / "items"
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(store.glob("*.json"))]
    tags = {r["title"]: r.get("tags") for r in records}
    assert tags["NVIDIA expands supply deals"] == ["エヌビディア"] and tags["SpaceX Starship test flight set"] == ["スペースX"]
    assert len(records) == 2 + 2 + 2 + 1                            # the repeated address was never stored twice
    assert "SpaceX rumor of the day" not in tags                    # not one of the US news sites

    # the judge conversation for one company lists only that company's articles
    judge_calls = [m for who, m in fake.calls if who == "analyst" and "fs://news/003" in text_of(m)
                   and "fs://news/001" not in text_of(m)]                     # Apple's conversation: not NVIDIA's files
    assert judge_calls and "fs://news/005" not in text_of(judge_calls[0])

    # the reason that cited a whole article went back to the analyst once, asking for one of its paragraphs
    bad = [m for who, m in fake.calls if who == "analyst" and "記事の段落を1つ選んでください" in text_of(m)]
    assert bad, "the paragraph check never refused anything"

    assert len(smtp_server) == 1
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"]
    assert mail["Subject"].startswith("[株価見通し テスト] 2026-11-26 (木) エヌビディア 上昇")
    assert "スペースX 上昇" in mail["Subject"] and "マイクロン 下落" in mail["Subject"] and "アップル 横ばい" in mail["Subject"]
    body = mail.get_body(preferencelist=("plain",)).get_content()
    page = mail.get_body(preferencelist=("html",)).get_content()
    assert "投資の勧誘ではありません · ニュースから作った見通しです" in body and "投資の勧誘ではありません" in page
    assert "Nasdaq: SPCX" in body and "上場していない会社" not in body and "好材料が中心" not in body   # listed: normal
    assert "https://www.reuters.com/a/1" in body and "utm_source" not in body        # the clean address, read by the program
    assert "https://www.marketwatch.com/c/1" in page and "NVIDIA expands supply deals" in page
    assert "Micron shares slip before earnings" in body                  # a paragraph address finds its article
    assert '根拠の段落: "Micron shares fell 2% ahead of earnings.' in body      # and the program copies the paragraph
    assert re.search(r'根拠の段落: "NVIDIA said it signed new supply deals', body)
    assert "#2e7d32" in page and "#c62828" in page                       # US colors: green up, red down
    out = pathlib.Path(tmp_path) / "outlooks"
    assert (out / "2026-11-26.txt").read_text(encoding="utf-8") == body.replace("\r\n", "\n")


def test_a_search_that_cannot_be_asked_fails_the_run_instead_of_mailing_flat(news, proj, project_dir, smtp_server):
    news.server.fail = True
    collector = [call("news_search", {"company": "エヌビディア"}, "s1"), call("news_search", {"company": "エヌビディア"}, "s2"),
                 save(coverage={"items": [{"company": n, "status": "none", "note": "the search could not be made"} for n in ORDER]})]
    analyst = [lambda m: save(scan={"companies": [{"company": n, "focus": "関連記事なし"} for n in ORDER]})]
    analyst += [(lambda m, n=n: save(outlook={"items": [{"company": n, "direction": "flat", "reasons": []}]})) for n in ORDER]
    res = _run(proj, project_dir, FakeLLM({"collector": collector, "analyst": analyst}))
    assert not res.ok and "mail_outlook" in res.failed and "HTTP 500" in json.dumps(res.failed, ensure_ascii=False)
    assert smtp_server == []                                           # no "flat" mail went out


def test_second_run_stores_only_new_articles(news, proj, project_dir, smtp_server):
    fake = FakeLLM({"collector": _collector(), "analyst": _analyst(project_dir)})
    assert _run(proj, project_dir, fake).ok
    store = project_dir / "file_servers" / "news" / "store" / "items"
    assert len(list(store.glob("*.json"))) == 7

    ARTICLES["Micron"].append({"title": "Micron new news", "url": "https://www.cnbc.com/c/3",
                               "content": "Micron announced a new partnership today. Details were not shared.",
                               "published_date": "2026-11-25"})
    try:
        from tools import news_search          # the next day's search: the tool leaves out what is stored already
        ctx = {"files_dir": str(project_dir / "second_files"), "file_servers": views(proj, project_dir)}
        res = news_search.run(ctx, {"company": "エヌビディア"})
        assert res["articles"] == [] and res["skipped_known"] == 3           # two stored articles + the same page under another spelling
        res = news_search.run(ctx, {"company": "マイクロン"})
        assert [a["source"] for a in res["articles"]] == ["https://www.cnbc.com/c/3"] and res["skipped_known"] == 2
    finally:
        ARTICLES["Micron"].pop()


def test_the_flow_check_has_nothing_to_say(news, proj):
    from nextop.validate.precheck import check_project
    checked = check_project(proj, "daily_outlook")
    assert checked.errors == [], checked.errors
