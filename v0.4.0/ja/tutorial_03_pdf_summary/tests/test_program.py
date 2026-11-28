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
    assert got["parts"][1]["title"] == "1. 概要" and got["parts"][3]["rows"][0] == ["四半期", "来館者（人）", "貸出（冊）", "前年比"]
    assert got["parts"][3]["caption"] == "表1. 四半期ごとの来館者数と貸出冊数"
    assert got["meta"]["pages"] == 2


def test_report_text_lists_sections_tables_and_figures():
    report = {"file": "r.pdf", "pages": 2, "counts": {"text": 1, "table": 1, "figure": 1},
              "sections": [{"address": "fs://pdf/001#2", "title": "概要", "pages": "1", "characters": 40, "paragraphs": ["fs://pdf/001#2"]}],
              "tables": [{"address": "fs://pdf/001#3", "label": "table-1", "caption": "", "pages": "1", "rows": 3, "columns": 2, "header": ["a", "b"]}],
              "figures": [{"address": "fs://pdf/001#4", "label": "figure-1", "caption": "図1. グラフ", "pages": "2", "width": 800, "height": 400}]}
    text = _pdf.report_text(report)
    assert "本文 1 · 表 1 · 図 1" in text and "1. 概要（1 ページ）· 40 文字" in text
    assert "table-1（1 ページ）· 3 行 × 2 列 · 列: a | b" in text
    assert "図1. グラフ（2 ページ）· 800×400 ピクセル" in text


def test_no_font_says_what_to_do(monkeypatch, tmp_path):
    monkeypatch.setattr(_pdf, "FONT_CANDIDATES", [(str(tmp_path / "none.ttf"), str(tmp_path / "none-bold.ttf"))])
    monkeypatch.delenv("JAPANESE_FONT", raising=False)
    monkeypatch.setattr(_pdf, "setting", lambda name, default="": "")
    with pytest.raises(OSError) as e:
        _pdf.find_font()
    assert "JAPANESE_FONT" in str(e.value)


def test_a_font_named_in_the_settings_is_used(monkeypatch, tmp_path):
    font = tmp_path / "my.ttf"
    font.write_bytes(b"x")
    monkeypatch.setenv("JAPANESE_FONT", str(font))
    assert _pdf.find_font() == (str(font), str(font))


def test_korean_chinese_or_english_in_a_sentence_is_found():
    assert _pdf.language_errors("conclusion", "来館者は前年より18%増え、過去最多になりました。") == []
    assert _pdf.language_errors("conclusion", "Transformer は注意機構だけを使うモデルです。") == []
    assert _pdf.language_errors("conclusion", "12,400人") == []                  # short: a number, a name
    for slip, why in (("来館者が大きく늘었다。とても多いです。", "Korean letters"),
                      ("来館者数は前年より増えました。这是记录。", "Chinese characters that Japanese does not use"),
                      ("访问人数比去年增加了十八个百分点", "no hiragana or katakana"),
                      ("Visitors grew by 18 percent this year.", "no hiragana or katakana")):
        errors = _pdf.language_errors("conclusion", slip)
        assert errors and why in " ".join(errors), slip


def test_send_mail_carries_a_name_and_a_pdf(smtp_server):
    ok, note = _pdf.send_mail("office@example.com", "[PDF要約・テスト] 件名 · ×", "本文 — カフェ", [("要約_報告書.pdf", b"%PDF-1.4 test")])
    assert ok, note
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert mail["Subject"] == "[PDF要約・テスト] 件名 · ×" and "本文 — カフェ" in mail.get_body(preferencelist=("plain",)).get_content()
    pdf = next(mail.iter_attachments())
    assert pdf.get_filename() == "要約_報告書.pdf" and pdf.get_content() == b"%PDF-1.4 test"


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
