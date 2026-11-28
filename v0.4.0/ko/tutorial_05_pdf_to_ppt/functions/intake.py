"""Start of the flow: takes one PDF and a theme, puts the PDF on the file server `pdf` and sets the amounts.

The amounts (how many slides, how many section dividers) come from the size of the document, here and nowhere else:
the workers get them in the brief and never count for themselves.
"""
import datetime
import pathlib

from functions._common import ROOT
from functions._deck import THEMES, amounts, theme_code, writing_guide

NAME = "intake"
DESC = "Upload the PDF the person gave to the pdf file server and set the number of slides from its size"
START = True
FILES_OUT = True                      # it uploads (_uploads) and shares the file with the next blocks
INPUTS = [{"name": "pdf_path", "description": "path of the PDF (absolute, or relative to the project folder)", "required": True},
          {"name": "theme", "description": "slide theme: basic (기본), dark (다크) or academic (학술); basic when not given",
           "required": False}]
OUTPUTS = [{"name": "brief", "schema": {
    "type": "object",
    "properties": {"file": {"type": "string"}, "today": {"type": "string"}, "theme": {"type": "string"},
                   "pages": {"type": "integer"}, "slides": {"type": "integer"}, "sections": {"type": "integer"},
                   "layouts": {"type": "object"}},
    "required": ["file", "today", "theme", "pages", "slides", "sections", "layouts"]}}]


def run(ctx, inputs):
    path = pathlib.Path(inputs["pdf_path"])
    path = path if path.is_absolute() else ROOT / path
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return {"error": f"pdf_path must be an existing .pdf file: {inputs['pdf_path']}"}
    theme = theme_code(inputs.get("theme") or "basic")
    if theme is None:
        names = ", ".join(f"{code} ({t['name']})" for code, t in THEMES.items())
        return {"error": f"theme must be one of {names}, not {inputs.get('theme')!r}"}
    import pypdfium2
    with pypdfium2.PdfDocument(str(path)) as doc:
        pages = len(doc)
    brief = {"file": path.name, "today": datetime.date.today().isoformat(), "theme": theme, "pages": pages,
             **amounts(pages), "layouts": writing_guide()}
    return {"brief": brief,
            "_uploads": [{"file_server": "pdf", "file": str(path), "title": path.name, "source": f"PDF given to the flow: {path.name}"}]}
