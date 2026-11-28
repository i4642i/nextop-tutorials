"""What the program does without any model: dates, article files, the search tool (dedupe), the paragraph check and the mail."""
import datetime
import email
import email.policy
import importlib
import importlib.util
import socketserver
import threading

import pytest
from conftest import views
from nextop.validate import Sources


def test_next_trading_day_skips_the_weekend(news):
    d = datetime.date
    assert news.next_trading_day(d(2026, 11, 25)) == d(2026, 11, 26)        # Wednesday -> Thursday
    assert news.next_trading_day(d(2026, 11, 27)) == d(2026, 11, 30)        # Friday -> Monday
    assert news.next_trading_day(d(2026, 11, 28)) == d(2026, 11, 30)        # Saturday -> Monday


def test_clean_url_makes_spellings_one_address(news):
    assert news.clean_url("https://News.Example.com/a/1/?utm_source=x#top") == "https://news.example.com/a/1"
    assert news.clean_url("https://news.example.com/a/1") == news.clean_url("https://news.example.com/a/1/")
    assert news.clean_url("https://x.com/p?id=3&utm_medium=m") == "https://x.com/p?id=3"


def test_dates_are_written_as_year_month_day(news):
    assert news.day_of("Mon, 23 Nov 2026 06:38:47 GMT") == "2026-11-23"
    assert news.day_of("2026-11-23T06:38:47Z") == "2026-11-23"
    assert news.day_of("") == ""


def test_article_file_round_trip(news):
    text = news.article_text("Title", "2026-11-24", "https://x.com/a", "The text.")
    assert news.article_parts(text) == {"title": "Title", "date": "2026-11-24", "url": "https://x.com/a"}
    assert news.day_label(__import__("datetime").date(2026, 11, 26)) == "2026-11-26 (Thu)"


def test_search_tool_saves_articles_and_drops_a_repeated_address(news, proj, project_dir, tmp_path):
    tool = importlib.import_module("tools.news_search")
    res = tool.run({"files_dir": str(tmp_path / "f"), "file_servers": views(proj, project_dir)}, {"company": "NVIDIA"})
    assert [a["source"] for a in res["articles"]] == ["https://www.reuters.com/a/1", "https://www.cnbc.com/a/2"]
    assert res["skipped_known"] == 1                       # the third hit is the first one under another spelling
    saved = (tmp_path / "f" / res["articles"][0]["file"].replace("\\", "/").rsplit("/", 1)[-1]).read_text(encoding="utf-8")
    assert "URL: https://www.reuters.com/a/1" in saved and "signed new supply deals" in saved
    assert len(news.searches) == 1 and "NVIDIA" in news.searches[0]


def test_search_tool_leaves_out_social_media_pages(news, proj, project_dir, tmp_path):
    tool = importlib.import_module("tools.news_search")
    res = tool.run({"files_dir": str(tmp_path), "file_servers": views(proj, project_dir)}, {"company": "SpaceX"})
    assert [a["source"] for a in res["articles"]] == ["https://apnews.com/d/1"]       # no social media, no other sites
    assert news.blocked("https://www.instagram.com/p/abc", ["instagram.com"]) and not news.blocked("https://notx.com/a", ["x.com"])
    assert news.blocked("https://rumors.example.com/x", [], ["apnews.com"])
    assert not news.blocked("https://www.reuters.com/x", [], ["reuters.com"]) and not news.blocked("https://apnews.com/x", [], ["apnews.com"])


def test_the_search_asks_only_the_us_news_sites(news, proj, project_dir, tmp_path):
    tool = importlib.import_module("tools.news_search")
    tool.run({"files_dir": str(tmp_path), "file_servers": views(proj, project_dir)}, {"company": "Apple"})
    sent = news.bodies[-1]
    assert "reuters.com" in sent["include_domains"] and "instagram.com" in sent["exclude_domains"]


def _search(proj, project_dir, tmp_path, company="NVIDIA"):
    tool = importlib.import_module("tools.news_search")
    return tool.run({"files_dir": str(tmp_path), "file_servers": views(proj, project_dir)}, {"company": company})


