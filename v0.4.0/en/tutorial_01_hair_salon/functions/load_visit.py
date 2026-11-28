"""Start of the flow `booking_notes` (run by the chat server in the background after a booking): the finished chat and
the booking as bookings holds it (read with this function's own access), for the summary, the prep memo and the mail."""
import datetime

from functions._salon import day_label, fields_of, rows_of

NAME = "load_visit"
DESC = "Take a booking chat and its booking row"
START = True
FILES_IN = True          # files/bookings (read all)
INPUTS = [
    {"name": "transcript", "description": "the chat: [{role: user|assistant, content}, ...], oldest first"},
    {"name": "booking", "description": "the booking id the chat made"},
]
OUTPUTS = [{"name": "visit", "schema": {
    "type": "object",
    "properties": {"booking": {"type": "object"}, "transcript": {"type": "array", "items": {"type": "object"}}},
    "required": ["booking", "transcript"]}}]


def run(ctx, inputs):
    b = next((f for f in fields_of(rows_of(inputs.get("files/bookings"))) if f["booking"] == inputs["booking"]), None)
    if b is None:
        return {"error": f"booking {inputs['booking']} is not in bookings"}
    return {"visit": {"booking": dict(b, day=day_label(datetime.date.fromisoformat(b["date"]))),
                      "transcript": inputs["transcript"]}}
