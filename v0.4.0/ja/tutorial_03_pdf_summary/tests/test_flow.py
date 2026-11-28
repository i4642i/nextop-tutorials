"""The whole flow (intake -> classify -> summarizer -> deliver) with a scripted model.

Reading the PDF into parts and paragraphs, the classification, the paragraph and quote checks, the A4 check, the PDF
and the mail run for real.
"""
import email
import email.policy
import io  # noqa

import pytest
from conftest import FakeLLM, adapters, call, save, text_of
from nextop.runtime.flow import run_flow

from functions._pdf import page_count

# Addresses of the sample PDF: the document fs://pdf/001, its parts in document order (#1 ... #10), and the paragraphs
# of a section of more than one paragraph (#3.1, #3.2); a section of one paragraph is its own paragraph
DOC = "fs://pdf/001"
TITLE, INTRO, USE, TABLE1, FIGURE1, CAPTION1, SATISFACTION, TABLE2, TASKS, CONCLUSION = (f"{DOC}#{n}" for n in range(1, 11))
USE_1 = USE + ".1"


def summary(point_text="それが要点です。", **change):
    s = {
        "title": "ほしあかり町図書館 2026年 利用状況報告書",
        "key_points": [
            {"point": "来館者数と貸出冊数がともに増えました。", "source": INTRO,
             "quote": "ほしあかり町図書館では、2026年の一年間で来館者数と貸出冊数がともに増えた。"},
            {"point": f"年間の来館者数は12,400人でした。{point_text}", "source": USE_1,
             "quote": "年間の来館者数は合計12,400人で、前年より18パーセント増えた。"},
            {"point": "平日の開館時間を延ばしてほしいという要望が多くありました。", "source": TASKS,
             "quote": "平日の開館時間を1時間延ばしてほしいという要望が多く寄せられた"},
        ],
        "tables": [
            {"source": TABLE1, "line": "来館者数と貸出冊数は第3四半期に最も大きく伸びました。", "rows": []},
            {"source": TABLE2, "line": "読み聞かせの会の満足度が最も高くなっています。", "rows": [1, 2]},
        ],
        "figures": [{"figure": FIGURE1, "line": "10月の来館者数が最も多くなっています。"}],
        "conclusion": "来年は平日の開館時間を延ばし、シニア向けスマホ教室をもう1クラス開く予定です。",
    }
    s.update(change)
    return s


def _run(proj, sample_pdf, steps):
    fake = FakeLLM(steps)
    res = run_flow(proj, "pdf_summary", {"pdf_path": str(sample_pdf)}, adapters=adapters(fake))
    return res, fake


def _open_then_save(*saves):
    return [call("get", {"address": USE}), *[save(summary=s) for s in saves]]


def test_whole_flow_classifies_summarizes_and_mails(proj, sample_pdf, smtp_server, tmp_path):
    res, fake = _run(proj, sample_pdf, _open_then_save(summary()))
    assert res.ok, res.failed

    report = res.outputs["classify"]["report"]
    assert report["counts"] == {"text": 7, "table": 2, "figure": 1} and report["pages"] == 2
    assert report["sections"][2]["paragraphs"] == [USE_1, USE + ".2"] and report["sections"][1]["paragraphs"] == [INTRO]
    assert [t["address"] for t in report["tables"]] == [TABLE1, TABLE2]
    assert report["tables"][0]["caption"] == "表1. 四半期ごとの来館者数と貸出冊数"
    assert (report["tables"][0]["rows"], report["tables"][0]["columns"], report["tables"][0]["pages"]) == (5, 4, "1")
    assert report["tables"][1]["header"] == ["催し", "参加（人）", "満足度"]
    assert report["figures"][0]["caption"].startswith("図1.") and report["figures"][0]["width"] > 100
    assert [s["pages"] for s in report["sections"]] == ["1", "1", "1", "1", "2", "2", "2"]

    assert len(smtp_server) == 1
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"]
    assert mail["Subject"] == "[PDF要約・テスト] sample_report.pdf の A4 要約（本文 7、表 2、図 1）"
    body = mail.get_body(preferencelist=("plain",)).get_content()
    assert "表1. 四半期ごとの来館者数と貸出冊数（1 ページ）· 5 行 × 4 列" in body
    assert "本文 7 · 表 2 · 図 1" in body
    pdfs = [p for p in mail.iter_attachments() if p.get_content_type() == "application/pdf"]
    assert len(pdfs) == 1 and pdfs[0].get_filename() == "要約_sample_report.pdf"
    data = pdfs[0].get_content()
    assert page_count(data) == 1
    saved = tmp_path / "out" / "summaries" / "sample_report_summary.pdf"
    assert saved.read_bytes() == data

    import pypdfium2
    with pypdfium2.PdfDocument(data) as doc:                        # the page numbers come from the program, not the model
        page = doc[0].get_textpage().get_text_range()
    assert "出典: 1 ページ · 2. 利用状況" in page and "出典: 2 ページ · 4. 改善課題" in page
    assert "表1. 四半期ごとの来館者数と貸出冊数" in page and "（1 ページ）" in page
    assert "要点" in page and "結論" in page
    # the chosen table is drawn from table.rows (every cell of table 1), the picture is the figure part's image
    assert all(cell in page for row in report["tables"][0]["cells"] for cell in row)
    assert "5,900" in page and "+27%" in page
    assert "表の一部: 4 行中 2 行" in page and "4.7" in page and "4.4" not in page    # table 2: header + row 2 only
    assert "子ども作文教室" not in page and "読み聞かせの会" in page
    with pypdfium2.PdfDocument(data) as doc:
        images = [o for o in doc[0].get_objects() if o.type == pypdfium2.raw.FPDF_PAGEOBJ_IMAGE]
    assert len(images) == 1
    assert report["figures"][0]["image"].endswith(".png")


