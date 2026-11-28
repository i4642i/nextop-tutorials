"""Makes samples/sample_report.pdf: a small made-up report (headings, paragraphs, two tables, one picture) to try the flow on.

Run:  python make_sample_pdf.py
The text is invented for this tutorial. The PDF is drawn with a Korean font that is already on your computer
(see functions/_common.py find_font); no font file is shipped with the tutorial.
"""
import io
import pathlib
import sys

from functions._common import find_font, register_fonts

ROOT = pathlib.Path(__file__).resolve().parent

TITLE = "별빛마을 작은도서관 2026년 이용 현황 보고서"
BLOCKS = [
    ("h1", "1. 개요"),
    ("p", "별빛마을 작은도서관은 2026년 한 해 동안 방문자와 대출이 모두 늘었다. 이 보고서는 분기별 이용 현황, 월별 방문자, "
          "프로그램 만족도를 정리하고 내년의 개선 과제를 제안한다."),
    ("h1", "2. 이용 현황"),
    ("p", "연간 방문자는 모두 12,400명으로 전년보다 18퍼센트 늘었다. 방문자는 가을에 가장 많았고, 대출은 3분기에 가장 크게 늘었다."),
    ("caption", "표 1. 분기별 방문자와 대출 권수"),
    ("table", [["분기", "방문자(명)", "대출(권)", "전년 대비"],
               ["1분기", "2,600", "4,100", "+9%"],
               ["2분기", "3,000", "4,800", "+14%"],
               ["3분기", "3,300", "5,900", "+27%"],
               ["4분기", "3,500", "5,200", "+21%"]]),
    ("figure", None),
    ("caption", "그림 1. 월별 방문자 수 (10월이 가장 많음)"),
    ("pagebreak", None),
    ("h1", "3. 프로그램 만족도"),
    ("p", "작은도서관은 올해 세 가지 프로그램을 운영했다. 참여자 설문에서 책 읽어 주기 모임의 만족도가 가장 높았다."),
    ("caption", "표 2. 프로그램별 참여자와 만족도 (5점 만점)"),
    ("table", [["프로그램", "참여(명)", "만족도"],
               ["책 읽어 주기 모임", "420", "4.7"],
               ["어린이 글쓰기 교실", "260", "4.4"],
               ["어르신 스마트폰 교실", "180", "4.2"]]),
    ("h1", "4. 개선 과제"),
    ("p", "저녁 시간 방문자가 늘면서 평일 개관 시간을 한 시간 늘려 달라는 요청이 많았다. 또 어르신 스마트폰 교실은 대기자가 있어 "
          "한 반을 더 열어야 한다는 의견이 나왔다."),
    ("h1", "5. 결론"),
    ("p", "2026년은 방문자와 대출이 모두 늘고 프로그램 만족도도 높았다. 내년에는 평일 개관 시간을 늘리고 어르신 스마트폰 교실을 한 반 "
          "더 여는 것을 우선 과제로 제안한다."),
]
MONTHLY = [610, 760, 880, 920, 980, 1010, 940, 1050, 1180, 1290, 1020, 760]    # sums to 12,400 (the report's total)


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
        d.text((x0 + 35, 450), f"{i + 1}월", fill="black", font=font, anchor="mt")
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
