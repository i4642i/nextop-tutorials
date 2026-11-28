"""Salon data and rules shared by the navigator, the tools and the flow functions (files starting with '_' are not
functions).

salon.json holds designers (working days and hours), services (a menu of styles, each with its price and minutes,
and the per-service checklist) and the slot size; checklists.json holds the consult checklist of every purpose and every sentence of the step notice. The
program decides everything here: prices and minutes (from the styles the customer chose), free times, which checklist items apply, which are answered, whether a
recorded answer has the right form, and whether the recorded name and phone match a booking. Workers never do.

Where things live (file servers only):
  consult    the chat's records, written by the reception with put: purpose rows (item purpose_<id>, state open/done)
             and checklist answers (item = checklist id). Key item: writing an item again replaces it (history kept).
  bookings   one row per booking (key booking; "per_subject": false, so a booking is the same row from every chat).
             The reception may read all and write; its model gets no common tool on it (type.json "tools": []) and no
             step shows it, so only the program reads it: the tools and the navigator, through the worker's view
             ctx["file_servers"]["bookings"], which acts with the worker's rights.
  customers  what a customer told about their hair, one row per phone number, written by the book tool
The identity check is the program's (verified_bookings): the name and phone recorded in consult against every booking.
Before it passes, no tool and no notice says anything about a booking (not even whether one exists); after it passes,
only this customer's bookings. A free time can be taken, never by whom: that is the tool author's duty, since the
tools read every booking. SALON_DATA_DIR keeps outbox/, memos/ and schedule.html somewhere else (the tests do).
"""
from __future__ import annotations

import datetime
import json
import os
import pathlib
import re

from nextop.parts.field_type import phone as phone_type

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
ACTIVE = ("pending", "confirmed")          # a booking in one of these holds its slot
PURPOSE = "purpose_"                      # the item of a purpose row: purpose_<purpose id>


def data_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("SALON_DATA_DIR") or ROOT)


def salon() -> dict:
    return json.loads((ROOT / "salon.json").read_text(encoding="utf-8"))


def checklists() -> dict:
    return json.loads((ROOT / "checklists.json").read_text(encoding="utf-8"))


def text(key: str, **values) -> str:
    """A sentence of checklists.json "texts" with its {values} filled."""
    return checklists()["texts"][key].format(**values)


def day_label(day: datetime.date) -> str:
    return f"{day.isoformat()} ({WEEKDAYS[day.weekday()]})"


def when_label(when: datetime.datetime) -> str:
    return f"{day_label(when.date())} {when:%H:%M}"


def now() -> datetime.datetime:
    return datetime.datetime.now()


# ---- the menu: styles with price and minutes (salon.json services.<id>.styles) ------------------------------------
def style_index() -> dict:
    """{style name: (service id, style)} of the whole menu."""
    return {st["name"]: (sid, st) for sid, s in salon()["services"].items() for st in s["styles"]}


def style_names() -> list[str]:
    return list(style_index())


def menu_text(services: list[str]) -> str:
    """The menu names of these services as the step notice lists them (no prices, no groups)."""
    s = salon()["services"]
    return "; ".join(text("menu_of", service=s[x]["label"], names=", ".join(st["name"] for st in s[x]["styles"]))
                     for x in services if x in s)


def needs_choice(service: str) -> bool:
    """A service whose menu has one style takes it without asking."""
    return len(salon()["services"][service]["styles"]) > 1


def plan(services: list[str], value: str) -> dict:
    """The styles of a visit: for each chosen service the style named in value (comma separated menu names) or, for a
    one-style menu, its only style. {"styles": [names, in service order], "missing": [service ids], "wrong": [names
    not on the chosen services' menus], "twice": {service id: [names]}, "recommend": bool}."""
    data, index = salon(), style_index()
    names = [v.strip() for v in str(value or "").split(",") if v.strip()]
    out = {"styles": [], "missing": [], "wrong": [], "twice": {}, "recommend": data["recommend"] in names}
    for sid in services:
        mine = [n for n in names if n in index and index[n][0] == sid]
        if not needs_choice(sid):
            mine = mine or [data["services"][sid]["styles"][0]["name"]]
        if not mine:
            out["missing"].append(sid)
        elif len(mine) > 1:
            out["twice"][sid] = mine
        else:
            out["styles"].append(mine[0])
    out["wrong"] = [n for n in names if n != data["recommend"] and (n not in index or index[n][0] not in services)]
    return out


