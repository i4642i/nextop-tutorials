"""End of the flow `booking_notes`: puts the consultation summary and the prep memo next to the booking
(memos/<id>.memo.md, the chat in memos/<id>.chat.txt) and mails them to the designer, with the whole chat attached and
two links: approve or decline. The customer gets no text message here; it goes out only after the designer answers
(flow `decide`). Names, times, prices and the checklist answers come from the booking row."""
from functions._approval import links
from functions._notify import designer_address, send_mail, setting
from functions._salon import data_dir, people_time, phone_display

NAME = "mail_designer"
DESC = "Mail the designer the consultation summary, prep memo, chat (attached) and the approve / decline links"
OUTPUTS = []

SPEAKER = {"user": "Customer", "assistant": "Riley"}


def chat_text(transcript: list[dict], b: dict) -> str:
    """The whole chat as the designer reads it: one line per message, word for word (the program writes it)."""
    lines = [f"Consultation chat · {b['name']} · booking {b['day']} {people_time(b['time'])}", ""]
    lines += [f"{SPEAKER.get(m.get('role'), m.get('role'))}: {m.get('content', '')}" for m in transcript]
    return "\n".join(lines) + "\n"


def run(ctx, inputs):
    visit = inputs["load_visit/visit"]
    b = visit["booking"]
    summary = inputs["nuri/summary"]
    prep = inputs["duri/prep"]
    services = ", ".join(b["service_labels"])
    lines = [f"# {b['day']} {people_time(b['time'])} · {b['designer_name']}",
             f"- Customer: {b['name']} · {phone_display(b['phone'])}",
             f"- Services: {services} ({', '.join(b['styles'])}) · {int(b['minutes'])} min · ${int(b['price']):,}",
             "", "## Consultation summary", summary["text"]]
    lines += [f"- Wants: {w}" for w in summary["wishes"]]
    answers = [f"- {x}" for x in str(b.get("answers") or "").splitlines() if x.strip() and x.strip() != "-"]
    if answers:
        lines += ["", "## Answered in advance"] + answers
    lines += ["", "## To prepare"] + [f"- {x}" for x in prep["ready"]]
    lines += ["", "## To ask first"] + [f"- {x}" for x in prep["ask_first"]]
    if prep["care"]:
        lines += ["", "## Be careful about"] + [f"- {x}" for x in prep["care"]]
    try:
        yes, no = links(b["booking"])
    except ValueError as e:
        return {"error": f"the mail to the designer was not sent ({e})"}
    lines += ["", "## Your answer", "Please answer with a link below. When you approve, the customer gets the "
              "confirmation text.", f"- Approve: {yes}", f"- Decline: {no}", "", "(attached: the whole consultation chat)"]
    body = "\n".join(lines) + "\n"
    chat = chat_text(visit["transcript"], b)
    folder = data_dir() / "memos"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{b['booking']}.memo.md").write_text(body, encoding="utf-8")
    (folder / f"{b['booking']}.chat.txt").write_text(chat, encoding="utf-8")
    test = "[booking TEST] " if setting("MAIL_TEST_MODE", "1") == "1" else ""      # test mode: say so in the subject
    subject = f"{test}[new booking, please approve] {b['day']} {people_time(b['time'])} {b['name']} · {', '.join(b['styles'])}"
    ok, note = send_mail(designer_address(b["designer"]), subject, body,
                         attachments=[(f"chat_{b['booking']}.txt", chat)])
    if not ok:
        return {"error": f"the mail to the designer was not sent ({note}); the memo is in memos/{b['booking']}.memo.md"}
    return {}
