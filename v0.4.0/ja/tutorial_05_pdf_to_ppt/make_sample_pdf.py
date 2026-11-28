"""Makes samples/sample_report.pdf: a small made-up report (headings, paragraphs, two tables, one picture) to try the flow on.

Run:  python make_sample_pdf.py
The text is invented for this tutorial. The PDF is drawn with a Japanese font that is already on your computer
(see functions/_common.py find_font); no font file is shipped with the tutorial.
"""
import io
import pathlib
import sys

from functions._common import find_font, register_fonts

ROOT = pathlib.Path(__file__).resolve().parent

TITLE = "ほしあかり町図書館 2026年 利用状況報告書"
BLOCKS = [
    ("h1", "1. 概要"),
    ("p", "ほしあかり町図書館では、2026年の一年間で来館者数と貸出冊数がともに増えた。本報告書では、四半期ごとの利用状況、"
          "月ごとの来館者数、催しの満足度をまとめ、来年の改善課題を提案する。"),
    ("h1", "2. 利用状況"),
    ("p", "年間の来館者数は合計12,400人で、前年より18パーセント増えた。来館者は秋に最も多く、貸出冊数は第3四半期に最も大きく伸びた。"),
    ("caption", "表1. 四半期ごとの来館者数と貸出冊数"),
    ("table", [["四半期", "来館者（人）", "貸出（冊）", "前年比"],
               ["第1四半期", "2,600", "4,100", "+9%"],
               ["第2四半期", "3,000", "4,800", "+14%"],
               ["第3四半期", "3,300", "5,900", "+27%"],
               ["第4四半期", "3,500", "5,200", "+21%"]]),
    ("figure", None),
    ("caption", "図1. 月ごとの来館者数（10月が最も多い）"),
    ("pagebreak", None),
    ("h1", "3. 催しの満足度"),
    ("p", "図書館は今年、三つの催しを開いた。参加者アンケートでは、読み聞かせの会の満足度が最も高かった。"),
    ("caption", "表2. 催しごとの参加者数と満足度（5点満点）"),
    ("table", [["催し", "参加（人）", "満足度"],
               ["読み聞かせの会", "420", "4.7"],
               ["子ども作文教室", "260", "4.4"],
               ["シニア向けスマホ教室", "180", "4.2"]]),
    ("h1", "4. 改善課題"),
    ("p", "夕方の来館者が増えたため、平日の開館時間を1時間延ばしてほしいという要望が多く寄せられた。また、シニア向けスマホ教室は"
          "順番待ちの人がいるため、もう1クラス開くべきだという意見が出た。"),
    ("h1", "5. 結論"),
    ("p", "2026年は来館者数と貸出冊数がともに増え、催しの満足度も高かった。来年は平日の開館時間を延ばし、シニア向けスマホ教室を"
          "もう1クラス開くことを優先課題として提案する。"),
]
MONTHLY = [610, 760, 880, 920, 980, 1010, 940, 1050, 1180, 1290, 1020, 760]    # sums to 12,400 (the report's total)


def chart_png() -> bytes:
    """A plain bar chart of MONTHLY (months 1-12) as a PNG picture."""
    from PIL import Image, ImageDraw, ImageFont
    w, h = 1200, 520
    im = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(find_font()[0], 26, index=0)
    top = max(MONTHLY)
    for i, v in enumerate(MONTHLY):
        x0 = 60 + i * 95
        y0 = 440 - int(v / top * 360)
        d.rectangle([x0, y0, x0 + 70, 440], fill=(31, 58, 104) if v < top else (198, 70, 50))
        d.text((x0 + 35, 450), f"{i + 1}月", fill="black", font=font, anchor="mt")
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
    title = ParagraphStyle("title", fontName=bold, fontSize=22, leading=30, spaceAfter=10, wordWrap="CJK")
    h1 = ParagraphStyle("h1", fontName=bold, fontSize=14, leading=20, spaceBefore=14, spaceAfter=6, wordWrap="CJK")
    body = ParagraphStyle("body", fontName=regular, fontSize=10, leading=14.5, spaceAfter=6, wordWrap="CJK")
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