def test_a_changed_quote_is_refused_then_fixed(proj, sample_pdf, smtp_server):
    bad = summary()
    bad["key_points"][0]["quote"] = "ほしあかり町図書館では、2026年の一年間で来館者数と貸出冊数がとても増えた。"      # one word changed
    res, fake = _run(proj, sample_pdf, _open_then_save(bad, summary()))
    assert res.ok, res.failed
    later = text_of(fake.calls[-1])
    assert "引用が見つかりません" in later and "とても増えた" in later       # the refusal (language pack ja) reached the model
    assert len(smtp_server) == 1


def test_a_quote_across_a_line_break_of_the_page_passes(proj, sample_pdf, smtp_server):
    s = summary()
    s["key_points"][0]["quote"] = "本報告書では、四半期ごとの利用状況、月ごとの来館者数"       # "四\n半期" in the PDF's text
    res, fake = _run(proj, sample_pdf, _open_then_save(s))
    assert res.ok, res.failed
    assert len(fake.calls) == 2 and len(smtp_server) == 1                  # passed at the first save


def test_a_sentence_that_is_not_japanese_is_refused_then_fixed(proj, sample_pdf, smtp_server):
    bad = summary(conclusion="Next year the library will stay open longer.")
    res, fake = _run(proj, sample_pdf, _open_then_save(bad, summary()))
    assert res.ok, res.failed
    assert "no hiragana or katakana" in text_of(fake.calls[-1]) and len(smtp_server) == 1


def test_a_summary_longer_than_one_page_is_refused_then_shortened(proj, sample_pdf, smtp_server):
    long = summary(point_text="とても長い説明が続きます。" * 300)
    res, fake = _run(proj, sample_pdf, _open_then_save(long, summary()))
    assert res.ok, res.failed
    later = text_of(fake.calls[-1])
    assert "does not fit one A4 page" in later and "spill past page 1" in later
    assert len(smtp_server) == 1                                    # only the shortened one was mailed
    mail = email.message_from_string(smtp_server[0][1], policy=email.policy.default)
    data = next(mail.iter_attachments()).get_content()
    assert page_count(data) == 1 and b"\xec" not in b""             # one page


def test_a_whole_section_as_a_source_is_refused_then_its_paragraph_is_cited(proj, sample_pdf, smtp_server):
    bad = summary()
    bad["key_points"][1]["source"] = USE                                       # the section, not its paragraph
    res, fake = _run(proj, sample_pdf, _open_then_save(bad, summary()))
    assert res.ok, res.failed
    later = text_of(fake.calls[-1])
    assert "is a whole section" in later and USE_1 in later and len(smtp_server) == 1


def test_a_table_that_is_not_in_the_report_is_refused(proj, sample_pdf, smtp_server):
    wrong = summary(tables=[{"source": USE, "line": "これは本文の部分です。", "rows": []}])      # a text part, not a table
    res, fake = _run(proj, sample_pdf, _open_then_save(wrong, summary()))
    assert res.ok and "is not one of the report's tables" in text_of(fake.calls[-1])


def test_no_table_and_no_figure_is_allowed(proj, sample_pdf, smtp_server):
    res, fake = _run(proj, sample_pdf, _open_then_save(summary(tables=[], figures=[])))
    assert res.ok, res.failed
    mail = email.message_from_string(smtp_server[0][1], policy=email.policy.default)
    assert page_count(next(mail.iter_attachments()).get_content()) == 1 and len(fake.calls) == 2


class _Sources:
    def __init__(self, text):
        self._text = text

    def text(self, address):
        return self._text


def _png(tmp_path, w=900, h=900):
    from PIL import Image
    path = tmp_path / "fig.png"
    Image.new("RGB", (w, h), (200, 220, 240)).save(path)
    return str(path)


