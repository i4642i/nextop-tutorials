"""End of the flow `booking_notes`: puts the consultation summary and the prep memo next to the booking
(memos/<id>.memo.md, the chat in memos/<id>.chat.txt) and mails them to the designer, with the whole chat attached and
two links: approve or decline. The customer gets no text message here; it goes out only after the designer answers
(flow `decide`). Names, times, prices and the checklist answers come from the booking row."""
from functions._approval import links
from functions._notify import designer_address, send_mail, setting
from functions._salon import data_dir

NAME = "mail_designer"
DESC = "Mail the designer the consultation summary, prep memo, chat (attached) and the approve / decline links"
OUTPUTS = []

SPEAKER = {"user": "손님", "assistant": "하나"}


def chat_text(transcript: list[dict], b: dict) -> str:
    """The whole chat as the designer reads it: one line per message, word for word (the program writes it)."""
    lines = [f"상담 대화 · {b['name']} · {b['day']} {b['time']} 예약", ""]
    lines += [f"{SPEAKER.get(m.get('role'), m.get('role'))}: {m.get('content', '')}" for m in transcript]
    return "\n".join(lines) + "\n"


def run(ctx, inputs):
    visit = inputs["load_visit/visit"]
    b = visit["booking"]
    summary = inputs["nuri/summary"]
    prep = inputs["duri/prep"]
    services = ", ".join(b["service_labels"])
    lines = [f"# {b['day']} {b['time']} · {b['designer_name']}",
             f"- 손님: {b['name']} · {b['phone']}",
             f"- 시술: {services} ({', '.join(b['styles'])}) · {int(b['minutes'])}분 · {int(b['price']):,}원",
             "", "## 상담 요약", summary["text"]]
    lines += [f"- 원하는 것: {w}" for w in summary["wishes"]]
    answers = [f"- {x}" for x in str(b.get("answers") or "").splitlines() if x.strip() and x.strip() != "-"]
    if answers:
        lines += ["", "## 손님이 미리 답한 것"] + answers
    lines += ["", "## 준비할 것"] + [f"- {x}" for x in prep["ready"]]
    lines += ["", "## 처음에 확인할 것"] + [f"- {x}" for x in prep["ask_first"]]
    if prep["care"]:
        lines += ["", "## 조심할 점"] + [f"- {x}" for x in prep["care"]]
    try:
        yes, no = links(b["booking"])
    except ValueError as e:
        return {"error": f"the mail to the designer was not sent ({e})"}
    lines += ["", "## 예약 확인", "아래 링크로 답해 주세요. 승인하면 손님께 확정 문자가 갑니다.",
              f"- 승인: {yes}", f"- 거절: {no}", "", "(첨부: 상담 대화 전체)"]
    body = "\n".join(lines) + "\n"
    chat = chat_text(visit["transcript"], b)
    folder = data_dir() / "memos"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{b['booking']}.memo.md").write_text(body, encoding="utf-8")
    (folder / f"{b['booking']}.chat.txt").write_text(chat, encoding="utf-8")
    test = "[예약·시험] " if setting("MAIL_TEST_MODE", "1") == "1" else ""      # test mode: say so in the subject
    subject = f"{test}[예약 승인 요청] {b['day']} {b['time']} {b['name']} · {', '.join(b['styles'])}"
    ok, note = send_mail(designer_address(b["designer"]), subject, body,
                         attachments=[(f"상담대화_{b['booking']}.txt", chat)])
    if not ok:
        return {"error": f"the mail to the designer was not sent ({note}); the memo is in memos/{b['booking']}.memo.md"}
    return {}
