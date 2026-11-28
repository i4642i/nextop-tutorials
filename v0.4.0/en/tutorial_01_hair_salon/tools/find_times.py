"""Free start times per day and designer, from the designers' hours and every booking (read with the reception's
rights). The result has times only: a taken time is simply not there, never whose it is. To move a booking, the
booking must be one of the verified customer's (the identity check); any other id is refused without a word about it."""
import datetime

from functions._salon import (all_bookings, day_label, free_starts, quote, records, salon, style_index, style_names,
                              verified_bookings, view_rows)

NAME = "find_times"
DESC = ("Find free start times in the next days. For a new booking give styles (the chosen menu names, one per "
        "service: their minutes add up); to move a booking give "
        "booking (its id from the step notice: its own slot counts as free, its minutes are used). Returns each day with its "
        "date and weekday (use them to understand words like 'Saturday' or 'tomorrow') and, per designer, the free "
        "start times. Give designer only when the customer asked for one, and from (YYYY-MM-DD) to start at a later "
        "day. Offer the customer one of the returned times with the designer's name; never a time that is not in the "
        "result.")
GROUP = "salon"
SCHEMA = {
    "type": "object",
    "properties": {
        "styles": {"type": "array", "minItems": 1, "uniqueItems": True,
                   "items": {"type": "string", "enum": style_names()}},
        "booking": {"type": "string", "description": "the id of the verified customer's booking to move (instead of "
                                                     "styles)"},
        "designer": {"type": "string", "enum": list(salon()["designers"])},
        "from": {"type": "string", "description": "YYYY-MM-DD, the first day to look at (default today)"},
        "days": {"type": "integer", "minimum": 1, "maximum": 14, "default": 7,
                 "description": "how many days to look at"},
    },
}


def run(ctx, args):
    schedule = all_bookings(ctx)
    leave_out = ""
    if args.get("booking"):
        mine = verified_bookings(records(view_rows(ctx, "consult")), schedule)["bookings"]
        own = next((f for f in mine if f.get("booking") == args["booking"]), None)
        if own is None:
            return {"error": "give the booking id of the verified customer (the step notice lists them after the "
                             "identity check)"}
        minutes, leave_out = int(own["minutes"]), own["booking"]
    elif args.get("styles"):
        services = [style_index()[n][0] for n in args["styles"]]
        if len(set(services)) < len(services):
            return {"error": "give one style per service"}
        minutes = quote(args["styles"])["minutes"]
    else:
        return {"error": "give styles (a new booking) or booking (to move one)"}
    try:
        start = datetime.date.fromisoformat(args["from"]) if args.get("from") else datetime.date.today()
    except ValueError:
        return {"error": "from must be YYYY-MM-DD"}
    designers = salon()["designers"]
    names = [args["designer"]] if args.get("designer") else list(designers)
    today = datetime.date.today()
    days = []
    for n in range(args.get("days", 7)):
        day = max(start, today) + datetime.timedelta(days=n)
        free = {f"{d} ({designers[d]['name']})": free_starts(schedule, d, day, minutes, leave_out=leave_out)
                for d in names}
        free = {k: v for k, v in free.items() if v}
        tag = " today" if day == today else " tomorrow" if day == today + datetime.timedelta(days=1) else ""
        days.append({"day": day_label(day) + tag, "free": free or "no free time"})
    return {"minutes": minutes, "days": days}
