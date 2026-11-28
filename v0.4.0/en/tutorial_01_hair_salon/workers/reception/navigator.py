"""The conversation navigator of the reception: which step this question is in, and what the step notice says.

The platform calls navigate(ctx) before every question and again after every tool round, so the notice already shows
what a put or a tool just recorded. It reads through the reception's views ctx["file_servers"], with the reception's
rights: consult (this chat's purposes and checklist answers) and bookings (every booking: read all). The notice is the
reception's model input, so it filters: free or taken times only (never whose), and bookings only of the customer the
identity check verified (the recorded name and phone match), nothing at all before that. It compares the records with
checklists.json and salon.json (functions/_salon.py holds the rules, shared with the tools and flow functions). Every
sentence comes from checklists.json "texts"; this file writes nothing and uses no LLM.

Steps: consult (find the purposes, shop questions, collect booking items), booking (every booking item but the
agreement is recorded: propose a free time, record the agreement, book), manage (see, change or cancel a booking:
identity check first). The first open booking, my_booking or change purpose picks the step; shop questions and other
purposes are named in the notice in any step.
"""
from functions._salon import (all_bookings, booking_line, checklist_state, day_label, now, purposes, records, salon,
                              text, verified_bookings, view_rows, when_label)

CONSULT, BOOKING, MANAGE = "consult", "booking", "manage"
TIME_ITEMS = {"booking": ("wish_time", "designer", "agree"), "change": ("change_time", "change_designer", "change_agree")}
AGREEMENTS = ("change_agree", "cancel_agree")      # the change purpose's agreements: asked for last


def describe(item: dict, full: bool = True) -> str:
    """One item as the notice names it: the label, the id to record it under, and its form. The style item lists the
    menus of the chosen services (full; once per notice, so the short form elsewhere)."""
    if item.get("menu"):
        if not full:
            return text("item", label=item["label"], id=item["id"])
        if not item.get("menus"):
            return text("item_style_later", label=item["label"], id=item["id"])
        return text("item_style", label=item["label"], id=item["id"], field=item.get("field", "words"),
                    menus=item["menus"], recommend=salon()["recommend"])
    if item.get("choices"):
        return text("item_choices", label=item["label"], id=item["id"], choices=", ".join(item["choices"]),
                    many=text("item_many") if item.get("many") else "")
    if item.get("format") == "phone":
        return text("item_phone", label=item["label"], id=item["id"])
    if item.get("format") == "name":
        return text("item_name", label=item["label"], id=item["id"])
    if item.get("format") == "datetime":
        return text("item_datetime", label=item["label"], id=item["id"])
    return text("item", label=item["label"], id=item["id"])


def collect_lines(label: str, st: dict, skip: tuple = ()) -> list[str]:
    """What is still to collect, what must be asked again, what is optional, and what is recorded."""
    items = [i for i in st["items"] if not i.get("computed") and i["id"] not in skip]
    need = [i for i in items if i.get("required") and not i["done"] and not i.get("why")]
    redo = [i for i in items if i.get("why")]
    optional = [i for i in items if not i.get("required") and not i["done"]]
    done = [i for i in items if i["done"]]
    first = (redo or need)[0] if redo or need else None
    lines = [text("collect", label=label, items=", ".join(describe(i, i is not first) for i in need) or "-",
                  next=describe(first, not first.get("why")))] if first else [text("collect_done", label=label)]
    needed = [i for i in redo + need if i.get("required") and i.get("need")]
    if needed:                                 # why each missing item is needed (checklists.json "need")
        lines.append(text("need", items=" ".join(text("need_item", label=i["label"], id=i["id"], need=i["need"])
                                                 for i in needed)))
    if redo:
        lines.append(text("redo", items="; ".join(f"{describe(i, i.get('menus', '') not in i['why'])}: {i['why']}" for i in redo)))
    if optional:
        lines.append(text("optional", items=", ".join(describe(i) for i in optional)))
    if done:
        lines.append(text("recorded", items=", ".join(text("item_value", label=i["label"], words=i["words"])
                                                       for i in done)))
    return lines


