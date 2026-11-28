"""The program parts without a model: reading the links, the two workers' checks, the mail."""
import email
import email.policy
import importlib


def test_parse_links(links):
    got, problems = links.parse_links("https://a.example/x\n https://b.example/y, https://a.example/x")
    assert got == ["https://a.example/x", "https://b.example/y"] and problems == []
    assert links.parse_links("")[1] == ["give 1 to 3 web addresses, one per line"]
    assert links.parse_links("www.example.com")[1] == ["not a web address (http:// or https://): www.example.com"]
    assert links.parse_links("\n".join(f"https://e.example/{i}" for i in range(4)))[1] == [
        "give at most 3 web addresses; got 4"]


def test_intake_numbers_pages_and_names_the_report(links, smtp_server):
    intake = importlib.import_module("functions.intake")
    out = intake.run({}, {"links": "https://a.example/1\nhttps://b.example/2"})["request"]
    assert out["pages"] == [{"page": 1, "url": "https://a.example/1"}, {"page": 2, "url": "https://b.example/2"}]
    assert out["report_file"].startswith("links_") and out["report_file"].endswith(".md")
    assert "error" in intake.run({}, {"links": "not a link"})


def test_intake_refuses_missing_mail_settings_by_name(links, monkeypatch):
    intake = importlib.import_module("functions.intake")
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(links, "ROOT", links.ROOT / "no_env_here")
    out = intake.run({}, {"links": "https://a.example/1"})
    assert set(out) == {"error"} and all(k in out["error"] for k in ("SMTP_HOST", "SMTP_PASS", "OFFICE_EMAIL")) and ".env" in out["error"]


def _load_check(project_dir, worker):
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"{worker}_checks", project_dir / "workers" / worker / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check


REQUEST = {"pages": [{"page": 1, "url": "https://a.example/1"}, {"page": 2, "url": "https://b.example/2"}],
           "report_file": "links_20261125-090000.md"}


def test_japanese_check(links):
    assert links.japanese_errors("x", "MCPはオープンな標準です。写真や学校、机、将来の話も書けます。") == []
    assert links.japanese_errors("x", "这是一个开放标准") == [
        "x has simplified Chinese characters (个开这); write it in Japanese only",
        "x is not Japanese (no hiragana or katakana); write it in Japanese"]
    assert links.japanese_errors("x", "An open standard") == [
        "x is not Japanese (no hiragana or katakana); write it in Japanese"]
    assert links.japanese_errors("x", "한국어です") == [
        "x has Korean letters (국어한); write it in Japanese only"]
    assert links.japanese_errors("x", "") == []


def test_reader_check(links, project_dir):
    check = _load_check(project_dir, "reader")
    good = {"notes": {"pages": [
        {"page": 1, "read": True, "title": "A", "points": ["一つ目です。", "二つ目です。", "三つ目です。"], "problem": ""},
        {"page": 2, "read": False, "title": "", "points": [], "problem": "アクセスが拒否されました。"}]}}
    assert check(good, {"request": REQUEST}) == []
    bad = {"notes": {"pages": [
        {"page": 1, "read": True, "title": "", "points": ["一つ目です。", "这是同行业"], "problem": ""},
        {"page": 1, "read": False, "title": "", "points": [], "problem": ""}]}}
    errors = check(bad, {"request": REQUEST})
    assert "notes.pages must hold page 1 exactly once; it holds it 2 times" in errors
    assert "notes.pages must hold page 2 exactly once; it holds it 0 times" in errors
    assert "notes.pages[0].title is empty; write the page's title" in errors
    assert "notes.pages[0].points has 2 points; write 3" in errors
    assert "notes.pages[1] was not read; write why in problem" in errors
    assert "notes.pages[0].points[1] has simplified Chinese characters (业这); write it in Japanese only" in errors
    assert "notes.pages[0].points[1] is not Japanese (no hiragana or katakana); write it in Japanese" in errors


