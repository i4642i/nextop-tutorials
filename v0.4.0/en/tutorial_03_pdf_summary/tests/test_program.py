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
    assert got["parts"][1]["title"] == "1. Overview" and got["parts"][3]["rows"][0] == ["Quarter", "Visitors", "Loans", "Change vs 2025"]
    assert got["meta"]["pages"] == 2


def test_report_text_lists_sections_tables_and_figures():
    report = {"file": "r.pdf", "pages": 2, "counts": {"text": 1, "table": 1, "figure": 1},
              "sections": [{"address": "fs://pdf/001#2", "title": "Overview", "pages": "1", "characters": 40, "paragraphs": ["fs://pdf/001#2"]}],
              "tables": [{"address": "fs://pdf/001#3", "label": "table-1", "caption": "", "pages": "1", "rows": 3, "columns": 2, "header": ["a", "b"]}],
              "figures": [{"address": "fs://pdf/001#4", "label": "figure-1", "caption": "Figure 1. A chart", "pages": "2", "width": 800, "height": 400}]}
    text = _pdf.report_text(report)
    assert "1 text part · 1 table · 1 figure" in text and "1. Overview (page 1) · 40 characters" in text
    assert "table-1 (page 1) · 3 rows × 2 columns · columns: a | b" in text
    assert "Figure 1. A chart (page 2) · 800×400 pixels" in text


def test_no_font_says_what_to_do(monkeypatch, tmp_path):
    monkeypatch.setattr(_pdf, "FONT_CANDIDATES", [(str(tmp_path / "none.ttf"), str(tmp_path / "none-bold.ttf"))])
    monkeypatch.delenv("PDF_FONT", raising=False)
    monkeypatch.setattr(_pdf, "setting", lambda name, default="": "")
    with pytest.raises(OSError) as e:
        _pdf.find_font()
    assert "PDF_FONT" in str(e.value)


def test_a_font_named_in_the_settings_is_used(monkeypatch, tmp_path):
    font = tmp_path / "my.ttf"
    font.write_bytes(b"x")
    monkeypatch.setenv("PDF_FONT", str(font))
    assert _pdf.find_font() == (str(font), str(font))


def test_chinese_japanese_or_korean_letters_in_a_sentence_are_found():
    assert _pdf.cjk_errors("conclusion", "Visitors grew by 18% — a record.") == []
    for slip in ("Visitors 增加 a lot.", "Visitors \ub298\uc5c8\ub2e4.", "Visitors ふえた."):
        assert "write it again in English only" in _pdf.cjk_errors("conclusion", slip)[0], slip


def test_send_mail_carries_a_name_and_a_pdf(smtp_server):
    ok, note = _pdf.send_mail("office@example.com", "[PDF summary TEST] Subject · ×", "Body — café", [("summary_résumé.pdf", b"%PDF-1.4 test")])
    assert ok, note
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert mail["Subject"] == "[PDF summary TEST] Subject · ×" and "Body — café" in mail.get_body(preferencelist=("plain",)).get_content()
    pdf = next(mail.iter_attachments())
    assert pdf.get_filename() == "summary_résumé.pdf" and pdf.get_content() == b"%PDF-1.4 test"


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
