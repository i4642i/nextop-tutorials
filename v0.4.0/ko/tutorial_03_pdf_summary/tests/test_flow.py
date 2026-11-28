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


def summary(point_text="요점입니다.", **change):
    s = {
        "title": "별빛마을 작은도서관 2026년 이용 현황 보고서",
        "key_points": [
            {"point": "방문자와 대출이 모두 늘었다.", "source": INTRO,
             "quote": "별빛마을 작은도서관은 2026년 한 해 동안 방문자와 대출이 모두 늘었다."},
            {"point": f"연간 방문자는 12,400명으로 늘었다. {point_text}", "source": USE_1,
             "quote": "연간 방문자는 모두 12,400명으로 전년보다 18퍼센트 늘었다."},
            {"point": "개관 시간을 늘려 달라는 요청이 많았다.", "source": TASKS,
             "quote": "평일 개관 시간을 한 시간 늘려 달라는 요청이 많았다."},
        ],
        "tables": [
            {"source": TABLE1, "line": "분기별 방문자와 대출은 3분기에 가장 크게 늘었다.", "rows": []},
            {"source": TABLE2, "line": "책 읽어 주기 모임의 만족도가 가장 높다.", "rows": [1, 2]},
        ],
        "figures": [{"figure": FIGURE1, "line": "10월 방문자가 가장 많다."}],
        "conclusion": "내년에는 개관 시간을 늘리고 스마트폰 교실을 한 반 더 연다.",
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
    assert report["tables"][0]["caption"] == "표 1. 분기별 방문자와 대출 권수"
    assert (report["tables"][0]["rows"], report["tables"][0]["columns"], report["tables"][0]["pages"]) == (5, 4, "1")
    assert report["tables"][1]["header"] == ["프로그램", "참여(명)", "만족도"]
    assert report["figures"][0]["caption"].startswith("그림 1.") and report["figures"][0]["width"] > 100
    assert [s["pages"] for s in report["sections"]] == ["1", "1", "1", "1", "2", "2", "2"]

    assert len(smtp_server) == 1
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"]
    assert mail["Subject"] == "[PDF 요약·시험] sample_report.pdf A4 요약 (글 7 · 표 2 · 그림 1)"
    body = mail.get_body(preferencelist=("plain",)).get_content()
    assert "표 1. 분기별 방문자와 대출 권수 (쪽 1) · 5행 × 4열" in body and "글 7개 · 표 2개 · 그림 1개" in body
    pdfs = [p for p in mail.iter_attachments() if p.get_content_type() == "application/pdf"]
    assert len(pdfs) == 1 and pdfs[0].get_filename() == "요약_sample_report.pdf"
    data = pdfs[0].get_content()
    assert page_count(data) == 1
    saved = tmp_path / "out" / "summaries" / "sample_report_summary.pdf"
    assert saved.read_bytes() == data

    import pypdfium2
    with pypdfium2.PdfDocument(data) as doc:                        # the page numbers come from the program, not the model
        page = doc[0].get_textpage().get_text_range()
    assert "근거: 쪽 1 · 2. 이용 현황" in page and "근거: 쪽 2 · 4. 개선 과제" in page
    assert "표 1. 분기별 방문자와 대출 권수" in page and "(쪽 1)" in page
    # the chosen table is drawn from table.rows (every cell of table 1), the picture is the figure part's image
    assert all(cell in page for row in report["tables"][0]["cells"] for cell in row)
    assert "5,900" in page and "+27%" in page
    assert "표 일부: 전체 4행 중 2행" in page and "4.7" in page and "2.4" not in page       # table 2: header + row 2 only
    assert "어린이 글쓰기 교실" not in page and "책 읽어 주기 모임" in page
    with pypdfium2.PdfDocument(data) as doc:
        images = [o for o in doc[0].get_objects() if o.type == pypdfium2.raw.FPDF_PAGEOBJ_IMAGE]
    assert len(images) == 1
    assert report["figures"][0]["image"].endswith(".png")


def test_a_changed_quote_is_refused_then_fixed(proj, sample_pdf, smtp_server):
    bad = summary()
    bad["key_points"][0]["quote"] = "별빛마을 작은도서관은 2026년 한 해 동안 방문자와 대출이 모두 늘어났다."      # one word changed
    res, fake = _run(proj, sample_pdf, _open_then_save(bad, summary()))
    assert res.ok, res.failed
    later = text_of(fake.calls[-1])
    assert "word for word" in later or "not found" in later or "찾을 수 없" in later       # the refusal reached the model
    assert "늘어났다" in later and len(smtp_server) == 1


def test_a_summary_longer_than_one_page_is_refused_then_shortened(proj, sample_pdf, smtp_server):
    long = summary(point_text="아주 긴 설명입니다. " * 500)
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
    wrong = summary(tables=[{"source": USE, "line": "이것은 글 부분이다.", "rows": []}])      # a text part, not a table
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
    return {"title": "T", "key_points": [{"point": "가", "source": "fs://pdf/001#1", "quote": "q"}] * 3,
            "tables": tables, "figures": figures, "conclusion": "나"}


def test_choosing_too_much_is_refused_by_the_page_check(tmp_path, project_dir, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("checks_t3", project_dir / "workers" / "summarizer" / "checks.py")
    monkeypatch.syspath_prepend(str(project_dir))
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    report = _big_report(tmp_path)
    rows = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
    both = _summary_for(report, [{"source": t["address"], "line": "표.", "rows": rows} for t in report["tables"]],
                        [{"figure": f["address"], "line": "그림."} for f in report["figures"]])
    errors = checks.check({"summary": both}, {"report": report}, _Sources("q"))
    assert any("does not fit one A4 page" in e and "choose fewer tables or figures" in e for e in errors), errors
    one = _summary_for(report, [{"source": report["tables"][0]["address"], "line": "표.", "rows": [1, 2, 3]}],
                       [{"figure": report["figures"][0]["address"], "line": "그림."}])
    assert checks.check({"summary": one}, {"report": report}, _Sources("q")) == []        # fewer choices fit


def test_a_big_table_needs_row_numbers_and_a_wide_one_is_refused(tmp_path, project_dir, monkeypatch):
    import importlib.util
    spec = importlib.util.spec_from_file_location("checks_t3b", project_dir / "workers" / "summarizer" / "checks.py")
    monkeypatch.syspath_prepend(str(project_dir))
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    report = _big_report(tmp_path)
    t0 = report["tables"][0]["address"]
    errors = checks.check({"summary": _summary_for(report, [{"source": t0, "line": "표.", "rows": []}], [])}, {"report": report}, _Sources("q"))
    assert any("has 20 rows" in e and "Give the numbers of the rows" in e for e in errors)
    errors = checks.check({"summary": _summary_for(report, [{"source": t0, "line": "표.", "rows": [1, 99]}], [])}, {"report": report}, _Sources("q"))
    assert any("outside 1..20" in e for e in errors)
    report["tables"][1].update(columns=39)
    errors = checks.check({"summary": _summary_for(report, [{"source": report["tables"][1]["address"], "line": "표.", "rows": [1, 2]}], [])},
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
        {"address": INTRO, "title": "개요", "pages": "1", "characters": 10, "paragraphs": [INTRO]}], "tables": [], "figures": []}
    long = summary(point_text="아주 긴 설명입니다. " * 500, tables=[], figures=[])
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
