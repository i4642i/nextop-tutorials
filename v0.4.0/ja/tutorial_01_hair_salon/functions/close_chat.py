"""Flow `chat_end` (run by the chat server when the customer ends the chat, with the chat's subject): delete this
chat's consult rows. What must stay was written by the book and change_booking tools (bookings, customers); rows of a
chat that never ends go one day after they were written (expire_after). A worker deletes nothing: deleting is this
function's right."""
from functions._salon import rows_of

NAME = "close_chat"
DESC = "Delete the chat's consult rows when the chat ends"
START = True
FILES_IN = True          # files/consult: this customer's rows (read subject, delete)
INPUTS = [{"name": "_subject", "description": "the chat's customer id (set by the program)"}]
OUTPUTS = [{"name": "closed", "schema": {"type": "object"}}]


def run(ctx, inputs):
    gone = [r["address"] for r in rows_of(inputs.get("files/consult"))]
    return {"closed": {"deleted": len(gone)}, "_deletes": gone}
