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


def _reader_check(project_dir):
    import importlib.util
    spec = importlib.util.spec_from_file_location("reader_checks", project_dir / "workers" / "reader" / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check


def _writer_check(project_dir):
    import importlib.util
    spec = importlib.util.spec_from_file_location("writer_checks", project_dir / "workers" / "writer" / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check


REQUEST = {"pages": [{"page": 1, "url": "https://a.example/1"}, {"page": 2, "url": "https://b.example/2"}],
           "report_file": "links_20261125-090000.md"}


def test_reader_check(links, project_dir):
    check = _reader_check(project_dir)
    good = {"notes": {"pages": [
        {"page": 1, "read": True, "title": "A", "points": ["One.", "Two.", "Three."], "problem": ""},
        {"page": 2, "read": False, "title": "", "points": [], "problem": "Access was blocked."}]}}
    assert check(good, {"request": REQUEST}) == []
    bad = {"notes": {"pages": [
        {"page": 1, "read": True, "title": "", "points": ["One.", "同行业"], "problem": ""},
        {"page": 1, "read": False, "title": "", "points": [], "problem": ""}]}}
    errors = check(bad, {"request": REQUEST})
    assert "notes.pages must hold page 1 exactly once; it holds it 2 times" in errors
    assert "notes.pages must hold page 2 exactly once; it holds it 0 times" in errors
    assert "notes.pages[0].title is empty; write the page's title" in errors
    assert "notes.pages[0].points has 2 points; write 3" in errors
    assert "notes.pages[1] was not read; write why in problem" in errors
    assert any("write it in English only" in e for e in errors)


def test_writer_check_reads_the_saved_file(links, project_dir):
    check = _writer_check(project_dir)
    out = {"report": {"file": REQUEST["report_file"], "headline": "Two pages in short"}}
    errors = check(out, {"request": REQUEST})
    assert errors == [f"the report {REQUEST['report_file']} is not saved yet; save it with filesystem__write_file "
                      f"(path = {REQUEST['report_file']!r})"]
    path = project_dir / "reports" / REQUEST["report_file"]
    path.write_text("# Link summary · 2000-01-01 (Sat)\nURL: https://a.example/1\n- \ud55c\uad6d\uc5b4\n", encoding="utf-8")
    errors = check(out, {"request": REQUEST})
    assert "the saved report lacks the address of page 2: https://b.example/2 (copy it word for word)" in errors
    assert any(e.startswith("the saved report lacks today's date") for e in errors)
    assert any(e.startswith("the saved report has Chinese, Japanese or Korean letters") for e in errors)
    today = links.today_seoul()
    path.write_text(f"# Link summary · {today}\n## 1. 東京ガイド\nURL: https://a.example/1\nURL: https://b.example/2\n",
                    encoding="utf-8")
    notes = {"pages": [{"page": 1, "title": "東京ガイド"}]}            # the letters of a page's own title are fine
    assert check(out, {"request": REQUEST, "notes": notes}) == []
    assert check({"report": {"file": "other.md", "headline": "x"}}, {"request": REQUEST, "notes": notes}) == [
        "report.file must be the request's report_file 'links_20261125-090000.md', not 'other.md'"]


def test_mail_sends_the_saved_file(links, project_dir, smtp_server):
    mail_report = importlib.import_module("functions.mail_report")
    (project_dir / "reports" / REQUEST["report_file"]).write_text("# Link summary\nURL: https://a.example/1\n", encoding="utf-8")
    out = mail_report.run({}, {"intake/request": REQUEST, "reader/notes": {"pages": [{"page": 1, "read": True, "title": "t", "points": ["a", "b", "c"], "problem": ""}]},
                               "writer/report": {"file": REQUEST["report_file"],
                                                                             "headline": "Two pages summed up"}})
    assert out == {"mail": {"sent": True, "to": "office@example.com", "note": "sent"}}
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"]
    assert mail["Subject"] == "[Link summary TEST] Two pages summed up (2 links)"
    body = mail.get_body(preferencelist=("plain",)).get_content()
    assert "URL: https://a.example/1" in body and f"reports/{REQUEST['report_file']}" in body
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