def test_search_tool_reports_a_failed_search_as_an_error(news, proj, project_dir, tmp_path):
    news.server.fail = True
    res = _search(proj, project_dir, tmp_path)
    assert "error" in res and "Tavily" in res["error"] and "HTTP 500" in res["error"]
    assert [r["company"] for r in news.search_problems()] == ["NVIDIA"]          # recorded: the run must not end as "no news"


def test_search_tool_without_a_key_names_the_variable_and_the_file(news, proj, project_dir, tmp_path, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setattr(news, "read_env", lambda path: {})        # the test copy's .env holds a key
    res = _search(proj, project_dir, tmp_path)
    assert "TAVILY_API_KEY" in res["error"] and ".env" in res["error"]
    assert news.search_problems() and "TAVILY_API_KEY" in news.search_problems()[0]["problem"]


def test_search_tool_reports_a_timeout_and_an_unusable_answer(news, proj, project_dir, tmp_path, monkeypatch):
    import urllib.request

    def timeout(*a, **k):
        raise TimeoutError("timed out")
    monkeypatch.setattr(urllib.request, "urlopen", timeout)
    res = _search(proj, project_dir, tmp_path)
    assert "Tavily" in res["error"] and "timed out" in res["error"]


def test_a_connection_that_cannot_be_made_is_a_failure(news, monkeypatch):
    monkeypatch.setenv("TAVILY_URL", "http://127.0.0.1:1/search")             # nothing listens there
    with pytest.raises(OSError, match="Tavily"):
        news.tavily_search("x", 3, 5)


def test_an_answer_without_a_results_list_is_a_failure(news, monkeypatch):
    import io
    import urllib.request

    class Res(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Res(b'{"detail": "bad"}'))
    with pytest.raises(OSError, match="results"):
        news.tavily_search("x", 3, 5)


def test_an_answer_with_zero_articles_is_a_real_empty_result(news, proj, project_dir, tmp_path):
    assert news.tavily_search("no such company anywhere", 3, 5) == []
    news.note_search("NVIDIA", "an old problem")
    from conftest import ARTICLES
    saved = ARTICLES.pop("NVIDIA")
    try:
        res = _search(proj, project_dir, tmp_path)
    finally:
        ARTICLES["NVIDIA"] = saved
    assert res == {"company": "NVIDIA", "articles": [], "skipped_known": 0}
    assert news.search_problems() == []                  # the service answered: the old problem is gone


def test_the_start_refuses_a_missing_key_or_mail_setting_by_name(news, monkeypatch, smtp_server, tmp_path):
    plan = importlib.import_module("functions.plan")
    assert "error" not in plan.run({}, {"today": "2026-11-25"})
    monkeypatch.setenv("TAVILY_API_KEY", "")
    monkeypatch.setenv("SMTP_PASS", "")
    monkeypatch.setattr(news, "read_env", lambda path: {})        # the test copy's .env holds a key
    res = plan.run({}, {"today": "2026-11-25"})
    assert set(res) == {"error"} and "TAVILY_API_KEY" in res["error"] and "SMTP_PASS" in res["error"] and ".env" in res["error"]


def test_the_mail_is_not_made_when_a_search_failed(news, smtp_server):
    news.note_search("NVIDIA", "Tavily answered HTTP 500")
    mail = importlib.import_module("functions.mail_outlook")
    res = mail.run({}, {"plan/brief": {}, "collector/coverage": {"items": []}, "analyst/scan": {"companies": []},
                        "analyst/outlook": {"items": []}})
    assert set(res) == {"error"} and "NVIDIA" in res["error"] and "HTTP 500" in res["error"]
    assert smtp_server == []


def _checks(project_dir):
    spec = importlib.util.spec_from_file_location("analyst_checks", project_dir / "workers" / "analyst" / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _outlook(reasons, direction="up", company="NVIDIA"):
    return {"outlook": {"items": [{"company": company, "direction": direction, "reasons": reasons}]}}


ARTICLE = {                                   # what the file server gives for each address of one stored article
    "fs://news/001": "# NVIDIA expands supply\n\nDate: 2026-11-24\nURL: https://x\n\nNVIDIA said it will expand its chip supply.",
    "fs://news/001#1": "# NVIDIA expands supply\r\n\r\nDate: 2026-11-24\r\nURL: https://x\r\n\r\nNVIDIA said it will expand its chip supply.",
    "fs://news/001#1.1": "Date: 2026-11-24\nURL: https://x",
    "fs://news/001#1.2": "NVIDIA said it will expand its chip supply.",
}


def test_a_reason_must_cite_one_body_paragraph_of_an_article(project_dir):
    checks = _checks(project_dir)
    sources = Sources(ARTICLE.get)
    inputs = {"coverage": {"items": [{"company": "NVIDIA", "status": "thin", "note": "n"}]}}
    good = [{"point": "p", "source": "fs://news/001#1.2"}]
    assert checks.check_judge(_outlook(good), inputs, sources) == []
    assert checks.check_judge(_outlook([{"point": "p", "source": " fs://news/001#P1.2 "}]), inputs, sources) == []
    for source, said in (("fs://news/001", "whole article"), ("fs://news/001#1", "whole article or section"),
                         ("fs://news/001#1.1", "date and URL"), ("fs://news/099#1.2", "not a paragraph")):
        errors = checks.check_judge(_outlook([{"point": "p", "source": source}]), inputs, sources)
        assert len(errors) == 1 and said in errors[0] and source in errors[0], (source, errors)


def test_chinese_japanese_or_korean_letters_in_an_english_sentence_are_sent_back(project_dir):
    checks = _checks(project_dir)
    text = "NVIDIA said it will expand its chip supply."
    sources = Sources(lambda a: text)
    inputs = {"coverage": {"items": [{"company": "NVIDIA", "status": "thin", "note": "n"}]}}
    for slip in ("The unit's 单独 value rises.", "Supply \ud655\ub300 is good news.", "Demand is つよい."):
        errors = checks.check_judge(_outlook([{"point": slip, "source": "fs://news/001#1.2"}]), inputs, sources)
        assert len(errors) == 1 and "English only" in errors[0], slip
    scan = {"scan": {"companies": [{"company": "NVIDIA", "focus": "新闻 flow"}]}}
    assert any("新闻" in e for e in checks.check_scan(scan, {"brief": {"companies": [{"name": "NVIDIA"}]}}))
    good = [{"point": "More supply is good news — about 2% more.", "source": "fs://news/001#1.2"}]
    assert checks.check_judge(_outlook(good), inputs, sources) == []


def test_reason_counts_follow_the_collection_status(project_dir):
    checks = _checks(project_dir)
    text = "NVIDIA said it will expand its chip supply."
    sources = Sources(lambda a: text)
    one = [{"point": "p", "source": "fs://news/001#1.2"}]

    def cov(status):
        return {"coverage": {"items": [{"company": "NVIDIA", "status": status, "note": "n"}]}}

    assert checks.check_judge(_outlook(one), cov("ok"), sources) != []              # ok needs 2-3
    assert checks.check_judge(_outlook(one), cov("thin"), sources) == []
    assert checks.check_judge(_outlook([], "up"), cov("none"), sources) != []        # none: direction must be flat
    assert checks.check_judge(_outlook([], "flat"), cov("none"), sources) == []
    assert checks.check_judge(_outlook(one, "flat"), cov("none"), sources) != []     # none: no reasons


class MiniSMTP(socketserver.StreamRequestHandler):
    """Just enough SMTP (EHLO, AUTH, MAIL, RCPT, DATA, QUIT) to receive mail."""
    mails = []

    def handle(self):
        w = lambda s: self.wfile.write(s.encode() + b"\r\n")
        w("220 test ready")
        to = []
        while line := self.rfile.readline().decode("utf-8", "replace").rstrip("\r\n"):
            cmd = line.upper()
            if cmd.startswith("EHLO"):
                self.wfile.write(b"250-test\r\n250 AUTH PLAIN\r\n")
            elif cmd.startswith("AUTH"):
                w("235 ok")
            elif cmd.startswith("RCPT"):
                to.append(line.split(":", 1)[1].strip(" <>"))
                w("250 ok")
            elif cmd == "DATA":
                w("354 go")
                lines = []
                while (l := self.rfile.readline().decode("utf-8", "replace").rstrip("\r\n")) != ".":
                    lines.append(l)
                MiniSMTP.mails.append((to, "\n".join(lines)))
                w("250 queued")
            elif cmd == "QUIT":
                w("221 bye")
                return
            else:
                w("250 ok")


@pytest.fixture()
def smtp_server(monkeypatch):
    MiniSMTP.mails.clear()
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), MiniSMTP)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    for k, v in {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(server.server_address[1]), "SMTP_USER": "bot@example.com",
                 "SMTP_PASS": "pw", "OFFICE_EMAIL": "office@example.com", "MAIL_TO": "a@example.com,b@example.com",
                 "MAIL_TEST_MODE": "1"}.items():
        monkeypatch.setenv(k, v)
    yield MiniSMTP.mails
    server.shutdown()
    server.server_close()


