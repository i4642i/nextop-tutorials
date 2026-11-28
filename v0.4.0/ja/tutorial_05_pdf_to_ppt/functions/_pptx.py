"""Writes the deck as a .pptx file with python-pptx (MIT license).

The file's slide master holds exactly the 8 layouts of the theme (表紙, 目次, セクション, 箇条書き, 図と説明,
表と説明, 2 列の比較, まとめ), each with the theme's background and accent shapes, and the theme's colours and fonts. Every
slide uses its layout and adds its own boxes from _deck.layout_slide (the same boxes the previews draw).
"""
import io

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.shapes.shapetree import SlideShapes
from pptx.util import Emu

from functions._deck import LAYOUT_ORDER, LAYOUTS, SLIDE_H, SLIDE_W, THEMES, decor, layout_slide, notes, theme_fonts

PT = 12700                                    # EMU per point
NO_STYLE_TABLE = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"     # PowerPoint's "No Style, No Grid" table style
ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}
ANCHOR = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE}


def E(v: float) -> Emu:
    return Emu(int(round(v * PT)))


def _plain(shape):
    """No theme style on a shape (no shadow, no outline): only the fill set here."""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)
    shape.line.fill.background()


def _run_font(run, size, bold, color, name):
    f = run.font
    f.size, f.bold, f.name = E(size), bold, name
    f.color.rgb = RGBColor.from_string(color)
    rpr = run._r.get_or_add_rPr()
    rpr.set("lang", "ja-JP")                   # Japanese text: PowerPoint's Japanese line breaking
    rpr.set("altLang", "en-US")
    latin = rpr.find(qn("a:latin"))
    ea = etree.SubElement(rpr, qn("a:ea"))
    ea.set("typeface", name)
    latin.addnext(ea)                          # Japanese text uses the same font (east Asian slot)


def _word_wrap(p):
    """Break lines as the previews and the fit check do: between Japanese characters (with the Japanese line-breaking
    rules), never inside a Latin word."""
    ppr = p._p.get_or_add_pPr()
    ppr.set("eaLnBrk", "1")
    ppr.set("latinLnBrk", "0")
    ppr.set("hangingPunct", "0")


MARKS = {"square": "■", "dot": "●", "dash": "–"}


def _bullet(p, marker, indent):
    """A bullet mark in the theme's accent colour, hanging `indent` points left of the text."""
    ppr = p._p.get_or_add_pPr()
    ppr.set("marL", str(int(indent * PT)))
    ppr.set("indent", str(-int(indent * PT)))
    clr = etree.SubElement(ppr, qn("a:buClr"))
    etree.SubElement(clr, qn("a:srgbClr")).set("val", marker["color"])
    etree.SubElement(ppr, qn("a:buSzPct")).set("val", "100000")
    etree.SubElement(ppr, qn("a:buFont")).set("typeface", "Arial")
    etree.SubElement(ppr, qn("a:buChar")).set("char", MARKS[marker["shape"]])


def _add(shapes, box, fonts):
    k = box["kind"]
    x, y, w, h = E(box["x"]), E(box["y"]), E(box["w"]), E(box["h"])
    if k in ("rect", "oval"):
        kind = MSO_SHAPE.OVAL if k == "oval" else MSO_SHAPE.ROUNDED_RECTANGLE if box.get("radius") else MSO_SHAPE.RECTANGLE
        sh = shapes.add_shape(kind, x, y, w, h)
        _plain(sh)
        sh.fill.solid()
        sh.fill.fore_color.rgb = RGBColor.from_string(box["fill"])
        if box.get("radius"):
            sh.adjustments[0] = box["radius"] / min(box["w"], box["h"])
    elif k in ("text", "paras"):
        sh = shapes.add_textbox(x, y, w, h)
        tf = sh.text_frame
        tf.word_wrap, tf.auto_size = True, MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = ANCHOR[box.get("anchor", "top")]
        for i, para in enumerate(box["paras"] if k == "paras" else [box]):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = ALIGN[para["align"]]
            p.line_spacing = E(para["lh"])
            if para.get("before"):
                p.space_before = E(para["before"])
            _word_wrap(p)
            if box.get("marker"):
                _bullet(p, box["marker"], box["indent"])
            _run_font(p.add_run(), para["size"], para["bold"], para["color"], fonts[para["font"]]["name"])
            p.runs[0].text = para["text"]
    elif k == "image":
        shapes.add_picture(box["path"], x, y, w, h)
    elif k == "table":
        rows = box["rows"]
        frame = shapes.add_table(len(rows), len(box["widths"]), x, y, w, h)
        tbl = frame.table
        tbl.first_row = tbl.horz_banding = False
        frame._element.graphic.graphicData.tbl.tblPr.find(qn("a:tableStyleId")).text = NO_STYLE_TABLE
        for c, cw in enumerate(box["widths"]):
            tbl.columns[c].width = E(cw)
        body_n = 0
        for r, row in enumerate(rows):
            tbl.rows[r].height = E(row["h"])
            fill = box["head_bg"] if row["header"] else (box["row_alt"] if body_n % 2 else box["row_bg"])
            color = box["head_text"] if row["header"] else box["row_text"]
            body_n += 0 if row["header"] else 1
            for c, text in enumerate(row["cells"]):
                cell = tbl.cell(r, c)
                cell.fill.solid()
                cell.fill.fore_color.rgb = RGBColor.from_string(fill)
                cell.margin_left = cell.margin_right = E(box["pad_x"])
                cell.margin_top = cell.margin_bottom = E(3)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                p = cell.text_frame.paragraphs[0]
                p.line_spacing = E(box["lh"])
                p.alignment = PP_ALIGN.LEFT if c == 0 else PP_ALIGN.CENTER
                _word_wrap(p)
                _run_font(p.add_run(), box["size"], row["header"], color, fonts["body"]["name"])
                p.runs[0].text = text