def slot_lines(purpose: str, st: dict) -> list[str]:
    """The recorded time against the calendar, and what to do about the agreement."""
    time_id, who_id, agree_id = TIME_ITEMS[purpose]
    slot = st["slot"]
    if slot is None:
        return []
    when = when_label(slot["when"])
    designers = salon()["designers"]
    if slot["free"]:
        lines = [text("slot_free", when=when, designer=designers[slot["designer"]]["name"])]
        agree = next(i for i in st["items"] if i["id"] == agree_id)
        if agree.get("why"):                   # an agreement that no longer counts says why
            lines.append(text("redo", items=f"{describe(agree)}: {agree['why']}"))
        lines.append(text("book_now" if purpose == "booking" else "change_now") if agree["done"]
                     else text("agree_open", agree_id=agree_id))
        return lines
    if slot["designer"]:
        return [text("slot_taken", when=when, designer=designers[slot["designer"]]["name"], why=slot["why"],
                     time_id=time_id, who_id=who_id)]
    if slot["free_designers"]:
        return [text("slot_no_designer", when=when, who_id=who_id,
                     free=", ".join(f"{designers[d]['name']}({d})" for d in slot["free_designers"]))]
    return [text("slot_none_free", when=when, time_id=time_id, who_id=who_id)]


def mine_lines(ident: dict) -> str:
    """The verified customer's bookings, one line each ("-" when there is none or nobody is verified)."""
    return "; ".join(booking_line(b) for b in ident["bookings"]) or "-"


def manage_lines(purpose: dict, rec: dict, ident: dict, schedule: list[dict]) -> list[str]:
    st = checklist_state(purpose["id"], rec, ident, schedule)
    if ident["state"] != "ok":                 # nothing about any booking before the identity check passes
        who = {**st, "items": [i for i in st["items"] if i["id"] in ("name", "phone")]}
        missing = any(i.get("required") and not i["done"] for i in who["items"])
        key = "verify_failed" if ident["state"] == "failed" else "verify_first"
        return (collect_lines(purpose["label"], who) if missing else []) + [text(key)]
    lines = [text("verified", lines=mine_lines(ident))]
    if purpose["id"] == "my_booking":
        return lines + [text("my_booking_now")]
    lines += collect_lines(purpose["label"], st, skip=AGREEMENTS)
    if [i for i in st["open"] if i not in AGREEMENTS]:
        return lines
    if (rec.get("change_action") or {}).get("words") != "cancel":
        return lines + slot_lines("change", st)
    agree = next(i for i in st["items"] if i["id"] == "cancel_agree")
    if agree.get("why"):
        lines.append(text("redo", items=f"{describe(agree)}: {agree['why']}"))
    if agree["done"]:
        return lines + [text("change_now")]
    chosen = next(b for b in ident["bookings"] if b["booking"] == rec["change_booking"]["words"])
    return lines + [text("cancel_agree_open", line=booking_line(chosen))]


def side_lines(p: dict) -> str:
    if p["id"] == "info":
        return text("info_open", words=p["words"])
    if p["id"] == "other":
        return text("other_open", words=p["words"])
    return text("next_purposes", list=f"{p['label']}(purpose_{p['id']})")


def navigate(ctx):
    rec = records(view_rows(ctx, "consult"))
    schedule = all_bookings(ctx)                   # every booking: only free times and the identity check use it
    ident = verified_bookings(rec, schedule)
    lines = [text("today", day=day_label(now().date()))]
    ps = purposes(rec)
    if ps:
        lines.append(text("purposes", list=", ".join(
            text("purpose_entry", label=p["label"], id=p["id"], words=p["words"], state=text(f"state_{p['state']}"))
            for p in ps)))
    open_ps = [p for p in ps if p["state"] == "open"]
    # a purpose the program finished in this question (book, change_booking): the step switch left its tool result
    # behind, so the notice says what was just done, with this customer's bookings as they are now
    entered = set(ctx.get("entered") or [])
    for p in ps:
        if p["state"] == "done" and p["step"] in entered and p["step"] != CONSULT:
            lines.append(text("just_done", label=p["label"], id=p["id"], lines=mine_lines(ident)))
    main = next((p for p in open_ps if p["step"] in (BOOKING, MANAGE)), None)
    step = CONSULT
    if not ps:
        lines.append(text("no_purpose"))
    elif not open_ps:
        lines.append(text("all_done"))
    elif main is not None and main["id"] == "booking":
        st = checklist_state("booking", rec, None, schedule)
        before_agreement = [i for i in st["open"] if i != TIME_ITEMS["booking"][2]]
        lines += collect_lines(main["label"], st, skip=(TIME_ITEMS["booking"][2],))
        if not before_agreement:
            step = BOOKING
            lines += slot_lines("booking", st)
    elif main is not None:
        step = MANAGE
        lines += manage_lines(main, rec, ident, schedule)
    lines += [side_lines(p) for p in open_ps if p is not main]
    return {"step": step, "notice": "\n".join(lines)}