def _big_report(tmp_path):
    cells = [[f"h{c}" for c in range(6)]] + [[f"r{r}c{c}" for c in range(6)] for r in range(1, 20)]
    tables = [{"address": f"fs://pdf/001#{n}", "label": f"Table {n}", "caption": f"Table {n}. Big", "pages": "1", "rows": 20, "columns": 6,
               "header": cells[0], "cells": cells} for n in (2, 3)]
    figures = [{"address": f"fs://pdf/001#{n}", "label": f"Figure {n}", "caption": f"Figure {n}. Tall", "pages": "1", "width": 900,
                "height": 900, "image": _png(tmp_path)} for n in (4, 5)]
    return {"file": "x.pdf", "pages": 1, "counts": {"text": 1, "table": 2, "figure": 2},
            "sections": [{"address": "fs://pdf/001#1", "title": "T", "pages": "1", "characters": 10, "paragraphs": ["fs://pdf/001#1"]}],
            "tables": tables, "figures": figures}


def _summary_for(report, tables, figures):
    return {"title": "T", "key_points": [{"point": "要点です。", "source": "fs://pdf/001#1", "quote": "q"}] * 3,
            "tables": tables, "figures": figures, "conclusion": "以上です。"}


def test_choosing_too_much_is_refused_by_the_page_check(tmp_path, project_dir, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("checks_t3", project_dir / "workers" / "summarizer" / "checks.py")
    monkeypatch.syspath_prepend(str(project_dir))
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    report = _big_report(tmp_path)
    rows = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    both = _summary_for(report, [{"source": t["address"], "line": "表です。", "rows": rows} for t in report["tables"]],
                        [{"figure": f["address"], "line": "図です。"} for f in report["figures"]])
    errors = checks.check({"summary": both}, {"report": report}, _Sources("q"))
    assert any("does not fit one A4 page" in e and "choose fewer tables or figures" in e for e in errors), errors
    one = _summary_for(report, [{"source": report["tables"][0]["address"], "line": "表です。", "rows": [1, 2, 3]}],
                       [{"figure": report["figures"][0]["address"], "line": "図です。"}])
    assert checks.check({"summary": one}, {"report": report}, _Sources("q")) == []        # fewer choices fit


def test_a_big_table_needs_row_numbers_and_a_wide_one_is_refused(tmp_path, project_dir, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("checks_t3b", project_dir / "workers" / "summarizer" / "checks.py")
    monkeypatch.syspath_prepend(str(project_dir))
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    report = _big_report(tmp_path)
    t0 = report["tables"][0]["address"]
    errors = checks.check({"summary": _summary_for(report, [{"source": t0, "line": "表です。", "rows": []}], [])}, {"report": report}, _Sources("q"))
    assert any("has 20 rows" in e and "Give the numbers of the rows" in e for e in errors)
    errors = checks.check({"summary": _summary_for(report, [{"source": t0, "line": "表です。", "rows": [1, 99]}], [])}, {"report": report}, _Sources("q"))
    assert any("outside 1..20" in e for e in errors)
    report["tables"][1].update(columns=39)
    errors = checks.check({"summary": _summary_for(report, [{"source": report["tables"][1]["address"], "line": "表です。", "rows": [1, 2]}], [])},
                          {"report": report}, _Sources("q"))
    assert any("39 columns" in e and "cannot be drawn" in e for e in errors)


def test_deliver_refuses_to_mail_more_than_one_page(project_dir, smtp_server, sample_pdf, monkeypatch):
    import importlib
    import sys
    monkeypatch.syspath_prepend(str(project_dir))
    for name in [m for m in sys.modules if m in ("functions",) or m.startswith("functions.")]:
        del sys.modules[name]
    deliver = importlib.import_module("functions.deliver")
    report = {"file": "x.pdf", "pages": 1, "counts": {"text": 1, "table": 0, "figure": 0}, "sections": [
        {"address": INTRO, "title": "Overview", "pages": "1", "characters": 10, "paragraphs": [INTRO]}], "tables": [], "figures": []}
    long = summary(point_text="とても長い説明が続きます。" * 300, tables=[], figures=[])
    out = deliver.run({}, {"intake/brief": {"file": "x.pdf", "today": "2026-11-25"},
                           "classify/report": report, "summarizer/summary": long})
    assert "not one A4 page" in out["error"] and smtp_server == []


def test_the_flow_check_has_nothing_to_say(proj):
    from nextop.validate.precheck import check_project
    checked = check_project(proj, "pdf_summary")
    assert checked.errors == [], checked.errors


def test_missing_mail_settings_stop_the_run_before_any_model_call(proj, sample_pdf, monkeypatch):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    res, fake = _run(proj, sample_pdf, [])
    assert not res.ok and "intake" in res.failed and "SMTP_HOST" in str(res.failed) and fake.calls == []


def test_a_mail_that_cannot_be_sent_fails_the_run_with_the_reason(proj, sample_pdf, smtp_server, monkeypatch):
    monkeypatch.setenv("SMTP_PORT", "1")                               # nothing listens there
    res, fake = _run(proj, sample_pdf, _open_then_save(summary()))
    assert not res.ok and "deliver" in res.failed and "127.0.0.1:1" in str(res.failed)
