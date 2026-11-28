"""The whole flow (intake -> classify -> みなと -> split -> しおり, one slide at a time -> gather -> deliver) with a
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
        slide("cover", "報告書を紹介する", [TITLE]),
        slide("agenda", "目次"),
        slide("section", "利用状況と改善課題"),
        slide("table", "四半期ごとの来館者数と貸出冊数", [USE], table=TABLE1),
        slide("figure", "月ごとの来館者数", [USE], figure=FIGURE1),
        slide("bullets", "催しの満足度と改善課題", [SATISFACTION, TASKS]),
        slide("closing", "まとめ", [INTRO, TASKS, CONCLUSION]),
    ]}
    o.update(change)
    return o


def bullet(text, source, quote):
    return {"text": text, "source": source, "quote": quote}


def written(first="来館者数と貸出冊数がともに増えました"):
    """The 7 written slides, in outline order (each is one writer conversation's writing)."""
    return [
        {"title": "図書館の一年をひと目で", "bullets": [], "columns": []},
        {"title": "目次", "bullets": [], "columns": []},
        {"title": "利用状況と改善課題", "bullets": [], "columns": []},
        {"title": "四半期ごとの来館者数と貸出冊数", "columns": [], "bullets": [
            bullet("来館者は12,400人で、前年より18パーセント増えました", USE_1, "年間の来館者数は合計12,400人で、前年より18パーセント増えた。"),
            bullet("貸出冊数は第3四半期に最も伸びました", USE_1, "貸出冊数は第3四半期に最も大きく伸びた。")]},     # "貸出冊数\nは" in the PDF
        {"title": "秋が最もにぎわいました", "columns": [], "bullets": [
            bullet("来館者は秋に最も多くなりました", USE_1, "来館者は秋に最も多く"),
            bullet("年間の来館者数は12,400人です", USE_1, "年間の来館者数は合計12,400人")]},
        {"title": "催しと改善課題", "columns": [], "bullets": [
            bullet("読み聞かせの会の満足度が最も高くなりました", SATISFACTION + ".1", "読み聞かせの会の満足度が最も高かった。"),
            bullet("平日の開館時間を延ばす要望が多くありました", TASKS, "平日の開館時間を1時間延ばしてほしいという要望が多く寄せられた。"),
            bullet("スマホ教室はもう1クラス開くべきです", TASKS, "もう1クラス開くべきだという意見が出た。")]},
        {"title": "まとめ", "columns": [], "bullets": [
            bullet(first, INTRO, "ほしあかり町図書館では、2026年の一年間で来館者数と貸出冊数がともに増えた。"),
            bullet("平日の開館時間を延ばす要望が多くありました", TASKS, "平日の開館時間を1時間延ばしてほしいという要望が多く寄せられた。"),
            bullet("来年は開館時間を延ばし、教室を増やします", CONCLUSION, "来年は平日の開館時間を延ばし")]},     # "延ば\nし" in the PDF
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
    assert [lay.name for lay in prs.slide_layouts] == ["表紙", "目次", "セクション", "箇条書き", "図と説明", "表と説明",
                                                     "2 列の比較", "まとめ"]
    assert [s.slide_layout.name for s in prs.slides] == ["表紙", "目次", "セクション", "表と説明", "図と説明",
                                                     "箇条書き", "まとめ"]
    assert sorted(p.name for p in (out / "sample_report_dark").glob("*.png")) == [f"slide_{n:02d}.png" for n in range(1, 8)]
    assert (out / "sample_report_dark_overview.png").is_file()

    def texts(s):                                                 # every paragraph of every text box
        return [p.text for sh in s.shapes if sh.has_text_frame for p in sh.text_frame.paragraphs]
    cover, agenda, table_slide, figure_slide = prs.slides[0], prs.slides[1], prs.slides[3], prs.slides[4]
    assert "ほしあかり町図書館 2026年 利用状況報告書" in texts(cover)             # the title part's heading, by program
    assert any("原本 sample_report.pdf · 2 ページ" in t for t in texts(cover))
    assert "利用状況と改善課題" in texts(agenda)                                     # from the section slide's title
    assert "秋が最もにぎわいました" in texts(figure_slide)                               # each slide in its outline place
    report = res.outputs["classify"]["report"]
    cells = [[c.text_frame.text for c in row.cells] for sh in table_slide.shapes if sh.has_table for row in sh.table.rows]
    assert cells == report["tables"][0]["cells"]                                       # every cell carried, none retyped
    assert any("表1. 四半期ごとの来館者数と貸出冊数（1 ページ）" in t for t in texts(table_slide))
    assert any(t.endswith("出典 1 ページ") for t in texts(table_slide)) and "4 / 7" in texts(table_slide)
    pictures = [sh for sh in figure_slide.shapes if sh.shape_type == 13]
    assert len(pictures) == 1 and pictures[0].image.blob == open(report["figures"][0]["image"], "rb").read()
    notes = prs.slides[6].notes_slide.notes_text_frame.text
    assert "出典: 2 ページ · 4. 改善課題 — 「平日の開館時間を1時間延ばしてほしいという要望が多く寄せられた。」" in notes
    run = cover.shapes[-1].text_frame.paragraphs[0].runs[0]._r                   # Japanese runs: ja-JP, Japanese line breaking
    assert run.get_or_add_rPr().get("lang") == "ja-JP"

    assert len(smtp_server) == 1
    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert to == ["office@example.com"] and mail["Subject"] == "[PDFスライド・テスト] sample_report.pdf のスライド（7 枚、ダーク テーマ）"
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
    assert pieces[2]["covers"] == ["四半期ごとの来館者数と貸出冊数", "月ごとの来館者数", "催しの満足度と改善課題"]  # the section's slides
    table_input = text_of(fake.by_slide[4][0])
    assert "四半期ごとの来館者数と貸出冊数" in table_input and USE_1 in table_input          # its topic and its paragraphs
    assert "催しの満足度と改善課題" not in table_input and TASKS not in table_input        # not the other slides


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
    bad["slides"][5]["rows"] = [1, 2]                                # rows on a bullets slide
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
    long = "来館者数と貸出冊数はどちらも今年大きく伸びました。" * 8
    res, fake = _run(proj, sample_pdf, _ok_planner(), _again(7, written(first=long)[6]))
    assert res.ok, res.failed
    assert [len(v) for _, v in sorted(fake.by_slide.items())] == [1, 1, 1, 1, 1, 1, 2]   # only slide 7 again
    sent = text_of(fake.by_slide[7][1])
    assert "writing.bullets[0].text" in sent and "Shorten it by about" in sent and "its box holds 2" in sent


def test_a_section_title_is_measured_on_the_agenda_too(proj, sample_pdf, smtp_server):
    long = "四半期ごとの来館者数と貸出冊数、そして月ごとの来館者数と催しごとの満足度についての調査"
    res, fake = _run(proj, sample_pdf, _ok_planner(), _again(3, {"title": long, "bullets": [], "columns": []}))
    assert res.ok, res.failed
    assert "writing.title (shown on the agenda)" in text_of(fake.by_slide[3][1])


def test_other_letters_parentheses_terms_a_wrong_quote_and_a_wrong_source_are_sent_back(proj, sample_pdf, smtp_server):
    bad = written(first="来館者数と貸出冊数がともに\ub298\uc5c8\ub2e4")                  # Korean letters slipped in
    bad[2]["title"] = "利用状況（usage）"
    bad[3]["bullets"][0]["quote"] = "年間の来館者数は合計12,500人で、前年より18パーセント増えた。"
    bad[4]["bullets"][0]["source"] = TASKS
    res, fake = _run(proj, sample_pdf, _ok_planner(),
                     {**_again(3, bad[2]), **_again(4, bad[3]), **_again(5, bad[4]), **_again(7, bad[6])})
    assert res.ok, res.failed
    sent = text_of(fake.by_slide[7][1])
    assert "has Korean letters" in sent and "write it again in Japanese only" in sent
    assert "writes a term twice with parentheses" in text_of(fake.by_slide[3][1])
    assert "12,500" in text_of(fake.by_slide[4][1])                 # the quote check named the quote it could not find
    assert "is not a paragraph of this slide's parts" in text_of(fake.by_slide[5][1])


def test_wrong_bullet_counts_are_sent_back(proj, sample_pdf, smtp_server):
    cover = dict(written()[0], bullets=[bullet("表紙の文", TITLE, "x")])
    closing = dict(written()[6], bullets=written()[6]["bullets"][:2])
    res, fake = _run(proj, sample_pdf, _ok_planner(), {**_again(1, cover), **_again(7, closing)})
    assert res.ok, res.failed
    assert "writing.bullets has 1; this slide is cover (表紙) and takes no bullets" in text_of(fake.by_slide[1][1])
    assert "writing.bullets has 2; this slide is closing (まとめ) and takes 3 to 5 bullets" in text_of(fake.by_slide[7][1])


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
    assert not res.ok and "theme must be one of basic (ベーシック), dark (ダーク), academic (アカデミック)" in str(res.failed)


def test_the_flow_check_has_nothing_to_say(proj):
    from nextop.validate.precheck import check_project
    checked = check_project(proj, "pdf_to_ppt")
    assert checked.errors == [], checked.errors
