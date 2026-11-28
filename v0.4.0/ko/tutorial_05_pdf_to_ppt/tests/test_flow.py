"""The whole flow (intake -> classify -> 보람 -> split -> 새롬, one slide at a time -> gather -> deliver) with a
scripted model.

Reading the PDF into parts and paragraphs, the classification, the checks, cutting the outline into slides, the deck,
the .pptx, the previews and the mail run for real.
"""
import email
import email.policy

from conftest import SlideLLM, adapters, call, save, text_of
from nextop.runtime.flow import run_flow

# Addresses of the sample PDF: the document fs://pdf/001, its parts in document order (#1 ... #10), and the paragraphs
# of a section of more than one paragraph (#3.1, #3.2); a section of one paragraph is its own paragraph
DOC = "fs://pdf/001"
TITLE, INTRO, USE, TABLE1, FIGURE1, CAPTION1, SATISFACTION, TABLE2, TASKS, CONCLUSION = (f"{DOC}#{n}" for n in range(1, 11))
USE_1 = USE + ".1"


def slide(layout, topic="", parts=(), table="", rows=(), figure=""):
    return {"layout": layout, "topic": topic, "parts": list(parts), "table": table, "rows": list(rows), "figure": figure}


def outline(**change):
    """7 slides: the sample PDF has 2 pages (brief.slides 7, brief.sections 1)."""
    o = {"slides": [
        slide("cover", "보고서 소개", [TITLE]),
        slide("agenda", "목차"),
        slide("section", "이용 현황과 과제"),
        slide("table", "분기별 방문자와 대출", [USE], table=TABLE1),
        slide("figure", "월별 방문자", [USE], figure=FIGURE1),
        slide("bullets", "프로그램 만족도와 과제", [SATISFACTION, TASKS]),
        slide("closing", "핵심 정리", [INTRO, TASKS, CONCLUSION]),
    ]}
    o.update(change)
    return o


def bullet(text, source, quote):
    return {"text": text, "source": source, "quote": quote}


def written(first="방문자와 대출이 모두 늘었다"):
    """The 7 written slides, in outline order (each is one writer conversation's writing)."""
    return [
        {"title": "2026년 작은도서관 이용을 한눈에", "bullets": [], "columns": []},
        {"title": "목차", "bullets": [], "columns": []},
        {"title": "이용 현황과 과제", "bullets": [], "columns": []},
        {"title": "분기별 방문자와 대출", "columns": [], "bullets": [
            bullet("연간 방문자는 12,400명으로 18퍼센트 늘었다", USE_1, "연간 방문자는 모두 12,400명으로 전년보다 18퍼센트 늘었다."),
            bullet("대출은 3분기에 가장 크게 늘었다", USE_1, "대출은\n3분기에 가장 크게 늘었다.")]},
        {"title": "가을에 가장 붐볐다", "columns": [], "bullets": [
            bullet("방문자는 가을에 가장 많았다", USE_1, "방문자는 가을에 가장 많았고"),
            bullet("10월 방문자가 가장 많다", USE_1, "연간 방문자는 모두 12,400명으로")]},
        {"title": "프로그램과 과제", "columns": [], "bullets": [
            bullet("책 읽어 주기 모임의 만족도가 가장 높았다", SATISFACTION + ".1", "책 읽어 주기 모임의 만족도가 가장 높았다."),
            bullet("저녁 방문자가 늘어 개관 연장 요청이 많았다", TASKS, "평일 개관 시간을 한 시간 늘려 달라는 요청이 많았다."),
            bullet("스마트폰 교실은 한 반을 더 열어야 한다", TASKS, "한 반을 더 열어야 한다는 의견이 나왔다.")]},
        {"title": "핵심 정리", "columns": [], "bullets": [
            bullet(first, INTRO, "방문자와 대출이 모두 늘었다."),
            bullet("평일 개관 시간을 늘려 달라는 요청이 많았다", TASKS, "평일 개관 시간을 한 시간 늘려 달라는 요청이 많았다."),
            bullet("내년에는 개관 시간을 늘리고 교실을 한 반 더 연다", CONCLUSION, "내년에는 평일 개관 시간을 늘리고")]},
    ]


