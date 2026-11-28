"""Cuts the outline into one piece per slide, so the writer writes and saves the slides one at a time.

Each piece is one slide of the outline with what the writer needs for it: its number, layout, topic and limits, its
text parts with their paragraph addresses, the table or figure the program will place, and for a section slide the
topics of the slides in that section (covers). The order of the slides is the outline's: the gather block after the
writer gives the written slides back in piece order.
"""
from functions._deck import slide_pieces

NAME = "split_slides"
DESC = "Cut the outline into one piece per slide (the writer writes one slide per conversation)"
KIND = "split"
OUTPUTS = [{"name": "slide", "from": "outline", "schema": {
    "type": "object",
    "properties": {"no": {"type": "integer"}, "of": {"type": "integer"}, "layout": {"type": "string"},
                   "topic": {"type": "string"}, "covers": {"type": "array"}, "title_chars": {"type": "integer"},
                   "bullets": {"type": "array"}, "bullet_chars": {"type": "integer"}, "parts": {"type": "array"},
                   "table": {"type": "object"}, "figure": {"type": "object"}, "section_no": {"type": "integer"},
                   "document": {"type": "object"}},
    "required": ["no", "of", "layout", "topic", "bullets", "parts", "table", "figure", "document"]}}]


def run(ctx, inputs):
    pieces = slide_pieces(inputs["intake/brief"], inputs["classify/report"], inputs["planner/outline"])
    return [{"slide": p} for p in pieces]