def test_writer_check_reads_the_saved_file(links, project_dir):
    check = _load_check(project_dir, "writer")
    out = {"report": {"file": REQUEST["report_file"], "headline": "2ページを短くまとめました"}}
    errors = check(out, {"request": REQUEST})
    assert errors == [f"the report {REQUEST['report_file']} is not saved yet; save it with filesystem__write_file "
                      f"(path = {REQUEST['report_file']!r})"]
    path = project_dir / "reports" / REQUEST["report_file"]
    path.write_text("# リンク要約 · 2000-01-01 (土)\nアドレス: https://a.example/1\n- 한국어\n", encoding="utf-8")
    errors = check(out, {"request": REQUEST})
    assert "the saved report lacks the address of page 2: https://b.example/2 (copy it word for word)" in errors
    assert any(e.startswith("the saved report lacks today's date") for e in errors)
    assert any(e.startswith("the saved report has Korean letters") for e in errors)
    today = links.today_seoul()
    path.write_text(f"# リンク要約 · {today}\n## 1. 东京导游指南\nアドレス: https://a.example/1\nアドレス: https://b.example/2\n",
                    encoding="utf-8")
    notes = {"pages": [{"page": 1, "title": "东京导游指南"}]}        # the letters of a page's own title are fine
    assert check(out, {"request": REQUEST, "notes": notes}) == []
    assert any("simplified Chinese characters" in e for e in check(out, {"request": REQUEST}))   # but not elsewhere
    assert check({"report": {"file": "other.md", "headline": "まとめ"}}, {"request": REQUEST, "notes": notes}) == [
        "report.file must be the request's report_file 'links_20261125-090000.md', not 'other.md'"]


def test_mail_sends_the_saved_file(links, project_dir, smtp_server):
    mail_report = importlib.import_module("functions.mail_report")
    (project_dir / "reports" / REQUEST["report_file"]).write_text("# リンク要約\nアドレス: https://a.example/1\n",
                                                                  encoding="utf-8")
    out = mail_report.run({}, {"intake/request": REQUEST, "reader/notes": {"pages": [{"page": 1, "read": True, "title": "t", "points": ["a", "b", "c"], "problem": ""}]},
                               "writer/report": {"file": REQUEST["report_file"],
                                                                             "headline": "2ページをまとめました"}})
    assert out == {"mail": {"sent": True, "to": "office@example.com", "note": "sent"}}
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"]
    assert mail["Subject"] == "[リンク要約・テスト] 2ページをまとめました（リンク2件）"
    body = mail.get_body(preferencelist=("plain",)).get_content()
    assert "アドレス: https://a.example/1" in body and f"reports/{REQUEST['report_file']}" in body
    files = list(mail.iter_attachments())
    assert [f.get_filename() for f in files] == [REQUEST["report_file"]]
    assert "https://a.example/1" in files[0].get_content()


READ = {"pages": [{"page": 1, "read": True, "title": "t", "points": ["a", "b", "c"], "problem": ""},
                  {"page": 2, "read": False, "title": "", "points": [], "problem": "HTTP 404"}]}


def _mail_inputs(notes=READ):
    return {"intake/request": REQUEST, "reader/notes": notes, "writer/report": {"file": REQUEST["report_file"], "headline": "x"}}


def test_mail_failure_fails_the_block_with_the_reason(links, project_dir, monkeypatch):
    mail_report = importlib.import_module("functions.mail_report")
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(links, "ROOT", links.ROOT / "no_env_here")
    (project_dir / "reports" / REQUEST["report_file"]).write_text("# report", encoding="utf-8")
    out = mail_report.run({}, _mail_inputs())
    assert set(out) == {"error"} and "SMTP_HOST" in out["error"] and ".env" in out["error"]
    (project_dir / "reports" / REQUEST["report_file"]).unlink()
    out = mail_report.run({}, _mail_inputs())
    assert set(out) == {"error"} and "reports/" in out["error"]


def test_a_mail_server_that_cannot_be_reached_fails_the_block(links, project_dir, smtp_server, monkeypatch):
    mail_report = importlib.import_module("functions.mail_report")
    monkeypatch.setenv("SMTP_PORT", "1")                               # nothing listens there
    (project_dir / "reports" / REQUEST["report_file"]).write_text("# report", encoding="utf-8")
    out = mail_report.run({}, _mail_inputs())
    assert set(out) == {"error"} and "SMTP" in out["error"] and "127.0.0.1:1" in out["error"]


def test_no_page_read_fails_the_block(links, project_dir, smtp_server):
    mail_report = importlib.import_module("functions.mail_report")
    (project_dir / "reports" / REQUEST["report_file"]).write_text("# report", encoding="utf-8")
    none = {"pages": [{"page": 1, "read": False, "title": "", "points": [], "problem": "fetch: HTTP 404"},
                      {"page": 2, "read": False, "title": "", "points": [], "problem": "timed out"}]}
    out = mail_report.run({}, _mail_inputs(none))
    assert set(out) == {"error"} and "HTTP 404" in out["error"] and smtp_server == []
