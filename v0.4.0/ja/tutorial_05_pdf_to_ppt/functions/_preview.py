"""PNG previews of the slides, drawn with Pillow from the same boxes the .pptx is written from.

LibreOffice is not needed: the previews are drawn here, line by line as _deck wrapped the text. PowerPoint draws the
.pptx itself with its own text engine, so a line may break a word earlier or later there; the fit check leaves 6% of
every box free for that.
"""
import io
import pathlib

from functions._deck import SLIDE_H, SLIDE_W, font_chars, font_file, layout_slide

WIDTH = 1600                                  # preview width in pixels (16:9)
FALLBACKS = [("C:/Windows/Fonts/seguisym.ttf", 0), ("C:/Windows/Fonts/cambria.ttc", 1),
             ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 0), ("/Library/Fonts/Arial Unicode.ttf", 0)]


def _rgb(hex_color: str) -> tuple[int, int, int]:
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def _font(code, box, k):
    path, index = font_file(code, box["font"], box["bold"])
    from PIL import ImageFont
    return ImageFont.truetype(path, max(1, round(box["size"] * k)), index=index)


def _fallback(size_px: int):
    """A font for characters the slide font lacks (PowerPoint also falls back to another font for them)."""
    from PIL import ImageFont
    for path, index in FALLBACKS:
        if pathlib.Path(path).is_file():
            return ImageFont.truetype(path, size_px, index=index)
    return None


def _runs(code, box, line):
    """The line cut into (text, drawn by the slide font?) pieces."""
    cmap = font_chars(*font_file(code, box["font"], box["bold"]))
    out = []
    for ch in line:
        ok = cmap is None or ch.isspace() or ord(ch) in cmap
        if out and out[-1][1] == ok:
            out[-1][0] += ch
        else:
            out.append([ch, ok])
    return out


def _lines(draw, code, box, k, lines, x, y, w, h, color):
    font = _font(code, box, k)
    other = _fallback(font.size)
    lh = box["lh"]
    top = y + ((h - len(lines) * lh) / 2 if box.get("anchor") == "middle" else 0)
    for i, line in enumerate(lines):
        runs = [(t, font if ok or other is None else other) for t, ok in _runs(code, box, line)]
        lw = sum(f.getlength(t) for t, f in runs) / k
        lx = x + (w - lw) / 2 if box["align"] == "center" else x + w - lw if box["align"] == "right" else x
        base = (top + i * lh + lh * 0.80) * k
        px = lx * k
        for t, f in runs:
            draw.text((px, base), t, font=f, fill=_rgb(color), anchor="ls")
            px += f.getlength(t)


def _mark(draw, marker, x, mid, k):
    """The bullet mark (as PowerPoint draws ■, ● or – in the accent colour)."""
    color = _rgb(marker["color"])
    if marker["shape"] == "square":
        draw.rectangle([x * k, (mid - 4) * k, (x + 8) * k, (mid + 4) * k], fill=color)
    elif marker["shape"] == "dot":
        draw.ellipse([x * k, (mid - 4.5) * k, (x + 9) * k, (mid + 4.5) * k], fill=color)
    else:
        draw.rectangle([x * k, (mid - 1) * k, (x + 11) * k, (mid + 1) * k], fill=color)


def render_slide(code: str, deck: dict, index: int, width: int = WIDTH):
    """The slide as a PIL image `width` pixels wide."""
    from PIL import Image, ImageDraw
    k = width / SLIDE_W
    sl = layout_slide(code, deck, index)
    im = Image.new("RGB", (width, round(SLIDE_H * k)), _rgb(sl.bg))
    draw = ImageDraw.Draw(im)
    for box in sl.decor + sl.boxes:
        x, y, w, h = box["x"], box["y"], box["w"], box["h"]
        rect = [x * k, y * k, (x + w) * k - 1, (y + h) * k - 1]
        if box["kind"] == "rect":
            if box.get("radius"):
                draw.rounded_rectangle(rect, radius=box["radius"] * k, fill=_rgb(box["fill"]))
            else:
                draw.rectangle(rect, fill=_rgb(box["fill"]))
        elif box["kind"] == "oval":
            draw.ellipse(rect, fill=_rgb(box["fill"]))
        elif box["kind"] == "text":
            _lines(draw, code, box, k, box["lines"], x, y, w, h, box["color"])
        elif box["kind"] == "paras":
            cy, indent = y, box["indent"]
            for para in box["paras"]:
                cy += para["before"]
                if box["marker"]:
                    _mark(draw, box["marker"], x, cy + para["lh"] / 2, k)
                height = len(para["lines"]) * para["lh"]
                _lines(draw, code, para, k, para["lines"], x + indent, cy, w - indent, height, para["color"])
                cy += height
        elif box["kind"] == "image":
            pic = Image.open(box["path"]).convert("RGB").resize((round(w * k), round(h * k)), Image.LANCZOS)
            im.paste(pic, (round(x * k), round(y * k)))
        elif box["kind"] == "table":
            cy, body_n = y, 0
            for row in box["rows"]:
                fill = box["head_bg"] if row["header"] else (box["row_alt"] if body_n % 2 else box["row_bg"])
                color = box["head_text"] if row["header"] else box["row_text"]
                body_n += 0 if row["header"] else 1
                cx = x
                for c, cw in enumerate(box["widths"]):
                    draw.rectangle([cx * k, cy * k, (cx + cw) * k, (cy + row["h"]) * k], fill=_rgb(fill))
                    cell = {"font": "body", "bold": row["header"], "size": box["size"], "lh": box["lh"], "anchor": "middle",
                            "align": "left" if c == 0 else "center"}
                    _lines(draw, code, cell, k, row["lines"][c], cx + box["pad_x"], cy, cw - 2 * box["pad_x"], row["h"], color)
                    cx += cw
                cy += row["h"]
    return im


def render_all(code: str, deck: dict, width: int = WIDTH) -> list[bytes]:
    out = []
    for i in range(len(deck["slides"])):
        buf = io.BytesIO()
        render_slide(code, deck, i, width).save(buf, format="PNG", optimize=True)
        out.append(buf.getvalue())
    return out


def contact_sheet(pngs: list[bytes], columns: int = 3, thumb: int = 520, gap: int = 18, background: str = "E5E7EB") -> bytes:
    """All slides as one picture (for the README and the mail)."""
    from PIL import Image
    th = round(thumb * SLIDE_H / SLIDE_W)
    rows = -(-len(pngs) // columns)
    sheet = Image.new("RGB", (columns * thumb + (columns + 1) * gap, rows * th + (rows + 1) * gap), _rgb(background))
    for n, data in enumerate(pngs):
        pic = Image.open(io.BytesIO(data)).convert("RGB").resize((thumb, th), Image.LANCZOS)
        sheet.paste(pic, (gap + (n % columns) * (thumb + gap), gap + (n // columns) * (th + gap)))
    buf = io.BytesIO()
    sheet.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


