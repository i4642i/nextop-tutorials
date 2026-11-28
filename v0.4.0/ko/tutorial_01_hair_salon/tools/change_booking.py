"""Change or cancel a booking from what is recorded in fs://consult (no arguments). The program runs the identity check
(the recorded name and phone against every booking, read with the reception's rights), so only a booking of the
verified customer can be changed, whichever browser the chat comes from; then it checks the change items, the
customer's agreement (change_agree for a new time, cancel_agree for a cancel) and the new slot. It writes the booking
(a changed booking is pending again; a cancelled one keeps its row with status cancelled and frees the slot),
schedule.html and the designer's mail, and finishes the purpose in consult. Before the check passes the result says
nothing about any booking."""
from functions._approval import tell_designer
from functions._salon import (all_bookings, booking_line, change_draft, finish_purpose, records, verified_bookings,
                              view_rows, write_rows, write_schedule)

NAME = "change_booking"
DESC = ("Change or cancel the booking recorded in fs://consult (no arguments): change_booking (the booking id from the "
        "step notice), change_action (change or cancel), for a change change_time, optional change_designer and "
        "change_agree (the customer agreed to the new time), for a cancel optional cancel_reason and cancel_agree (the "
        "customer confirmed the cancel). Refused until the identity check matches the recorded name and phone. A "
        "changed booking waits for the designer's approval again; a cancelled one frees the slot.")
GROUP = "salon"
SCHEMA = {"type": "object", "properties": {}}


def run(ctx, args):
    rec = records(view_rows(ctx, "consult"))
    every = all_bookings(ctx)
    ident = verified_bookings(rec, every)
    if ident["state"] == "none":
        return {"error": "not changed; the identity check needs the customer's name and mobile number (items name and phone)"}
    if ident["state"] != "ok":
        return {"error": "not changed; the identity check failed: no booking has this name and phone"}
    changed, problems = change_draft(rec, ident, ident["bookings"], every)
    if problems:
        return {"error": "not changed; " + "; ".join(problems)}
    old = next(b for b in ident["bookings"] if b["booking"] == changed["booking"])
    wrong = write_rows(ctx, "bookings", [changed])
    if wrong:
        return {"error": f"not changed; {wrong}"}
    write_schedule([b for b in every if b["booking"] != changed["booking"]] + [changed])
    mail = tell_designer(old, changed)
    out = {"changed": True, "status": changed["status"], "line": booking_line(changed), "mail": mail}
    wrong = finish_purpose(ctx, "change", rec)
    if wrong:
        out["warning"] = wrong
    if changed["status"] == "cancelled":
        out["note"] = "the booking is cancelled and the slot is free; the designer was told"
    else:
        out["note"] = (f"the new time is held but not confirmed yet: {changed['designer_name']} checks it, and the "
                       "customer gets a confirmation text message after the approval")
    return out