def _run(proj, pdf, planner, slides=None, theme="dark"):
    """planner: the planner's replies; slides: {slide number: replies} for the slides that are not saved right away
    (every other slide saves its written() slide at once)."""
    script = {n: [save(writing=w)] for n, w in enumerate(written(), 1)}
    script.update(slides or {})
    fake = SlideLLM(planner, script)
    res = run_flow(proj, "pdf_to_ppt", {"pdf_path": str(pdf), "theme": theme}, adapters=adapters(fake))
    return res, fake


def _ok_planner():
    return [save(outline=outline())]


def _again(n, bad):
    """Slide n saves `bad` first, then its right writing."""
    return {n: [save(writing=bad), save(writing=written()[n - 1])]}


def _pptx(path):
    from pptx import Presentation
    return Presentation(str(path))


def test_whole_flow_makes_the_pptx_previews_and_mail(proj, sample_pdf, smtp_server, tmp_path):
    res, fake = _run(proj, sample_pdf, _ok_planner(), {4: [call("get", {"address": USE}), save(writing=written()[3])]})
    assert res.ok, res.failed
    brief = res.outputs["intake"]["brief"]
    assert (brief["pages"], brief["slides"], brief["sections"], brief["theme"]) == (2, 7, 1, "dark")
    assert brief["layouts"]["bullets"]["bullets"] == [3, 5] and brief["layouts"]["bullets"]["bullet_chars"] > 20
    assert [len(v) for _, v in sorted(fake.by_slide.items())] == [1, 1, 1, 2, 1, 1, 1]     # one conversation per slide

    out = tmp_path / "out" / "output"
    prs = _pptx(out / "sample_report_dark.pptx")
    assert [lay.name for lay in prs.slide_layouts] == ["표지", "목차", "구역 표지", "글머리표", "그림과 설명", "표와 설명", "두 단 비교", "핵심 정리"]
    assert [s.slide_layout.name for s in prs.slides] == ["표지", "목차", "구역 표지", "표와 설명", "그림과 설명", "글머리표", "핵심 정리"]
    assert sorted(p.name for p in (out / "sample_report_dark").glob("*.png")) == [f"slide_{n:02d}.png" for n in range(1, 8)]
    assert (out / "sample_report_dark_overview.png").is_file()

    def texts(s):                                                 # every paragraph of every text box
        return [p.text for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs]
    cover, agenda, table_slide, figure_slide = prs.slides[0], prs.slides[1], prs.slides[3], prs.slides[4]
    assert "별빛마을 작은도서관 2026년 이용 현황 보고서" in texts(cover)                 # the title part's heading, by program
    assert any("원본 sample_report.pdf · 2쪽" in t for t in texts(cover))
    assert "이용 현황과 과제" in texts(agenda)                                         # from the section slide's title
    assert "가을에 가장 붐볐다" in texts(figure_slide)                               # each slide in its outline place
    report = res.outputs["classify"]["report"]
    cells = [[c.text_frame.text for c in row.cells] for sh in table_slide.shapes if sh.has_table for row in sh.table.rows]
    assert cells == report["tables"][0]["cells"]                                       # every cell carried, none retyped
    assert any("표 1. 분기별 방문자와 대출 권수 (쪽 1)" in t for t in texts(table_slide))
    assert any(t.endswith("근거 쪽 1") for t in texts(table_slide)) and "4 / 7" in texts(table_slide)
    pictures = [sh for sh in figure_slide.shapes if sh.shape_type == 13]
    assert len(pictures) == 1 and pictures[0].image.blob == open(report["figures"][0]["image"], "rb").read()
    notes = prs.slides[6].notes_slide.notes_text_frame.text
    assert "근거: 쪽 2 · 4. 개선 과제 — “평일 개관 시간을 한 시간 늘려 달라는 요청이 많았다.”" in notes

    assert len(smtp_server) == 1
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"] and mail["Subject"] == "[PDF 발표·시험] sample_report.pdf 발표 자료 (7장, 다크 테마)"
    names = [p.get_filename() for p in mail.iter_attachments()]
    assert names == ["sample_report_dark.pptx", "sample_report_dark_overview.png"]


