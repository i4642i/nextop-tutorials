"""The facts the program finds for the planner (pieces of a section, the text that talks about a table or figure) and
the planner's checks that use them. No model, no flow: the functions are called directly."""
import importlib.util

from conftest import ROOT

from functions._common import build_report
from functions._deck import writing_guide

D = "fs://pdf/001"


def _checks():
    spec = importlib.util.spec_from_file_location("planner_checks", ROOT / "workers" / "planner" / "checks.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _text(n, title, text, page):
    return {"kind": "text", "address": f"{D}#{n}", "title": title, "leaf": True, "text": text, "pages": page}


def _rows():
    """A paper: title, an introduction, a model section cut by a figure and a page break, a table told about later."""
    parts = [
        _text(1, "A Paper", "A Paper. Some authors.", 1),
        _text(2, "1 Introduction", "We study things.", 1),
        _text(3, "2 Model", "The model is shown in Figure 1 (left).", 1),
        {"kind": "figure", "address": f"{D}#4", "title": "Figure 1: The model.", "caption": "Figure 1: The model.",
         "leaf": True, "pages": 1, "image": "x.png", "width": 4, "height": 3},
        _text(5, "2 Model", "It has two halves.", 2),
        {"kind": "table", "address": f"{D}#6", "title": "Table 1: Costs.", "caption": "Table 1: Costs.", "leaf": True,
         "pages": 2, "columns": ["a", "b"], "rows": [["1", "2"]]},
        _text(7, "3 Results", "Table 1 compares the costs; Table 12 is elsewhere.", 2),
        {"kind": "table", "address": f"{D}#8", "title": "Table 2: Other.", "caption": "Table 2: Other.", "leaf": True,
         "pages": 2, "columns": ["a", "b"], "rows": [["3", "4"]]},
        _text(9, "4 Conclusion", "Table 2: Other. (the caption repeated as text)", 2),
    ]
    return [{"address": D, "doc": {"pages": 2}, "parts": parts}]


def test_the_report_names_the_pieces_of_a_section_and_the_text_about_each_table_and_figure():
    r = build_report(_rows(), "paper.pdf")
    pieces = {s["address"]: s.get("pieces") for s in r["sections"]}
    assert pieces[f"{D}#3"] == pieces[f"{D}#5"] == [f"{D}#3", f"{D}#5"]             # cut by the figure and the page
    assert pieces[f"{D}#2"] is None and pieces[f"{D}#7"] is None
    about = {x["address"]: x["text_parts"] for x in r["tables"] + r["figures"]}
    assert about[f"{D}#4"] == [f"{D}#3"]                         # "Figure 1" is named in #3
    assert about[f"{D}#6"] == [f"{D}#7"]                         # told about after it, not where it stands
    assert about[f"{D}#8"] == [f"{D}#7"]                         # only its repeated caption names it: where it stands


def _outline(model_parts, table_parts):
    s = lambda layout, parts=(), **kw: {"layout": layout, "topic": "t", "parts": list(parts), "table": kw.get("table", ""),
                                        "rows": [], "figure": kw.get("figure", "")}
    return {"slides": [s("cover", [f"{D}#1"]), s("agenda"), s("section"), s("bullets", [f"{D}#2"]),
                       s("figure", model_parts, figure=f"{D}#4"), s("section"), s("table", table_parts, table=f"{D}#6"),
                       s("closing", [f"{D}#7", f"{D}#9"])]}


def _check(outline):
    r = build_report(_rows(), "paper.pdf")
    brief = {"slides": 8, "sections": 2, "layouts": writing_guide()}
    return _checks().check({"outline": outline}, {"brief": brief, "report": r})


def test_a_good_outline_passes():
    assert _check(_outline([f"{D}#3", f"{D}#5"], [f"{D}#7"])) == []


def test_one_piece_of_a_section_gives_the_slide_the_whole_section():
    """The planner may name one piece of a section cut by a figure or a page break: it passes, and the writer's piece
    of that slide holds every piece of the section, in document order."""
    from functions._deck import slide_pieces
    outline = _outline([f"{D}#5"], [f"{D}#7"])
    assert _check(outline) == []
    brief = {"today": "2026-11-27", "layouts": writing_guide()}
    pieces = slide_pieces(brief, build_report(_rows(), "paper.pdf"), outline)
    assert [p["address"] for p in pieces[4]["parts"]] == [f"{D}#3", f"{D}#5"]


def test_a_table_slide_without_the_text_about_its_table_is_sent_back():
    errors = _check(_outline([f"{D}#3", f"{D}#5"], [f"{D}#2"]))
    assert errors == [f"slides[6] shows {D}#6 (Table 1: Costs.), but its parts ['{D}#2'] do not talk about it: "
                      f"name at least one of its text_parts ['{D}#7'] in parts"]
