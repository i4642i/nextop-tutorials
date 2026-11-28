"""The identity check: the program matches the name and phone recorded in fs://consult against every booking (the
reception may read all bookings; this tool filters). verified true: only this customer's bookings. verified false: no
booking has exactly that name and phone, and nothing else is said (not whether another name has a booking)."""
from functions._salon import all_bookings, booking_line, records, verified_bookings, view_rows

NAME = "verify_customer"
DESC = ("Check the customer's identity (no arguments): the name and phone recorded in fs://consult (items name and "
        "phone) are matched against the salon's bookings. verified true: the result lists this customer's bookings. "
        "verified false: no booking has exactly that name and phone; nothing else is said.")
GROUP = "salon"
SCHEMA = {"type": "object", "properties": {}}


def run(ctx, args):
    rec = records(view_rows(ctx, "consult"))
    ident = verified_bookings(rec, all_bookings(ctx))
    if ident["state"] == "none":
        return {"error": "not checked: record the customer's name (the name only) and mobile number first (items name "
                         "and phone)"}
    if ident["state"] != "ok":
        return {"verified": False, "note": "no booking has this name and phone"}
    return {"verified": True, "bookings": [booking_line(b) for b in ident["bookings"]]}