def test_each_writer_gets_only_its_slide(proj, sample_pdf, smtp_server):
    res, fake = _run(proj, sample_pdf, _ok_planner())
    assert res.ok, res.failed
    pieces = [p["slide"] for p in res.outputs["split"]["pieces"]]
    assert [(p["no"], p["of"], p["layout"]) for p in pieces] == [(n, 7, s["layout"]) for n, s in enumerate(outline()["slides"], 1)]
    table = pieces[3]["table"]
    assert table["cells"] == res.outputs["classify"]["report"]["tables"][0]["cells"] and table["address"] == TABLE1
    assert [p["address"] for p in pieces[3]["parts"]] == [USE, CAPTION1]      # USE's section goes on after the figure
    assert USE_1 in pieces[3]["parts"][0]["paragraphs"]
    assert pieces[4]["figure"]["address"] == FIGURE1 and "image" not in pieces[4]["figure"]     # the picture stays a file
    assert pieces[2]["covers"] == ["분기별 방문자와 대출", "월별 방문자", "프로그램 만족도와 과제"]  # the section's slides
    table_input = text_of(fake.by_slide[4][0])
    assert "분기별 방문자와 대출" in table_input and USE_1 in table_input            # its topic and its paragraphs
    assert "프로그램 만족도와 과제" not in table_input and TASKS not in table_input    # not the other slides


def test_the_planner_is_sent_back_for_a_wrong_layout_and_count(proj, sample_pdf, smtp_server):
    bad = outline()
    bad["slides"][3]["layout"] = "timeline"
    short = outline(slides=outline()["slides"][:6])
    res, fake = _run(proj, sample_pdf, [save(outline=bad), save(outline=short), *_ok_planner()])
    assert res.ok, res.failed
    sent = [text_of(c) for c in fake.calls]
    assert any("'timeline' is not a layout" in t for t in sent)
    assert any("the outline has 6 slides; brief.slides is 7" in t for t in sent)


def test_the_planner_cannot_pick_a_table_that_is_not_there_or_reuse_a_figure(proj, sample_pdf, smtp_server):
    bad = outline()
    bad["slides"][3]["table"] = USE                                  # a text part, not a table
    bad["slides"][5]["rows"] = [1, 2]                                # rows on a figure slide
    res, fake = _run(proj, sample_pdf, [save(outline=bad), *_ok_planner()])
    assert res.ok, res.failed
    sent = text_of(fake.calls[1])
    assert "is not one of the report's tables" in sent and "only a table slide has a table and rows" in sent


def test_a_table_slide_must_name_the_text_that_talks_about_its_table(proj, sample_pdf, smtp_server):
    bad = outline()
    bad["slides"][3]["parts"] = [TASKS]                              # the table stands in USE, not in TASKS
    res, fake = _run(proj, sample_pdf, [save(outline=bad), *_ok_planner()])
    assert res.ok, res.failed
    assert res.outputs["classify"]["report"]["tables"][0]["text_parts"] == [USE]
    sent = text_of(fake.calls[1])
    assert f"slides[3] shows {TABLE1}" in sent and f"name at least one of its text_parts ['{USE}'] in parts" in sent