def quote(styles: list[str]) -> dict:
    """Price and minutes of one visit from the menu styles (one per service; several add up)."""
    index, s = style_index(), salon()["services"]
    picked = [index[n] for n in styles]
    return {"services": [s[sid]["label"] for sid, _st in picked], "service_ids": [sid for sid, _st in picked],
            "styles": [st["name"] for _sid, st in picked],
            "items": [{"service": s[sid]["label"], "style": st["name"], "price": st["price"], "minutes": st["minutes"]}
                      for sid, st in picked],
            "price": sum(st["price"] for _sid, st in picked), "minutes": sum(st["minutes"] for _sid, st in picked)}


def menu(services: list[str]) -> list[dict]:
    """The menu of these services with prices and minutes (price_quote without styles)."""
    s = salon()["services"]
    return [{"service": s[x]["label"], "styles": [{k: st[k] for k in ("name", "price", "minutes")}
                                                  for st in s[x]["styles"]]} for x in services]


# ---- reading rows ---------------------------------------------------------------------------------------------------
def rows_of(records_in: list[dict] | None) -> list[dict]:
    """The table rows among records (a view's list or a function's FILES_IN): those with field values."""
    return [r for r in records_in or [] if r.get("fields")]


def view_rows(ctx: dict, name: str) -> list[dict]:
    """The rows a tool or the navigator may read of file server `name` (its worker's rights; [] without a view)."""
    view = ((ctx or {}).get("file_servers") or {}).get(name)
    if view is None:
        return []
    got = view.list(limit=5000)
    return rows_of(got.get("rows") if isinstance(got, dict) else [])


def write_rows(ctx: dict, name: str, new_rows: list[dict]) -> str | None:
    """Write rows into file server `name` with the worker's write right (the view's put, which checks the fields and
    keeps old values in the history): None, or what went wrong."""
    view = ((ctx or {}).get("file_servers") or {}).get(name)
    if view is None:
        return f"no view of {name}"
    got = view.put(new_rows)
    if "error" in got:
        return str(got["error"])
    if got.get("refused"):
        return "; ".join(f"row {r['row']}: {', '.join(r['why'])}" for r in got["refused"])
    return None


def all_bookings(ctx: dict) -> list[dict]:
    """Every booking (fields) as the program reads them through the reception's view. Never give these to the model:
    filter first (verified_bookings, free_starts)."""
    return fields_of(view_rows(ctx, "bookings"))


def records(rows: list[dict]) -> dict:
    """{item: {"words", "state", "style", "updated", "address"}} of consult rows."""
    out = {}
    for r in rows:
        f = r["fields"]
        if f.get("item"):
            out[str(f["item"])] = {"words": str(f.get("words") or "").strip(), "state": str(f.get("state") or ""),
                                   "style": str(f.get("style") or "").strip(),
                                   "updated": str(r.get("updated") or ""), "address": r.get("address", "")}
    return out


def table_unit(records_in: list[dict] | None) -> str | None:
    """The address of the table unit among a function's FILES_IN records (None: the table does not exist yet)."""
    for r in records_in or []:
        address = str(r.get("address", ""))
        if "fields" not in r and address.startswith("fs://") and address[5:].count("/") == 1:
            return address
    return None


def fields_of(rows: list[dict]) -> list[dict]:
    return [r["fields"] for r in rows]


