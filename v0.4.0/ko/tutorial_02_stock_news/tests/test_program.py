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
    text = news.article_text("제목", "2026-11-24", "https://x.com/a", "본문입니다.")
    assert news.article_parts(text) == {"title": "제목", "date": "2026-11-24", "url": "https://x.com/a"}


def test_search_tool_saves_articles_and_drops_a_repeated_address(news, proj, project_dir, tmp_path):
    tool = importlib.import_module("tools.news_search")
    res = tool.run({"files_dir": str(tmp_path / "f"), "file_servers": views(proj, project_dir)}, {"company": "삼성전자"})
    assert [a["source"] for a in res["articles"]] == ["https://news.example.com/a/1", "https://news.example.com/a/2"]
    assert res["skipped_known"] == 1                       # the third hit is the first one under another spelling
    saved = (tmp_path / "f" / res["articles"][0]["file"].replace("\\", "/").rsplit("/", 1)[-1]).read_text(encoding="utf-8")
    assert "주소: https://news.example.com/a/1" in saved and "HBM4 공급을 확대한다고" in saved
    assert len(news.searches) == 1 and "삼성전자" in news.searches[0]


def test_search_tool_leaves_out_social_media_pages(news, proj, project_dir, tmp_path):
    tool = importlib.import_module("tools.news_search")
    res = tool.run({"files_dir": str(tmp_path), "file_servers": views(proj, project_dir)}, {"company": "SpaceX"})
    assert [a["source"] for a in res["articles"]] == ["https://news.example.com/d/1"]
    assert news.blocked("https://www.instagram.com/p/abc", ["instagram.com"]) and not news.blocked("https://notx.com/a", ["x.com"])


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
    news.note_search("NVIDIA", "Tavily 뉴스 검색이 HTTP 500 로 답했습니다")
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


def _outlook(reasons, direction="up", company="삼성전자"):
    return {"outlook": {"items": [{"company": company, "direction": direction, "reasons": reasons}]}}


ARTICLE = {                                   # what the file server gives for each address of one stored article
    "fs://news/001": "# 삼성전자, HBM4 공급 확대\n\n날짜: 2026-11-24\n주소: https://x\n\n삼성전자가 HBM4 공급을 확대한다고 밝혔다.",
    "fs://news/001#1": "# 삼성전자, HBM4 공급 확대\r\n\r\n날짜: 2026-11-24\r\n주소: https://x\r\n\r\n삼성전자가 HBM4 공급을 확대한다고 밝혔다.",
    "fs://news/001#1.1": "날짜: 2026-11-24\n주소: https://x",
    "fs://news/001#1.2": "삼성전자가 HBM4 공급을 확대한다고 밝혔다.",
}


def test_a_reason_must_cite_one_body_paragraph_of_an_article(project_dir):
    checks = _checks(project_dir)
    sources = Sources(ARTICLE.get)
    inputs = {"coverage": {"items": [{"company": "삼성전자", "status": "thin", "note": "n"}]}}
    good = [{"point": "p", "source": "fs://news/001#1.2"}]
    assert checks.check_judge(_outlook(good), inputs, sources) == []
    assert checks.check_judge(_outlook([{"point": "p", "source": " fs://news/001#P1.2 "}]), inputs, sources) == []
    for source, said in (("fs://news/001", "whole article"), ("fs://news/001#1", "whole article or section"),
                         ("fs://news/001#1.1", "date and address"), ("fs://news/099#1.2", "not a paragraph")):
        errors = checks.check_judge(_outlook([{"point": "p", "source": source}]), inputs, sources)
        assert len(errors) == 1 and said in errors[0] and source in errors[0], (source, errors)