def test_a_slide_that_does_not_fit_is_redone_alone(proj, sample_pdf, smtp_server):
    long = ("방문자와 대출이 모두 늘었고 " * 12).strip()
    res, fake = _run(proj, sample_pdf, _ok_planner(), _again(7, written(first=long)[6]))
    assert res.ok, res.failed
    assert [len(v) for _, v in sorted(fake.by_slide.items())] == [1, 1, 1, 1, 1, 1, 2]   # only slide 7 again
    sent = text_of(fake.by_slide[7][1])
    assert "writing.bullets[0].text" in sent and "Shorten it by about" in sent and "its box holds 2" in sent


def test_a_section_title_is_measured_on_the_agenda_too(proj, sample_pdf, smtp_server):
    long = "분기별 방문자와 대출 그리고 월별 방문자와 프로그램별 만족도 조사"
    res, fake = _run(proj, sample_pdf, _ok_planner(), _again(3, {"title": long, "bullets": [], "columns": []}))
    assert res.ok, res.failed
    assert "writing.title (shown on the agenda)" in text_of(fake.by_slide[3][1])


def test_parentheses_terms_a_wrong_quote_and_a_wrong_source_are_sent_back(proj, sample_pdf, smtp_server):
    bad = written(first="방문자(visitors)와 대출이 모두 늘었다")
    bad[3]["bullets"][0]["quote"] = "연간 방문자는 모두 12,500명이었다."
    bad[4]["bullets"][0]["source"] = TASKS
    res, fake = _run(proj, sample_pdf, _ok_planner(), {**_again(4, bad[3]), **_again(5, bad[4]), **_again(7, bad[6])})
    assert res.ok, res.failed
    assert "writes a term twice with parentheses" in text_of(fake.by_slide[7][1])
    assert "12,500" in text_of(fake.by_slide[4][1])                 # the quote check named the quote it could not find
    assert "is not a paragraph of this slide's parts" in text_of(fake.by_slide[5][1])


def test_wrong_bullet_counts_are_sent_back(proj, sample_pdf, smtp_server):
    cover = dict(written()[0], bullets=[bullet("표지 글", TITLE, "x")])
    closing = dict(written()[6], bullets=written()[6]["bullets"][:2])
    res, fake = _run(proj, sample_pdf, _ok_planner(), {**_again(1, cover), **_again(7, closing)})
    assert res.ok, res.failed
    assert "writing.bullets has 1; this slide is cover (표지) and takes no bullets" in text_of(fake.by_slide[1][1])
    assert "writing.bullets has 2; this slide is closing (핵심 정리) and takes 3 to 5 bullets" in text_of(fake.by_slide[7][1])


def test_missing_mail_settings_do_not_fail_the_run_and_it_says_no_mail_was_sent(proj, sample_pdf, tmp_path, monkeypatch):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    res, fake = _run(proj, sample_pdf, _ok_planner(), theme="academic")
    assert res.ok, res.failed
    mail = res.outputs["deliver"]["mail"]
    assert mail["sent"] is False and "SMTP_HOST" in mail["note"] and ".env" in mail["note"] and "OFFICE_EMAIL" in mail["note"]
    assert (tmp_path / "out" / "output" / "sample_report_academic.pptx").is_file()


def test_a_configured_mail_that_cannot_be_sent_fails_the_run_but_the_slides_are_saved(proj, sample_pdf, smtp_server, tmp_path, monkeypatch):
    monkeypatch.setenv("SMTP_PORT", "1")                               # nothing listens there
    res, fake = _run(proj, sample_pdf, _ok_planner(), theme="academic")
    assert not res.ok and "deliver" in res.failed and "127.0.0.1:1" in str(res.failed)
    assert (tmp_path / "out" / "output" / "sample_report_academic.pptx").is_file()


def test_an_unknown_theme_stops_at_the_start(proj, sample_pdf):
    res, fake = _run(proj, sample_pdf, [], theme="neon")
    assert not res.ok and "theme must be one of basic (기본), dark (다크), academic (학술)" in str(res.failed)


def test_the_flow_check_has_nothing_to_say(proj):
    from nextop.validate.precheck import check_project
    checked = check_project(proj, "pdf_to_ppt")
    assert checked.errors == [], checked.errors