# ---- answer forms --------------------------------------------------------------------------------------------------
# the phone field of the bookings and customers tables (type.json "country": "US"): nextop's phone field type reads a
# number the way people in the US write it and keeps one key per number, E.164 (+15550107777)
PHONE_FIELD = {"name": "phone", "type": "phone", "country": "US"}
US_KEY = re.compile(r"^\+1[2-9]\d{9}$")                  # a US number: +1, an area code that starts with 2-9, 7 digits
# a recorded name is the name only: words that read like a sentence ("I'm Emma", "my name is Emma", "Emma here")
NAME_WORDS = 3                                              # at most this many words (Mary Ann Smith)
NOT_A_NAME = re.compile(r"^(i'?m|i am|my name|name'?s|it'?s|this is)\b|\b(here|speaking)[.!]*$|[.!?,]", re.I)


def mobile(words: str) -> str | None:
    """The key of a US phone number ((555) 010-7777, 555-010-7777, +1 555 010 7777, ...): E.164 (+15550107777), the
    same key nextop's phone field type gives the bookings table, so a recorded phone and a booking's phone compare
    equal. None for anything that is not a US number."""
    s = str(words or "").strip()
    if not s or phone_type.check(s, PHONE_FIELD) is not None:
        return None
    key = phone_type.normalize(s, PHONE_FIELD)
    return key if US_KEY.match(key) else None


def phone_display(key: str) -> str:
    """(555) 010-7777 for a US key, as people read it; anything else as it is."""
    k = str(key or "")
    return f"({k[2:5]}) {k[5:8]}-{k[8:]}" if US_KEY.match(k) else k


def people_time(hhmm: str) -> str:
    """2:30 PM for 14:30 (people in the US read 12-hour times; the tools and records keep 24-hour HH:MM)."""
    h, m = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'AM' if h < 12 else 'PM'}"