def test_send_mail_carries_text_and_html(news, smtp_server):
    ok, note = news.send_mail("office@example.com", "[Stock outlook TEST] Subject ▲", "Body · café", "<p>Body <b>café</b></p>")
    assert ok, note
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"] and mail["Subject"] == "[Stock outlook TEST] Subject ▲"
    assert "Body · café" in mail.get_body(preferencelist=("plain",)).get_content()
    assert "<b>café</b>" in mail.get_body(preferencelist=("html",)).get_content()


def test_recipients_follow_the_test_mode(news, monkeypatch, smtp_server):
    assert news.recipients() == "office@example.com"
    monkeypatch.setenv("MAIL_TEST_MODE", "0")
    assert news.recipients() == "a@example.com,b@example.com"


def test_mail_without_setup_says_what_to_fill(news, monkeypatch):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        monkeypatch.setenv(k, "")
    ok, note = news.send_mail("x@example.com", "s", "t")
    assert not ok and "SMTP_HOST" in note


def _section(listed, direction="up"):
    return {"name": "Example Co" if not listed else "NVIDIA", "ticker": "" if not listed else "NVDA (Nasdaq)", "listed": listed,
            "direction": direction, "word": {True: {"up": "Up"}, False: {"up": "Mostly good news"}}[listed][direction],
            "focus": "Summary", "status": "ok", "reasons": []}


