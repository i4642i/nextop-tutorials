"""What the program does without any model: the sample PDF, table parsing, the report text, fonts, the A4 count and the mail."""
import email
import email.policy

import pytest
from conftest import call  # noqa: F401  (keeps the conftest import path)

from functions import _pdf


def test_the_sample_pdf_reads_into_text_table_and_figure_parts_in_order(sample_pdf):
    from nextop.parts.reader import pdf_text
    got = pdf_text.read(sample_pdf)
    kinds = [(p["kind"], p["pages"]) for p in got["parts"]]
    assert kinds == [("text", "1"), ("text", "1"), ("text", "1"), ("table", "1"), ("figure", "1"), ("text", "1"),
                     ("text", "2"), ("table", "2"), ("text", "2"), ("text", "2")]
    assert got["parts"][1]["title"] == "1. 개요" and got["parts"][3]["rows"][0] == ["분기", "방문자(명)", "대출(권)", "전년 대비"]
    assert got["meta"]["pages"] == 2


def test_report_text_lists_sections_tables_and_figures():
    report = {"file": "r.pdf", "pages": 2, "counts": {"text": 1, "table": 1, "figure": 1},
              "sections": [{"address": "fs://pdf/001#2", "title": "개요", "pages": "1", "characters": 40, "paragraphs": ["fs://pdf/001#2"]}],
              "tables": [{"address": "fs://pdf/001#3", "label": "table-1", "caption": "", "pages": "1", "rows": 3, "columns": 2, "header": ["a", "b"]}],
              "figures": [{"address": "fs://pdf/001#4", "label": "figure-1", "caption": "그림 1. 차트", "pages": "2", "width": 800, "height": 400}]}
    text = _pdf.report_text(report)
    assert "글 1개 · 표 1개 · 그림 1개" in text and "1. 개요 (쪽 1) · 40자" in text
    assert "table-1 (쪽 1) · 3행 × 2열 · 열: a | b" in text and "그림 1. 차트 (쪽 2) · 800×400 픽셀" in text


def test_no_korean_font_says_what_to_do(monkeypatch, tmp_path):
    monkeypatch.setattr(_pdf, "FONT_CANDIDATES", [(str(tmp_path / "none.ttf"), str(tmp_path / "none-bold.ttf"))])
    monkeypatch.delenv("KOREAN_FONT", raising=False)
    monkeypatch.setattr(_pdf, "setting", lambda name, default="": "")
    with pytest.raises(OSError) as e:
        _pdf.find_font()
    assert "KOREAN_FONT" in str(e.value)


def test_a_font_named_in_the_settings_is_used(monkeypatch, tmp_path):
    font = tmp_path / "my.ttf"
    font.write_bytes(b"x")
    monkeypatch.setenv("KOREAN_FONT", str(font))
    assert _pdf.find_font() == (str(font), str(font))


def test_chinese_characters_in_a_sentence_are_found():
    assert _pdf.han_errors("title", "방문자가 늘었다") == []
    assert "Chinese characters" in _pdf.han_errors("title", "방문자가 增加했다")[0]


def test_send_mail_carries_a_korean_name_and_a_pdf(smtp_server):
    ok, note = _pdf.send_mail("office@example.com", "[PDF 요약·시험] 제목", "본문 한글", [("요약_파일.pdf", b"%PDF-1.4 test")])
    assert ok, note
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert mail["Subject"] == "[PDF 요약·시험] 제목" and "본문 한글" in mail.get_body(preferencelist=("plain",)).get_content()
    pdf = next(mail.iter_attachments())
    assert pdf.get_filename() == "요약_파일.pdf" and pdf.get_content() == b"%PDF-1.4 test"


def test_recipients_follow_the_test_mode(monkeypatch, smtp_server):
    assert _pdf.recipients() == "office@example.com"
    monkeypatch.setenv("MAIL_TEST_MODE", "0")
    assert _pdf.recipients() == "a@example.com,b@example.com"


def test_mail_without_setup_says_what_to_fill(monkeypatch):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"):
        monkeypatch.setenv(k, "")
    monkeypatch.setattr(_pdf, "ROOT", _pdf.ROOT / "nowhere")        # no .env to fall back on
    ok, note = _pdf.send_mail("x@example.com", "s", "t")
    assert not ok and "SMTP_HOST" in note


def test_intake_refuses_a_missing_or_wrong_file(project_dir, monkeypatch, tmp_path):
    import importlib
    import sys
    monkeypatch.syspath_prepend(str(project_dir))
    for name in [m for m in sys.modules if m == "functions" or m.startswith("functions.")]:
        del sys.modules[name]
    intake = importlib.import_module("functions.intake")
    assert "existing .pdf" in intake.run({}, {"pdf_path": str(tmp_path / "nope.pdf")})["error"]
    other = tmp_path / "notes.txt"
    other.write_text("x")
    assert "existing .pdf" in intake.run({}, {"pdf_path": str(other)})["error"]


def test_a_mail_server_that_cannot_be_reached_is_named(monkeypatch, smtp_server):
    monkeypatch.setenv("SMTP_PORT", "1")                               # nothing listens there
    ok, note = _pdf.send_mail("office@example.com", "s", "t")
    assert not ok and "SMTP" in note and "127.0.0.1:1" in note


def test_intake_refuses_missing_mail_settings_by_name(project_dir, monkeypatch, sample_pdf):
    import importlib
    import sys
    monkeypatch.syspath_prepend(str(project_dir))
    for name in [m for m in sys.modules if m == "functions" or m.startswith("functions.")]:
        del sys.modules[name]
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    intake = importlib.import_module("functions.intake")
    out = intake.run({}, {"pdf_path": str(sample_pdf)})
    assert set(out) == {"error"} and all(k in out["error"] for k in ("SMTP_HOST", "SMTP_PASS", "OFFICE_EMAIL")) and ".env" in out["error"]
