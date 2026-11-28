"""The whole flow (plan -> collector -> analyst -> mail) with a scripted model; search, store, quote check and mail run for real.

What is checked: the collector's uploads carry the company as a tag and an address seen before is not stored twice
(also across two runs), the analyst talks about one company at a time and sees only that company's articles, a
reason that cites a whole article instead of one of its paragraphs is refused and fixed, a listed company (SpaceX) gets a normal up/flat/down outlook,
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

ORDER = ["삼성전자", "SK하이닉스", "NVIDIA", "SpaceX"]


def _collector(statuses=None):
    """Search each company once, upload what the search returned (tagged with the company), then save the coverage."""
    steps = []
    for n, name in enumerate(ORDER):
        steps.append(call("news_search", {"company": name}, f"s{n}"))
        steps.append(lambda m, name=name: call("upload", {"to": "fs://news", "items": [
            {"file": a["file"], "title": a["title"], "source": a["source"], "tags": [name]}
            for a in last_tool_json(m)["articles"]]}, "u" + name))
    items = [{"company": n, "status": {"SpaceX": "thin", **(statuses or {})}.get(n, "ok"), "note": f"{n} 뉴스를 모았습니다."} for n in ORDER]
    steps.append(save(coverage={"items": items}))
    return steps


def _paragraphs(messages):
    """The paragraph addresses (fs://news/003#1.2) the last tool result gave, body paragraphs only."""
    got = last_tool_json(messages)
    return [x["address"] for x in got.get("passages") or [] if not x["text"].startswith("날짜:")]


def _analyst(project_dir, bad_source_for=None, fake_holder=None):
    """scan: one save. judge: per company ask each of its first two articles with query, then save citing a body
    paragraph of each (or, once, a whole article: refused, then saved again)."""
    fake_holder = {} if fake_holder is None else fake_holder
    def scan(m):
        return save(scan={"companies": [{"company": n, "focus": f"{n} 최근 뉴스 요약"} for n in ORDER]})

    def judge(name, direction):
        cited = []
        articles = 1 if name == "SpaceX" else 2              # the fake search keeps one SpaceX article (thin)

        def ask(k):
            def run(m):
                if k:
                    cited.extend(_paragraphs(m)[:1])
                return call("query", {"question": f"{name} 주가에 영향을 주는 소식", "address": addresses(m)[k]}, f"q{k}")
            return run

        def answer(m):
            if not fake_holder.get(name):                    # the paragraphs of the last query (not again on a retry)
                fake_holder[name] = True
                cited.extend(_paragraphs(m)[:1])
            reasons = [{"point": f"{name} 관련 기사에 근거한 이유", "source": a} for a in dict.fromkeys(cited)]
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
    fake = FakeLLM({"collector": _collector(), "analyst": _analyst(project_dir, "SK하이닉스", holder)})
    res = _run(proj, project_dir, fake)
    assert res.ok, res.failed

    assert len(news.searches) == 4                                  # one paid search per company
    store = project_dir / "file_servers" / "news" / "store" / "items"
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(store.glob("*.json"))]
    tags = {r["title"]: r.get("tags") for r in records}
    assert tags["삼성전자, HBM4 공급 확대"] == ["삼성전자"] and tags["SpaceX Starship test flight set"] == ["SpaceX"]
    assert len(records) == 2 + 2 + 2 + 1                            # the repeated address was never stored twice

    # the judge conversation for one company lists only that company's articles
    judge_calls = [m for who, m in fake.calls if who == "analyst" and "fs://news/003" in text_of(m)
                   and "fs://news/001" not in text_of(m)]                     # SK hynix's conversation: not Samsung's files
    assert judge_calls and "fs://news/005" not in text_of(judge_calls[0])

    # the reason that cited a whole article went back to the analyst once, asking for one of its paragraphs
    bad = [m for who, m in fake.calls if who == "analyst" and "cite one of its paragraphs" in text_of(m)]
    assert bad, "the paragraph check never refused anything"

    assert len(smtp_server) == 1
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"]
    assert mail["Subject"].startswith("[주가 전망·시험] 2026-11-26(목) 삼성전자 상승")
    assert "SpaceX 상승" in mail["Subject"] and "NVIDIA 하락" in mail["Subject"]
    body = mail.get_body(preferencelist=("plain",)).get_content()
    page = mail.get_body(preferencelist=("html",)).get_content()
    assert "투자 권유가 아닙니다 · 뉴스로 만든 전망입니다" in body and "투자 권유가 아닙니다 · 뉴스로 만든 전망입니다" in page
    assert "SPCX (NASDAQ)" in body and "비상장" not in body and "호재 중심" not in body      # SpaceX is listed: a normal outlook
    assert "https://news.example.com/a/1" in body and "utm_source" not in body       # the clean address, read by the program
    assert "https://news.example.com/c/1" in page and "삼성전자, HBM4 공급 확대" in page
    assert "NVIDIA shares slip before earnings" in body                  # a paragraph address finds its article
    assert '근거 문단: "NVIDIA shares fell 2% ahead of earnings.' in body      # and the program copies the paragraph
    assert re.search(r'근거 문단: "삼성전자가 HBM4 공급을 확대한다고 밝혔다\.', body)
    out = pathlib.Path(tmp_path) / "outlooks"
    assert (out / "2026-11-26.txt").read_text(encoding="utf-8") == body.replace("\r\n", "\n")


