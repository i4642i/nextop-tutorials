"""Flow `seed` (run by seed.py, no subject): write the example bookings of data/seed_bookings.json (confirmed),
counted from tomorrow, into bookings. A booking id that already exists is left alone."""
import datetime
import json

from functions._salon import ROOT, fields_of, now, quote, rows_of, salon, table_unit, uploads, write_schedule

NAME = "seed_bookings"
DESC = "Write the example bookings"
START = True
FILES_IN = True          # files/bookings (read all, write)
FILES_OUT = True
INPUTS = [{"name": "seed", "description": "anything (the flow needs an input)", "required": False}]
OUTPUTS = [{"name": "seeded", "schema": {"type": "object"}}]


def nth_workday(designer: str, n: int) -> datetime.date:
    days, day = salon()["designers"][designer]["days"], datetime.date.today()
    while n > 0:
        day += datetime.timedelta(days=1)
        n -= day.weekday() in days
    return day


def run(ctx, inputs):
    books = inputs.get("files/bookings") or []
    have = {f["booking"]: f for f in fields_of(rows_of(books))}
    data = salon()
    new = []
    for s in json.loads((ROOT / "data" / "seed_bookings.json").read_text(encoding="utf-8"))["bookings"]:
        date = nth_workday(s["designer"], s["nth_workday"]).isoformat()
        bid = f"{date}-{s['time'].replace(':', '')}-{s['designer']}"
        if bid in have:
            continue
        q = quote(s["styles"])
        new.append({"booking": bid, "status": "confirmed", "date": date, "time": s["time"], "designer": s["designer"],
                    "designer_name": data["designers"][s["designer"]]["name"], "services": s["services"],
                    "service_labels": q["services"], "styles": q["styles"], "price": q["price"],
                    "minutes": q["minutes"], "name": s["name"], "phone": s["phone"], "answers": "-",
                    "booked_at": f"{now():%Y-%m-%d %H:%M}"})
    write_schedule(list(have.values()) + new)
    out = {"seeded": {"new": len(new), "kept": len(have)}}
    if new:
        out["_uploads"] = [uploads(table_unit(books), "bookings", new, "example bookings")]
    return out