def _theme_part(prs, code):
    """Set the colour scheme and the fonts of the file's theme (what PowerPoint offers for new shapes and text)."""
    t, fonts = THEMES[code], theme_fonts(code)
    part = prs.slide_master.part.part_related_by(RT.THEME)
    root = etree.fromstring(part.blob)
    a = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    root.find(f"{a}themeElements").find(f"{a}clrScheme").set("name", f"nextop {t['name']}")
    scheme = {"dk1": t["text"] if code != "dark" else "0F141C", "lt1": t["bg"] if code != "dark" else "FFFFFF",
              "dk2": t["title"] if code != "dark" else t["panel"], "lt2": t["panel"],
              "accent1": t["accent"], "accent2": t["accent2"], "accent3": t["title"], "accent4": t["muted"]}
    for slot, color in scheme.items():
        el = root.find(f".//{a}clrScheme/{a}{slot}")
        for child in list(el):
            el.remove(child)
        etree.SubElement(el, f"{a}srgbClr").set("val", color)
    fs = root.find(f".//{a}fontScheme")
    fs.set("name", f"nextop {t['name']}")
    for which, role in (("majorFont", "title"), ("minorFont", "body")):
        f = fs.find(f"{a}{which}")
        f.find(f"{a}latin").set("typeface", fonts[role]["name"])
        f.find(f"{a}ea").set("typeface", fonts[role]["name"])
    part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _prepare_layouts(prs, code):
    """Keep 8 layouts in the master, named and drawn for the theme; returns {layout code: slide layout}."""
    t = THEMES[code]
    fonts = theme_fonts(code)
    prs.slide_master.background.fill.solid()
    prs.slide_master.background.fill.fore_color.rgb = RGBColor.from_string(t["bg"])
    layouts = list(prs.slide_layouts)
    for extra in layouts[len(LAYOUT_ORDER):]:
        prs.slide_layouts.remove(extra)
    out = {}
    for layout, name in zip(layouts, LAYOUT_ORDER):
        layout.name = LAYOUTS[name]["name"]
        for ph in list(layout.placeholders):
            ph._element.getparent().remove(ph._element)
        bg, shapes = decor(code, name)
        layout.background.fill.solid()
        layout.background.fill.fore_color.rgb = RGBColor.from_string(bg)
        tree = SlideShapes(layout.shapes._spTree, layout)
        for box in shapes:
            _add(tree, box, fonts)
        out[name] = layout
    return out


def build_pptx(deck: dict, code: str) -> bytes:
    prs = Presentation()
    prs.slide_width, prs.slide_height = E(SLIDE_W), E(SLIDE_H)
    _theme_part(prs, code)
    layouts = _prepare_layouts(prs, code)
    fonts = theme_fonts(code)
    for i, s in enumerate(deck["slides"]):
        slide = prs.slides.add_slide(layouts[s["layout"]])
        for ph in list(slide.placeholders):
            ph._element.getparent().remove(ph._element)
        for box in layout_slide(code, deck, i).boxes:
            _add(slide.shapes, box, fonts)
        text = notes(s)
        if text:
            slide.notes_slide.notes_text_frame.text = text
    prs.core_properties.title = deck["doc_title"]
    prs.core_properties.subject = f"{deck['file']} の要約スライド（{THEMES[code]['name']} テーマ）"
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