def test_mail_for_an_unlisted_company_says_there_is_no_share_price(news):
    mail = importlib.import_module("functions.mail_outlook")
    brief = {"target_day": "2026-11-26 (Thu)", "today": "2026-11-25 (Wed)"}
    text = mail.build_text(brief, [_section(False), _section(True)])
    assert "## Example Co · Mostly good news" in text and "Not a listed company, so there is no share price" in text
    assert text.count("Not a listed company") == 1          # only the unlisted company says it
    assert "## NVIDIA (NVDA (Nasdaq)) · Up" in text
    assert "left at Mixed or quiet with no reasons" in text and "left at Flat with no reasons" in text
    assert "Not a listed company, so there is no share price" in mail.build_html(brief, [_section(False)])


def test_a_paragraph_address_finds_its_article_and_the_program_copies_the_paragraph(news, tmp_path):
    mail = importlib.import_module("functions.mail_outlook")
    f = tmp_path / "a.md"
    f.write_text(news.article_text("Title", "2026-11-24", "https://x.com/a", "Text."), encoding="utf-8")
    row = {"address": "fs://news/003", "path": str(f), "parts": [        # what FILES_IN gives for one article
        {"address": "fs://news/003#1", "leaf": False},
        {"address": "fs://news/003#1.1", "leaf": True, "text": "Date: 2026-11-24\nURL: https://x.com/a"},
        {"address": "fs://news/003#1.2", "leaf": True, "text": "Text."}]}
    got = mail.article("fs://news/003#1.2", {"fs://news/003": row})
    assert (got["title"], got["date"], got["url"], got["quote"]) == ("Title", "2026-11-24", "https://x.com/a", "Text.")
    assert mail.article("fs://news/009#1.2", {"fs://news/003": row})["quote"] == ""


def test_titles_lose_stray_markup():
    from functions._news import clean_title
    assert clean_title("Nvidia <!-- -->Stock  <b>Rises</b>") == "Nvidia Stock Rises"