def when_of(words: str) -> datetime.datetime | None:
    """The datetime of "YYYY-MM-DD HH:MM" (None for any other form)."""
    try:
        return datetime.datetime.strptime(str(words or "").strip(), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def chosen_services(rec: dict) -> list[str]:
    """The services recorded in the service item (known ids only)."""
    return [s for s in values_of({"many": True}, (rec.get("service") or {}).get("words", "")) if s in salon()["services"]]


def style_problem(rec: dict, item: dict) -> str | None:
    """Why the recorded style item does not count yet (None: one menu style for every chosen service that has a menu
    to choose from). The value is in the consult field the item names (checklists.json "field")."""
    services = chosen_services(rec)
    value = (rec.get(item["id"]) or {}).get(item.get("field", "words"), "")
    if not value:
        return text("why_style_field", field=item.get("field", "words"))
    if not services:                                         # nothing to match the names with yet
        return text("why_style_service", service=item["menu"])
    got = plan(services, value)
    if got["wrong"]:
        return text("why_style_menu", names=", ".join(got["wrong"]), menus=menu_text(services))
    if got["twice"]:
        sid, names = next(iter(got["twice"].items()))
        return text("why_style_twice", service=salon()["services"][sid]["label"], names=", ".join(names))
    if got["missing"]:
        menus = menu_text(got["missing"])
        if got["recommend"]:
            return text("why_recommend", menus=menus, field=item.get("field", "words"))
        return text("why_style_missing", services=", ".join(salon()["services"][x]["label"] for x in got["missing"]),
                    menus=menus)
    return None


def values_of(item: dict, words: str) -> list[str]:
    return [w.strip() for w in words.split(",") if w.strip()] if item.get("many") else [words.strip()]


def problem(item: dict, words: str, booking_ids: list[str] | None = None) -> str | None:
    """Why a recorded answer does not count yet (None: it counts)."""
    if item.get("choices"):
        got = values_of(item, words)
        if not got or any(v not in item["choices"] for v in got):
            return text("why_choices", choices=", ".join(item["choices"]),
                        many=text("why_many") if item.get("many") else "")
    form = item.get("format")
    if form == "phone" and mobile(words) is None:
        return text("why_phone")
    if form == "name" and (not words.strip() or NOT_A_NAME.search(words.strip()) or len(words.split()) > NAME_WORDS):
        return text("why_name")
    if form == "datetime" and when_of(words) is None:
        return text("why_datetime")
    if form == "booking" and words not in (booking_ids or []):
        return text("why_booking")
    return None


# ---- purposes and the items of a purpose ---------------------------------------------------------------------------
def purpose_items(purpose: str, rec: dict) -> list[dict]:
    """The items of a purpose that apply now: its items (an item with "when" only when that item has that value) and,
    for a purpose with service_items, the checklist items of the services recorded in that item (before the
    agreement)."""
    spec = checklists()["purposes"][purpose]
    out = [i for i in spec["items"]
           if all((rec.get(k) or {}).get("words") == v for k, v in (i.get("when") or {}).items())]
    picked = chosen_services(rec)
    # a style item applies unless every recorded service has a one-style menu (it takes that style without asking)
    out = [i for i in out if not i.get("menu") or not picked or any(needs_choice(s) for s in picked)]
    if spec.get("service_items"):
        services = salon()["services"]
        extra = [dict(q, service=s) for s in picked for q in services[s].get("checklist", [])]
        at = next((n for n, i in enumerate(out) if i.get("agreement")), len(out))
        out = out[:at] + extra + out[at:]
    return out


def purposes(rec: dict) -> list[dict]:
    """The recorded purposes in the order they were first recorded: {"id", "label", "words", "state", "step"}."""
    spec = checklists()["purposes"]
    got = sorted(((v["address"], k[len(PURPOSE):], v) for k, v in rec.items() if k.startswith(PURPOSE)),
                 key=lambda x: x[0])                         # row addresses grow with the first write
    return [{"id": pid, "label": spec[pid]["label"], "words": v["words"],
             "state": "done" if v["state"] == "done" else "open", "step": spec[pid]["step"]}
            for _a, pid, v in got if pid in spec]


# ---- the calendar ----------------------------------------------------------------------------------------------------
def _at(day: datetime.date, hhmm: str) -> datetime.datetime:
    h, m = map(int, hhmm.split(":"))
    return datetime.datetime.combine(day, datetime.time(h, m))


def busy(schedule: list[dict], designer: str, day: datetime.date, leave_out: str = "") -> list[tuple]:
    """(start, end) of the visits that hold the designer's slots that day (pending or confirmed), leaving out one
    booking (the one being changed). schedule: every booking's fields (all_bookings)."""
    out = []
    for f in schedule:
        if (f.get("designer") == designer and f.get("date") == day.isoformat() and f.get("status") in ACTIVE
                and f.get("booking") != leave_out):
            start = _at(day, f["time"])
            out.append((start, start + datetime.timedelta(minutes=int(f["minutes"]))))
    return out


def free_starts(schedule: list[dict], designer: str, day: datetime.date, minutes: int,
                at: datetime.datetime | None = None, leave_out: str = "") -> list[str]:
    """Start times (HH:MM) on that day when the designer is working and free for `minutes`."""
    data = salon()
    d = data["designers"][designer]
    if day.weekday() not in d["days"]:
        return []
    at = at or now()
    step = datetime.timedelta(minutes=data["slot_minutes"])
    need = datetime.timedelta(minutes=minutes)
    taken = busy(schedule, designer, day, leave_out)
    out, t, close = [], _at(day, d["open"]), _at(day, d["close"])
    while t + need <= close:
        if t > at and all(t + need <= s or t >= e for s, e in taken):
            out.append(t.strftime("%H:%M"))
        t += step
    return out


def slot_problem(schedule: list[dict], designer: str, when: datetime.datetime, minutes: int,
                 leave_out: str = "") -> str | None:
    """Why this designer cannot take a visit of `minutes` at `when` (None: the slot is free)."""
    d = salon()["designers"][designer]
    if when.weekday() not in d["days"]:
        return text("why_not_working", name=d["name"], weekday=WEEKDAYS[when.weekday()])
    if when <= now():
        return text("why_past")
    if when < _at(when.date(), d["open"]) or when + datetime.timedelta(minutes=minutes) > _at(when.date(), d["close"]):
        return text("why_hours", name=d["name"], open=d["open"], close=d["close"])
    if when.strftime("%H:%M") not in free_starts(schedule, designer, when.date(), minutes, leave_out=leave_out):
        return text("why_taken", name=d["name"])
    return None


def free_designers(schedule: list[dict], when: datetime.datetime, minutes: int) -> list[str]:
    return [k for k in salon()["designers"] if slot_problem(schedule, k, when, minutes) is None]


# ---- the identity check ----------------------------------------------------------------------------------------------
def matching_bookings(every: list[dict], name: str, phone: str) -> list[dict]:
    """The bookings with exactly this name (spaces and upper or lower case ignored) and this phone (the phone field type's key): the program's
    identity check. A real check (a code sent to the phone) is future work: see README."""
    want_name, want_phone = str(name or "").replace(" ", "").casefold(), mobile(phone)
    if not want_name or not want_phone:
        return []
    return sorted((b for b in every if str(b.get("name", "")).replace(" ", "").casefold() == want_name
                   and mobile(b.get("phone", "")) == want_phone), key=lambda b: (b["date"], b["time"]))


def verified_bookings(rec: dict, every: list[dict]) -> dict:
    """The identity check of this chat, from the name and phone recorded in consult: {"state", "ids", "bookings"}.
    state none: not both recorded in the right form; failed: no booking has exactly them; ok: only then "ids" and
    "bookings" hold this customer's bookings (else they are empty: nothing about any booking leaves here)."""
    name = (rec.get("name") or {}).get("words", "")
    phone = (rec.get("phone") or {}).get("words", "")
    if not name or mobile(phone) is None or problem({"format": "name"}, name):
        return {"state": "none", "ids": [], "bookings": []}
    mine = matching_bookings(every, name, phone)
    if not mine:
        return {"state": "failed", "ids": [], "bookings": []}
    return {"state": "ok", "ids": [b["booking"] for b in mine], "bookings": mine}


def booking_line(f: dict) -> str:
    """One booking as the reception reads it (the step notice and tool results, after the identity check)."""
    status = {"pending": "waiting for the designer's approval", "confirmed": "confirmed",
              "declined": "declined by the designer", "cancelled": "canceled"}
    return (f"{f['booking']}: {day_label(datetime.date.fromisoformat(f['date']))} {f['time']} ({people_time(f['time'])}) "
            f"{f['designer_name']}, {', '.join(f['service_labels'])} ({', '.join(f['styles'])}) ${int(f['price']):,}, "
            f"{int(f['minutes'])} min, status {f['status']} ({status.get(f['status'], f['status'])})")


# ---- the state of one purpose's checklist ---------------------------------------------------------------------------
TIME_ITEMS = {"booking": ("wish_time", "designer", "agree"), "change": ("change_time", "change_designer", "change_agree")}


def checklist_state(purpose: str, rec: dict, ident: dict | None, schedule: list[dict]) -> dict:
    """What the navigator, book and change_booking all go by: the applicable items, each with "done" and, when an answer
    does not count, "why"; the open required ids; and for a purpose with a time, the slot check of the recorded time.
    ident: the identity check (verified_bookings); schedule: every booking's fields (for free times only). An agreement
    counts only when it was recorded after the items its "after" names (checklists.json) and after the purpose row was
    last written (a purpose started again needs a new agreement) and, for a time, while that time is still free."""
    state = (ident or {}).get("state", "none")
    ids = ident["ids"] if state == "ok" else []
    out = []
    for item in purpose_items(purpose, rec):
        words = (rec.get(item["id"]) or {}).get("words", "")
        why = None
        if item.get("computed"):                                # the identity check: decided by the program
            done = state == "ok"
            if state == "failed":
                why = text("why_not_verified")
        elif item.get("agreement"):                             # after its items and the purpose's last (re)start
            done = bool(words)
            after = list(item.get("after") or []) + [PURPOSE + purpose]
            later = max([(rec.get(x) or {}).get("updated", "") for x in after] + [""])
            if done and (rec.get(item["id"]) or {}).get("updated", "") < later:
                done, why = False, text("why_agree_stale")
        elif item.get("menu"):                                  # the style: menu names, checked against the services
            row = rec.get(item["id"])
            words = (row or {}).get(item.get("field", "words"), "")
            why = style_problem(rec, item) if row else None
            done = row is not None and why is None
            # the notice lists the menus of the chosen services while the style is open
            item = {**item, "menus": menu_text([s for s in chosen_services(rec) if needs_choice(s)])}
        else:
            why = problem(item, words, ids) if words else None
            done = bool(words) and why is None
        out.append({**item, "words": words, "done": done, **({"why": why} if why else {})})
    by_id = {i["id"]: i for i in out}
    slot = None
    if purpose in TIME_ITEMS:
        time_id, _who_id, agree_id = TIME_ITEMS[purpose]
        agree = by_id.get(agree_id)
        if time_id in by_id and by_id[time_id]["done"]:
            slot = slot_of(purpose, rec, schedule)
            if agree is not None and agree["done"] and not slot["free"]:
                agree.update(done=False, why=text("why_agree_taken"))
        elif agree is not None:
            agree["done"] = False
    return {"items": out, "open": [i["id"] for i in out if i.get("required") and not i["done"]], "slot": slot}


def slot_of(purpose: str, rec: dict, schedule: list[dict]) -> dict:
    """The recorded time checked against the calendar: {"when", "designer", "minutes", "free", "why",
    "free_designers"}. For a change the booking's own slot is left out and its designer and minutes are kept unless
    a new designer is recorded."""
    time_id, who_id, _agree = TIME_ITEMS[purpose]
    when = when_of(rec[time_id]["words"])
    designer = (rec.get(who_id) or {}).get("words", "")
    leave_out = ""
    if purpose == "booking":
        got = visit_plan(rec)
        minutes = quote(got["styles"])["minutes"] if got and not got["missing"] and got["styles"] else 30
    else:
        leave_out = (rec.get("change_booking") or {}).get("words", "")
        own = next((f for f in schedule if f.get("booking") == leave_out), None)
        minutes = int(own["minutes"]) if own else 30
        designer = designer or (own["designer"] if own else "")
    if designer in salon()["designers"]:
        why = slot_problem(schedule, designer, when, minutes, leave_out)
        return {"when": when, "designer": designer, "minutes": minutes, "free": why is None, "why": why,
                "free_designers": []}
    others = [k for k in salon()["designers"] if slot_problem(schedule, k, when, minutes, leave_out) is None]
    return {"when": when, "designer": "", "minutes": minutes, "free": False,
            "why": text("why_no_designer") if others else text("why_none_free"), "free_designers": others}


def visit_plan(rec: dict) -> dict | None:
    """The styles of the recorded services and style item (plan), or None before a service is recorded."""
    services = chosen_services(rec)
    if not services:
        return None
    spec = next(i for i in checklists()["purposes"]["booking"]["items"] if i.get("menu"))
    return plan(services, (rec.get(spec["id"]) or {}).get(spec.get("field", "words"), ""))


def open_problems(st: dict) -> list[str]:
    out = [f"{i['id']}({i['label']}): {i.get('why') or text('why_missing')}"
           for i in st["items"] if i.get("required") and not i["done"]]
    slot = st["slot"]
    if slot and not slot["free"]:
        out.append(f"{when_label(slot['when'])}: {slot['why']}")
    return out


# ---- the booking and the change a tool checks and a flow function writes -------------------------------------------
def booking_draft(rec: dict, schedule: list[dict]) -> tuple[dict | None, list[str]]:
    """The booking the recorded answers make, or (None, what is missing). Every value comes from the records."""
    st = checklist_state("booking", rec, None, schedule)
    problems = open_problems(st)
    if problems:
        return None, problems
    data = salon()
    q = quote(visit_plan(rec)["styles"])
    when, designer = st["slot"]["when"], st["slot"]["designer"]
    answers = [f"{i['label']}: {i['words']}" for i in st["items"] if i.get("service") and i["words"]]
    return {"booking": f"{when:%Y-%m-%d}-{when:%H%M}-{designer}", "status": "pending",
            "date": f"{when:%Y-%m-%d}", "time": f"{when:%H:%M}", "designer": designer,
            "designer_name": data["designers"][designer]["name"], "services": q["service_ids"],
            "service_labels": q["services"], "styles": q["styles"], "price": q["price"], "minutes": q["minutes"],
            "name": rec["name"]["words"], "phone": mobile(rec["phone"]["words"]), "answers": "\n".join(answers),
            "booked_at": f"{now():%Y-%m-%d %H:%M}"}, []


def change_draft(rec: dict, ident: dict | None, mine: list[dict], schedule: list[dict]) -> tuple[dict | None, list[str]]:
    """The changed (or cancelled) booking the recorded answers make, or (None, what is missing). mine: the bookings
    the identity check matched just now (only those can be changed). A cancel is a status: the row stays, cancelled."""
    st = checklist_state("change", rec, ident, schedule)
    problems = open_problems(st)
    if problems:
        return None, problems
    b = next((dict(x) for x in mine if x["booking"] == rec["change_booking"]["words"]), None)
    if b is None:
        return None, [f"change_booking: {text('why_booking')}"]
    if b["status"] not in ACTIVE:
        return None, [f"change_booking: {text('why_not_active', status=b['status'])}"]
    b["booked_at"] = f"{now():%Y-%m-%d %H:%M}"
    if rec["change_action"]["words"] == "cancel":
        b["status"] = "cancelled"
        return b, []
    when, designer = st["slot"]["when"], st["slot"]["designer"]
    b.update(status="pending", date=f"{when:%Y-%m-%d}", time=f"{when:%H:%M}", designer=designer,
             designer_name=salon()["designers"][designer]["name"])
    return b, []


def finish_purpose(ctx: dict, purpose: str, rec: dict) -> str | None:
    """A purpose the program finished (book, change_booking): its purpose row is written again with state done. The
    answers stay until the chat ends (chat_end deletes the chat's rows; a worker deletes nothing); when the customer
    starts the same purpose again, its row is open again and an agreement counts only when given after that
    (checklist_state). None, or what went wrong."""
    words = (rec.get(PURPOSE + purpose) or {}).get("words") or checklists()["purposes"][purpose]["label"]
    return write_rows(ctx, "consult", [{"item": PURPOSE + purpose, "words": words, "state": "done"}])


def uploads(table: str | None, server: str, rows: list[dict], what: str) -> dict:
    """One _uploads item: rows written into the table of a file server (a new table when there is none yet). The
    title carries the time, so two writes of the same rows are both kept (the core skips a file whose title and content
    a table already holds)."""
    stamp = f"{now():%Y%m%d-%H%M%S-%f}"
    item = {"file_server": server, "name": f"{server}_{stamp}.json", "text": json.dumps(rows, ensure_ascii=False),
            "title": f"{server} {stamp}", "description": what, "source": "salon program"}
    if table:
        item["to"] = table
    return item


# ---- the schedule page ------------------------------------------------------------------------------------------------
SCHEDULE_CSS = """
body{margin:0;padding:16px;font-family:system-ui,sans-serif;background:#f4f6f8;color:#1d2633}
h1{font-size:1.3rem;margin:0 0 4px} .note{color:#6b7684;margin:0 0 16px;font-size:.9rem}
section{background:#fff;border:1px solid #d9dee5;border-radius:10px;padding:12px;margin-bottom:16px;overflow-x:auto}
h2{font-size:1.05rem;margin:0 0 8px} table{border-collapse:collapse;width:100%;min-width:520px;table-layout:fixed}
th,td{border:1px solid #e3e7ec;font-size:.8rem;padding:2px 6px;height:22px;vertical-align:top}
th{background:#f7f9fb} td.t{width:72px;color:#6b7684;text-align:right} td.off{background:#eceff3}
td.b{background:#e3eefc;border-left:3px solid #2f6fd6} td.b b{display:block}
td.p{background:#fff;border:2px dashed #2f6fd6} td.p b{display:block}
.legend{font-size:.85rem;margin:0 0 12px} .legend span{display:inline-block;padding:1px 8px;margin-right:8px;border-radius:4px}
"""


def write_schedule(bookings: list[dict], days: int = 7) -> pathlib.Path:
    """schedule.html for the owner: the next `days` days, one table per day (rows = slots, columns = designers), from
    the booking rows a flow function read (pending and confirmed). Written again after every booking write."""
    import html
    data = salon()
    step = data["slot_minutes"]
    designers = data["designers"]
    today = datetime.date.today()
    active = [b for b in bookings if b.get("status") in ACTIVE]
    out = ["<!doctype html><html lang='en'><head><meta charset='utf-8'>",
           "<meta name='viewport' content='width=device-width, initial-scale=1'>",
           f"<title>Bookings</title><style>{SCHEDULE_CSS}</style></head><body>",
           f"<h1>{html.escape(data['name'])} bookings</h1>",
           "<p class='legend'><span style='background:#e3eefc;border-left:3px solid #2f6fd6'>confirmed</span>"
           "<span style='border:2px dashed #2f6fd6'>pending (the designer has not answered yet)</span></p>",
           f"<p class='note'>as of {now():%Y-%m-%d %H:%M} · written again whenever a booking changes</p>"]
    opens = [d["open"] for d in designers.values()]
    closes = [d["close"] for d in designers.values()]
    for n in range(days):
        day = today + datetime.timedelta(days=n)
        start, end = _at(day, min(opens)), _at(day, max(closes))
        booked = {k: {b["time"]: b for b in active if b["designer"] == k and b["date"] == day.isoformat()}
                  for k in designers}
        count = sum(len(v) for v in booked.values())
        out.append(f"<section><h2>{day_label(day)} · {count} booking{'' if count == 1 else 's'}</h2><table><tr><th style='width:72px'></th>")
        out += [f"<th>{html.escape(d['name'])}</th>" for d in designers.values()]
        out.append("</tr>")
        covered = {k: 0 for k in designers}
        t = start
        while t < end:
            hhmm = t.strftime("%H:%M")
            out.append(f"<tr><td class='t'>{people_time(hhmm) if t.minute == 0 else ''}</td>")
            for key, d in designers.items():
                if covered[key] > 0:
                    covered[key] -= 1
                    continue
                b = booked[key].get(hhmm)
                works = day.weekday() in d["days"] and _at(day, d["open"]) <= t < _at(day, d["close"])
                if b:
                    rows = max(1, -(-int(b["minutes"]) // step))
                    covered[key] = rows - 1
                    pending = b.get("status") == "pending"
                    tag = " · pending" if pending else ""
                    out.append(f"<td class='{'p' if pending else 'b'}' rowspan='{rows}'><b>{html.escape(people_time(b['time']))} "
                               f"{html.escape(b['name'])}</b>{html.escape(', '.join(b['service_labels']))} "
                               f"({html.escape(', '.join(b['styles']))}) · {b['minutes']} min{tag}</td>")
                else:
                    out.append("<td class='off'></td>" if not works else "<td></td>")
            out.append("</tr>")
            t += datetime.timedelta(minutes=step)
        out.append("</table></section>")
    out.append("</body></html>")
    path = data_dir() / "schedule.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    return path