def test_a_search_that_cannot_be_asked_fails_the_run_instead_of_mailing_flat(news, proj, project_dir, smtp_server):
    news.server.fail = True
    collector = [call("news_search", {"company": "삼성전자"}, "s1"), call("news_search", {"company": "삼성전자"}, "s2"),
                 save(coverage={"items": [{"company": n, "status": "none", "note": "검색을 하지 못했습니다"} for n in ORDER]})]
    analyst = [lambda m: save(scan={"companies": [{"company": n, "focus": "관련 기사 없음"} for n in ORDER]})]
    analyst += [(lambda m, n=n: save(outlook={"items": [{"company": n, "direction": "flat", "reasons": []}]})) for n in ORDER]
    res = _run(proj, project_dir, FakeLLM({"collector": collector, "analyst": analyst}))
    assert not res.ok and "mail_outlook" in res.failed and "HTTP 500" in json.dumps(res.failed, ensure_ascii=False)
    assert smtp_server == []                                           # no "flat" mail went out


def test_second_run_stores_only_new_articles(news, proj, project_dir, smtp_server):
    fake = FakeLLM({"collector": _collector(), "analyst": _analyst(project_dir)})
    assert _run(proj, project_dir, fake).ok
    store = project_dir / "file_servers" / "news" / "store" / "items"
    assert len(list(store.glob("*.json"))) == 7

    ARTICLES["NVIDIA"].append({"title": "NVIDIA new news", "url": "https://news.example.com/c/3",
                               "content": "NVIDIA announced a new partnership today. Details were not shared.",
                               "published_date": "2026-11-25"})
    try:
        from tools import news_search          # the next day's search: the tool leaves out what is stored already
        ctx = {"files_dir": str(project_dir / "second_files"), "file_servers": views(proj, project_dir)}
        res = news_search.run(ctx, {"company": "삼성전자"})
        assert res["articles"] == [] and res["skipped_known"] == 3           # two stored articles + the same page under another spelling
        res = news_search.run(ctx, {"company": "NVIDIA"})
        assert [a["source"] for a in res["articles"]] == ["https://news.example.com/c/3"] and res["skipped_known"] == 2
    finally:
        ARTICLES["NVIDIA"].pop()


def test_the_flow_check_has_nothing_to_say(news, proj):
    from nextop.validate.precheck import check_project
    checked = check_project(proj, "daily_outlook")
    assert checked.errors == [], checked.errors
