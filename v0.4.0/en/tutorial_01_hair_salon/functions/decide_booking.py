"""Flow `decide` (run by the designer's approve / decline link or approve.py, no subject): the designer's answer.

approve: the booking is confirmed and the customer gets the confirmation text; decline: the slot is free again and the
customer gets a short text asking for another time. A booking that is not pending is left as it is."""
from functions._approval import confirmed_text, declined_text, who
from functions._notify import send_sms
from functions._salon import data_dir, fields_of, rows_of, table_unit, uploads, write_schedule

NAME = "decide_booking"
DESC = "Confirm or decline a pending booking and text the customer"
START = True
FILES_IN = True          # files/bookings (read all, write)
FILES_OUT = True
INPUTS = [{"name": "booking", "description": "the booking id"},
          {"name": "approve", "description": "true: approve, false: decline"}]
OUTPUTS = [{"name": "decision", "schema": {"type": "object"}}]


def run(ctx, inputs):
    books = inputs.get("files/bookings") or []
    rows = {f["booking"]: f for f in fields_of(rows_of(books))}
    b = rows.get(str(inputs["booking"]))
    if b is None:
        return {"decision": {"code": "refused", "message": "The booking was not found."}}
    if b["status"] != "pending":
        done = {"confirmed": "confirmed", "declined": "declined", "cancelled": "canceled"}.get(b["status"], b["status"])
        return {"decision": {"code": "done", "message": f"This booking is already {done}. Nothing was changed."}}
    approve = bool(inputs["approve"])
    b = dict(b, status="confirmed" if approve else "declined")
    rows[b["booking"]] = b
    write_schedule(list(rows.values()))
    sms = confirmed_text(b) if approve else declined_text(b)
    ok, note = send_sms(b["phone"], sms)
    folder = data_dir() / "memos"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{b['booking']}.sms.txt").write_text(f"{'sent' if ok else 'FAILED'}: {note}\n\n{sms}\n", encoding="utf-8")
    msg = (f"{who(b)} is confirmed. The customer was sent the confirmation text." if approve else
           f"{who(b)} is declined. The time is free again, and the customer was sent a text.")
    if not ok:
        msg = msg.replace("was sent", f"could not be sent ({note})")
    return {"decision": {"code": "ok", "message": msg, "status": b["status"]},
            "_uploads": [uploads(table_unit(books), "bookings", [b], "the designer's answer")]}
