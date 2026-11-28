"""What the program does without any model: the 8 layouts in every theme, the fit check, values carried by the program."""
import io
import json

import pytest
from conftest import call  # noqa: F401  (keeps the conftest import path)

from functions import _common, _deck, _pptx, _preview

ALL_LAYOUTS = list(_deck.LAYOUTS)


def _png(tmp_path, w=640, h=420):
    from PIL import Image
    path = tmp_path / "fig.png"
    Image.new("RGB", (w, h), (200, 220, 240)).save(path)
    return str(path)


def _report(tmp_path):
    cells = [["모델", "BLEU", "비용"], ["", "EN-DE", "EN-FR"]] + [[f"모델 {r}", f"{20 + r}.5", f"{r}.0 · 10^19"] for r in range(1, 12)]
    return {"file": "paper.pdf", "pages": 12, "counts": {"text": 3, "table": 1, "figure": 1},
            "sections": [{"address": f"fs://pdf/00{n}", "title": t, "pages": str(n - 1), "characters": 900,
                          "paragraphs": [f"fs://pdf/00{n}"]}
                         for n, t in ((2, "A Short Paper Title"), (3, "1 Introduction"), (4, "2 Results"))],
            "tables": [{"address": "fs://pdf/005", "label": "Table 1", "caption": "Table 1: Scores of the models. Second sentence here.",
                        "pages": "3", "rows": len(cells), "columns": 3, "header": cells[0], "cells": cells}],
            "figures": [{"address": "fs://pdf/006", "label": "Figure 1", "caption": "Figure 1: The model.", "pages": "2",
                         "width": 640, "height": 420, "image": _png(tmp_path)}]}


def _b(text, source="fs://pdf/003"):
    return {"text": text, "source": source, "quote": "q"}


def _deck_all(tmp_path, first="새 방법은 순서 없이 모든 단어를 한 번에 본다"):
    """A deck with every layout once."""
    plan = [{"layout": lay, "parts": ["fs://pdf/002"] if lay == "cover" else ["fs://pdf/003", "fs://pdf/004"],
             "table": "fs://pdf/005" if lay == "table" else "", "rows": [3, 4, 5, 13] if lay == "table" else [],
             "figure": "fs://pdf/006" if lay == "figure" else ""} for lay in ALL_LAYOUTS]
    three = [_b(first), _b("계산을 나누어 하기 쉬워 훈련이 빠르다"), _b("번역 품질이 기존 모델보다 높다")]
    text = {"cover": {"title": "어텐션만으로 번역하는 모델"}, "agenda": {"title": "목차"}, "section": {"title": "모델 구조"},
            "bullets": {"title": "핵심 아이디어", "bullets": three}, "figure": {"title": "모델 구조", "bullets": three[:2]},
            "table": {"title": "번역 성능", "bullets": three[1:]},
            "comparison": {"title": "새 방법과 옛 방법", "columns": [{"heading": "새 방법", "bullets": three[:2]},
                                                                {"heading": "옛 방법", "bullets": three[1:]}]},
            "closing": {"title": "핵심 정리", "bullets": three}}
    writing = {"slides": [{"bullets": [], "columns": [], **text[lay]} for lay in ALL_LAYOUTS]}
    return _deck.compose({"today": "2026-11-25"}, _report(tmp_path), {"slides": plan}, writing)


@pytest.mark.parametrize("theme", list(_deck.THEMES))
def test_every_layout_renders_in_every_theme(tmp_path, theme):
    from pptx import Presentation
    deck = _deck_all(tmp_path)
    assert _deck.fit_problems(deck) == []
    prs = Presentation(io.BytesIO(_pptx.build_pptx(deck, theme)))
    assert [lay.name for lay in prs.slide_layouts] == [_deck.LAYOUTS[k]["name"] for k in ALL_LAYOUTS]
    assert [s.slide_layout.name for s in prs.slides] == [_deck.LAYOUTS[k]["name"] for k in ALL_LAYOUTS]
    assert all(len(lay.shapes) >= 1 for lay in prs.slide_layouts)              # every layout carries the theme's accent shapes
    assert all(len(s.placeholders) == 0 for s in prs.slides)
    pngs = _preview.render_all(theme, deck)
    from PIL import Image
    sizes = {Image.open(io.BytesIO(p)).size for p in pngs}
    assert sizes == {(1600, 900)} and len(pngs) == 8
    assert Image.open(io.BytesIO(_preview.contact_sheet(pngs))).size[0] > 1500


