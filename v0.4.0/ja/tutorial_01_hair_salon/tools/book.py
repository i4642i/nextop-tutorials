"""Book the visit the recorded consult rows describe. book has no arguments: the program reads the rows the reception
wrote with put (name, phone, service, style, wish_time, designer, the service checklist, agree) and every booking,
through the reception's views (its rights on bookings: read all, write). It checks every item and the slot, then
writes the booking (status pending: the slot is held until the designer answers) and schedule.html, keeps what the
customer told about their hair in customers, and finishes the purpose in consult. A refusal names everything that is
still missing at once; a taken time names the designer, never whose booking it is.

Two chats booking the same slot at the same moment: the slot is checked just before the write, in one process; there is
no lock across processes (a real service keeps bookings in a database and lets it refuse the second one: README)."""
from functions._salon import (all_bookings, booking_draft, booking_line, finish_purpose, records, rows_of, view_rows,
                              write_rows, write_schedule)

NAME = "book"
DESC = ("Book the visit from what is recorded in fs://consult (no arguments): every required booking item, the "
        "service questions and the customer's agreement to the proposed time (agree, recorded after wish_time and "
        "designer). The booking is created as pending: the slot is held, and the customer gets a confirmation text "
        "only after the designer approves. When something is missing or the time is not free, nothing is booked and "
        "the result names every problem.")
GROUP = "salon"
SCHEMA = {"type": "object", "properties": {}}


def hair_note(ctx: dict, b: dict) -> str:
    """What the customer told about their hair: the customers row of this phone (if any) and the new answers."""
    old = next((r["fields"].get("hair_note", "") for r in rows_of(view_rows(ctx, "customers"))
                if r["fields"].get("phone") == b["phone"]), "")
    lines = [x for x in old.splitlines() if x.strip()]
    lines += [x for x in str(b.get("answers") or "").splitlines() if x.strip() and x not in lines]
    return "\n".join(lines)


def run(ctx, args):
    rec = records(view_rows(ctx, "consult"))
    every = all_bookings(ctx)
    draft, problems = booking_draft(rec, every)
    if problems:
        return {"error": "not booked; " + "; ".join(problems)}
    wrong = write_rows(ctx, "bookings", [draft])
    if wrong:
        return {"error": f"not booked; {wrong}"}
    write_schedule([b for b in every if b["booking"] != draft["booking"]] + [draft])
    note = hair_note(ctx, draft)
    warnings = [w for w in (write_rows(ctx, "customers", [{"phone": draft["phone"], "name": draft["name"],
                                                          "hair_note": note}]) if note else None,
                            finish_purpose(ctx, "booking", rec)) if w]
    out = {"booked": True, "status": "pending", "booking": draft["booking"], "line": booking_line(draft),
           "designer": draft["designer_name"],
           "note": f"the slot is held but not confirmed yet: {draft['designer_name']} checks it, and the customer "
                   f"gets a confirmation text message after {draft['designer_name']} approves; the consultation summary "
                   f"and the whole chat go to {draft['designer_name']} by mail"}
    if warnings:
        out["warning"] = "; ".join(warnings)
    return out
