"""Sorts the parts of the PDF into text, tables and figures. No model: the file server's reader already did the cutting."""
from functions._pdf import build_report

NAME = "classify"
DESC = "Count and list the text sections, tables and figures of the PDF"
FILES_IN = True                       # the flow hands it the PDF's records (share line intake -> classify)
OUTPUTS = [{"name": "report", "schema": {
    "type": "object",
    "properties": {
        "file": {"type": "string"}, "pages": {"type": "integer"}, "document": {"type": "string"},
        "counts": {"type": "object"},
        "sections": {"type": "array", "items": {"type": "object"}},
        "tables": {"type": "array", "items": {"type": "object"}},
        "figures": {"type": "array", "items": {"type": "object"}}},
    "required": ["file", "pages", "counts", "sections", "tables", "figures"]}}]


def run(ctx, inputs):
    try:
        return {"report": build_report(inputs.get("files/pdf", []), inputs["intake/brief"]["file"])}
    except ValueError as e:
        return {"error": str(e)}