def test_boxes_stay_on_the_slide_and_text_boxes_do_not_overlap(tmp_path):
    deck = _deck_all(tmp_path)
    for theme in _deck.THEMES:
        for i in range(len(deck["slides"])):
            sl = _deck.layout_slide(theme, deck, i)
            texts = [b for b in sl.boxes if b["kind"] in ("text", "paras", "table", "image")]
            for b in texts:
                assert 0 <= b["x"] and b["x"] + b["w"] <= _deck.SLIDE_W and 0 <= b["y"] and b["y"] + b["h"] <= _deck.SLIDE_H, (theme, i, b)
            for a in texts:
                for b in texts:
                    if a is b:
                        continue
                    overlap = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"]) > 1 and \
                        min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"]) > 1
                    number_in_circle = a.get("size") == _deck.STYLES["takeaway_no"]["size"] or b.get("size") == _deck.STYLES["takeaway_no"]["size"]
                    assert not overlap or number_in_circle, (theme, i, a.get("text"), b.get("text"))


def test_the_fit_check_names_the_characters_to_cut_and_that_cut_fits(tmp_path):
    long = "새 방법은 순서 없이 모든 단어를 한 번에 보고 계산을 나누어 하기 쉬워서 훈련이 아주 빠르고 번역 품질도 기존 모델보다 높다고 보고한다"
    deck = _deck_all(tmp_path, first=long)
    problems = _deck.fit_problems(deck)
    figure_slide = [p for p in problems if p.startswith("slides[4].bullets[0].text")]
    assert figure_slide and "its box holds 3" in figure_slide[0]
    over = int(figure_slide[0].split("Shorten it by about ")[1].split(" ")[0])
    shorter = _deck_all(tmp_path, first=long[:len(long) - over])
    assert not [p for p in _deck.fit_problems(shorter) if p.startswith("slides[4].bullets[0].text")]


def test_too_many_long_bullets_run_past_the_bottom(tmp_path):
    deck = _deck_all(tmp_path)
    deck["slides"][5]["table"]["cells"] = _report(tmp_path)["tables"][0]["cells"][:8]        # a tall table (8 rows)
    deck["slides"][5]["bullets"] = [dict(deck["slides"][5]["bullets"][0], text="번역 품질이 기존 모델보다 높고 비용은 낮다 " * 3)] * 3
    problems = _deck.fit_problems(deck)
    assert any(p.startswith("slides[5].bullets: the bullets run") for p in problems), problems


def test_table_cells_captions_and_pages_come_from_the_report(tmp_path):
    deck = _deck_all(tmp_path)
    table = deck["slides"][5]["table"]
    report = _report(tmp_path)
    assert table["cells"] == [report["tables"][0]["cells"][r - 1] for r in (1, 2, 3, 4, 5, 13)]      # header rows 1-2 always
    assert table["header_rows"] == 2 and table["part"] == "표 일부: 전체 13행 중 6행"
    assert table["caption"] == "Table 1: Scores of the models." and table["caption_full"].endswith("Second sentence here.")
    assert deck["slides"][0]["title"] == "A Short Paper Title" and deck["slides"][0]["subtitle"] == "어텐션만으로 번역하는 모델"
    assert deck["slides"][1]["items"] == ["모델 구조"]
    assert _deck.slide_pages(deck["slides"][5]) == ["2", "3"]
    assert _deck.header_count([["a", "b"], ["", "EN"], ["x", "1"]]) == 2


def test_a_saved_deck_draws_again_in_another_theme(tmp_path, monkeypatch):
    from functions._render import save_deck
    monkeypatch.setenv("DECK_DATA_DIR", str(tmp_path / "data"))
    saved = save_deck(_deck_all(tmp_path), "basic", "paper")
    stored = json.loads(saved["deck"].read_text(encoding="utf-8"))
    assert stored["slides"][4]["figure"]["image"] == "paper_assets/fig.png"        # relative to output/
    again = save_deck(stored, "academic", "paper")
    assert len(again["previews"]) == 8 and again["pptx"].name == "paper_academic.pptx"


def test_amounts_grow_with_the_document():
    assert _deck.amounts(2) == {"slides": 7, "sections": 1}          # a short document: one section
    assert _deck.amounts(15) == {"slides": 12, "sections": 2}
    assert _deck.amounts(100) == {"slides": 17, "sections": 4}
    guide = _deck.writing_guide()
    assert set(_deck.LAYOUTS) <= set(guide) and guide["closing"]["bullets"] == [3, 5] and guide["title_chars"] > 10


