"""Makes samples/sample_report.pdf: a small made-up report (headings, paragraphs, two tables, one picture) to try the flow on.

Run:  python make_sample_pdf.py
The text is invented for this tutorial. The PDF is drawn with a font that is already on your computer
(see functions/_common.py find_font); no font file is shipped with the tutorial.
"""
import io
import pathlib
import sys

from functions._common import find_font, register_fonts

ROOT = pathlib.Path(__file__).resolve().parent

TITLE = "Starlight Village Library: 2026 Usage Report"
BLOCKS = [
    ("h1", "1. Overview"),
    ("p", "Starlight Village Library saw more visitors and more loans in 2026. This report sums up use per quarter, "
          "visitors per month and how satisfied people were with our programs, and it proposes next year's priorities."),
    ("h1", "2. Usage"),
    ("p", "The library had 12,400 visitors this year, 18 percent more than last year. Visits peaked in the fall, and "
          "loans grew the most in the third quarter."),
    ("caption", "Table 1. Visitors and loans per quarter"),
    ("table", [["Quarter", "Visitors", "Loans", "Change vs 2025"],
               ["Q1", "2,600", "4,100", "+9%"],
               ["Q2", "3,000", "4,800", "+14%"],
               ["Q3", "3,300", "5,900", "+27%"],
               ["Q4", "3,500", "5,200", "+21%"]]),
    ("figure", None),
    ("caption", "Figure 1. Visitors per month (October was the busiest)"),
    ("pagebreak", None),
    ("h1", "3. Program satisfaction"),
    ("p", "The library ran three programs this year. In the visitor survey, the story time group got the highest "
          "satisfaction score."),
    ("caption", "Table 2. Participants and satisfaction per program (out of 5)"),
    ("table", [["Program", "Participants", "Satisfaction"],
               ["Story time group", "420", "4.7"],
               ["Kids' writing class", "260", "4.4"],
               ["Smartphone class for seniors", "180", "4.2"]]),
    ("h1", "4. Next steps"),
    ("p", "As more people came in the evening, many asked us to stay open one hour longer on weekdays. The smartphone "
          "class for seniors has a waiting list, so we were also asked to open one more class."),
    ("h1", "5. Conclusion"),
    ("p", "In 2026 both visitors and loans grew, and people were happy with the programs. For next year we propose to "
          "stay open one hour longer on weekdays and to open one more smartphone class for seniors."),
]
MONTHLY = [610, 760, 880, 920, 980, 1010, 940, 1050, 1180, 1290, 1020, 760]    # sums to 12,400 (the report's total)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def chart_png() -> bytes:
    """A plain bar chart of MONTHLY (months 1-12) as a PNG picture."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 1200, 520
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(find_font()[0], 26)
    top = max(MONTHLY)
    for i, v in enumerate(MONTHLY):
        x0 = 60 + i * 95
        y0 = 440 - int(v / top * 360)
        d.rectangle([x0, y0, x0 + 70, 440], fill=(31, 58, 104) if v < top else (198, 70, 50))
        d.text((x0 + 35, 450), MONTHS[i], fill="black", font=font, anchor="mt")
        d.text((x0 + 35, y0 - 8), f"{v:,}", fill="black", font=font, anchor="mb")
    d.line([(50, 440), (1160, 440)], fill="black", width=2)
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def make_pdf() -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    regular, bold = register_fonts()
    title = ParagraphStyle("title", fontName=bold, fontSize=22, leading=30, spaceAfter=10)
    h1 = ParagraphStyle("h1", fontName=bold, fontSize=14, leading=20, spaceBefore=14, spaceAfter=6)
    body = ParagraphStyle("body", fontName=regular, fontSize=10, leading=14.5, spaceAfter=6)
    caption = ParagraphStyle("caption", parent=body, fontSize=9.5, textColor=colors.HexColor("#444444"), spaceBefore=8, spaceAfter=4)
    flow = [Paragraph(TITLE, title)]
    for kind, value in BLOCKS:
        if kind == "h1":
            flow.append(Paragraph(value, h1))
        elif kind == "p":
            flow.append(Paragraph(value, body))
        elif kind == "pagebreak":
            flow.append(PageBreak())
        elif kind == "caption":
            flow.append(Paragraph(value, caption))
        elif kind == "table":
            t = Table(value, hAlign="LEFT", colWidths=[48 * mm] + [32 * mm] * (len(value[0]) - 1))
            t.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -1), regular), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                                   ("GRID", (0, 0), (-1, -1), 0.6, colors.black), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf5")),
                                   ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
            flow += [t, Spacer(1, 8)]
        else:
            png = chart_png()
            flow.append(Image(io.BytesIO(png), width=140 * mm, height=140 * mm * 520 / 1200, hAlign="LEFT"))
    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm, topMargin=20 * mm, bottomMargin=20 * mm,
                      title=TITLE).build(flow)
    return buf.getvalue()


if __name__ == "__main__":
    try:
        data = make_pdf()
    except OSError as e:
        sys.exit(f"cannot make the sample PDF: {e}")
    out = ROOT / "samples" / "sample_report.pdf"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(data)
    print(f"wrote {out} ({len(data)} bytes)")