def test_chinese_characters_in_a_korean_sentence_are_sent_back(project_dir):
    checks = _checks(project_dir)
    text = "삼성전자가 HBM4 공급을 확대한다고 밝혔다."
    sources = Sources(lambda a: text)
    inputs = {"coverage": {"items": [{"company": "삼성전자", "status": "thin", "note": "n"}]}}
    bad = [{"point": "사업부单独 가치가 오른다.", "source": "fs://news/001#1.2"}]
    errors = checks.check_judge(_outlook(bad), inputs, sources)
    assert len(errors) == 1 and "单独" in errors[0]
    scan = {"scan": {"companies": [{"company": "삼성전자", "focus": "新闻 흐름"}]}}
    assert any("新闻" in e for e in checks.check_scan(scan, {"brief": {"companies": [{"name": "삼성전자"}]}}))
    good = [{"point": "공급 확대가 호재다.", "source": "fs://news/001#1.2"}]
    assert checks.check_judge(_outlook(good), inputs, sources) == []


def test_reason_counts_follow_the_collection_status(project_dir):
    checks = _checks(project_dir)
    text = "삼성전자가 HBM4 공급을 확대한다고 밝혔다."
    sources = Sources(lambda a: text)
    one = [{"point": "p", "source": "fs://news/001#1.2"}]

    def cov(status):
        return {"coverage": {"items": [{"company": "삼성전자", "status": status, "note": "n"}]}}

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


def test_send_mail_carries_korean_text_and_html(news, smtp_server):
    ok, note = news.send_mail("office@example.com", "[주가 전망·시험] 제목", "본문 한글", "<p>본문 <b>한글</b></p>")
    assert ok, note
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"] and mail["Subject"] == "[주가 전망·시험] 제목"
    assert "본문 한글" in mail.get_body(preferencelist=("plain",)).get_content()
    assert "<b>한글</b>" in mail.get_body(preferencelist=("html",)).get_content()


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
    return {"name": "임시회사" if not listed else "삼성전자", "ticker": "" if not listed else "005930 (KOSPI)", "listed": listed,
            "direction": direction, "word": {True: {"up": "상승"}, False: {"up": "호재 중심"}}[listed][direction],
            "focus": "요약", "status": "ok", "reasons": []}


def test_mail_for_an_unlisted_company_says_there_is_no_share_price(news):
    mail = importlib.import_module("functions.mail_outlook")
    brief = {"target_day": "2026-11-26 (목)", "today": "2026-11-25 (수)"}
    text = mail.build_text(brief, [_section(False), _section(True)])
    assert "## 임시회사 · 호재 중심" in text and "비상장 회사라 주가가 없습니다" in text
    assert text.count("비상장") == 1                       # only the unlisted company says it
    assert "## 삼성전자 (005930 (KOSPI)) · 상승" in text
    assert "비상장 회사라 주가가 없습니다" in mail.build_html(brief, [_section(False)])


def test_a_paragraph_address_finds_its_article_and_the_program_copies_the_paragraph(news, tmp_path):
    mail = importlib.import_module("functions.mail_outlook")
    f = tmp_path / "a.md"
    f.write_text(news.article_text("제목", "2026-11-24", "https://x.com/a", "본문."), encoding="utf-8")
    row = {"address": "fs://news/003", "path": str(f), "parts": [        # what FILES_IN gives for one article
        {"address": "fs://news/003#1", "leaf": False},
        {"address": "fs://news/003#1.1", "leaf": True, "text": "날짜: 2026-11-24\n주소: https://x.com/a"},
        {"address": "fs://news/003#1.2", "leaf": True, "text": "본문."}]}
    got = mail.article("fs://news/003#1.2", {"fs://news/003": row})
    assert (got["title"], got["date"], got["url"], got["quote"]) == ("제목", "2026-11-24", "https://x.com/a", "본문.")
    assert mail.article("fs://news/009#1.2", {"fs://news/003": row})["quote"] == ""


def test_titles_lose_stray_markup():
    from functions._news import clean_title
    assert clean_title("Nvidia <!-- -->Stock  <b>Rises</b>") == "Nvidia Stock Rises"