def test_term_written_twice_and_chinese_characters_are_found():
    assert _common.double_term_errors("t", "자기 어텐션(self-attention)을 쓴다")
    assert _common.double_term_errors("t", "Transformer(트랜스포머)")
    assert _common.double_term_errors("t", "BLEU 28.4 (영어-독일어)") == []
    assert _common.double_term_errors("t", "복잡도는 O(n)이다") == []
    assert "Chinese characters" in _common.han_errors("t", "성능이 增加했다")[0]


def test_planner_check_limits_tables(tmp_path):
    import importlib.util
    spec = importlib.util.spec_from_file_location("planner_checks", _common.ROOT / "workers" / "planner" / "checks.py")
    checks = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(checks)
    report = _report(tmp_path)
    brief = {"slides": 7, "sections": 2}

    def outline(rows, table="fs://pdf/005"):
        s = lambda lay, **kw: {"layout": lay, "topic": "", "parts": kw.get("parts", []), "table": kw.get("table", ""),
                               "rows": kw.get("rows", []), "figure": kw.get("figure", "")}
        return {"slides": [s("cover", parts=["fs://pdf/002"]), s("agenda"), s("section"),
                           s("table", parts=["fs://pdf/003"], table=table, rows=rows), s("section"),
                           s("figure", parts=["fs://pdf/004"], figure="fs://pdf/006"), s("closing", parts=["fs://pdf/003"])]}
    assert checks.check({"outline": outline([3, 4, 5])}, {"brief": brief, "report": report}) == []
    errors = checks.check({"outline": outline([])}, {"brief": brief, "report": report})
    assert any("would show 13 rows; at most 8 fit" in e for e in errors)
    errors = checks.check({"outline": outline([0, 99])}, {"brief": brief, "report": report})
    assert any("outside 1..13" in e for e in errors)
    report["tables"][0]["columns"] = 9
    errors = checks.check({"outline": outline([3])}, {"brief": brief, "report": report})
    assert any("has 9 columns, more than 7" in e for e in errors)


def test_a_character_the_slide_font_lacks_is_sent_back(tmp_path):
    deck = _deck_all(tmp_path, first="허용되지 않은 연결을 −∞로 가린다")
    problems = _deck.fit_problems(deck)
    assert any("slides[3].bullets[0].text" in p and "cannot draw (−)" in p for p in problems), problems


def test_one_slide_is_measured_alone_with_its_own_field_names(tmp_path):
    """The writer writes one slide per conversation: its check measures that slide (and, for a section slide, its
    title on the agenda) and names the fields of the one-slide writing."""
    report = _report(tmp_path)
    plan = [{"layout": lay, "topic": lay, "parts": ["fs://pdf/002"] if lay == "cover" else ["fs://pdf/003"],
             "table": "fs://pdf/005" if lay == "table" else "", "rows": [3, 4] if lay == "table" else [],
             "figure": "fs://pdf/006" if lay == "figure" else ""} for lay in ALL_LAYOUTS]
    brief = {"today": "2026-11-27", "layouts": _deck.writing_guide()}
    pieces = _deck.slide_pieces(brief, report, {"slides": plan})
    assert [p["no"] for p in pieces] == list(range(1, 9)) and {p["of"] for p in pieces} == {8}
    table = pieces[ALL_LAYOUTS.index("table")]
    assert table["table"]["cells"] == [report["tables"][0]["cells"][r] for r in (0, 1, 2, 3)]     # header rows + chosen
    assert table["parts"][0]["paragraphs"] == ["fs://pdf/003"] and table["bullets"] == [2, 3]
    section = pieces[ALL_LAYOUTS.index("section")]
    long = "분기별 방문자와 대출 그리고 월별 방문자와 프로그램별 만족도 조사"
    said = _deck.fit_problems(_deck.piece_deck(section, {"title": long, "bullets": [], "columns": []}))
    assert any(p.startswith("writing.title (shown on the agenda)") for p in said), said
    bullets = pieces[ALL_LAYOUTS.index("bullets")]
    three = [_b("새 방법은 순서 없이 모든 단어를 한 번에 본다 " * 5), _b("짧다"), _b("짧다")]
    said = _deck.fit_problems(_deck.piece_deck(bullets, {"title": "핵심", "bullets": three, "columns": []}))
    assert any(p.startswith("writing.bullets[0].text") and "Shorten it by about" in p for p in said), said
    assert _deck.fit_problems(_deck.piece_deck(bullets, {"title": "핵심", "bullets": three[1:] + [_b("짧다")],
                                                         "columns": []})) == []
