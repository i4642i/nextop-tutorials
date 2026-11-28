"""End of the flow: reads the report the writer saved in reports/ (the program reads the file, not the model's words)
and mails it to the owner. A mail that cannot be sent fails the block with the reason (the report stays in reports/),
and so does a run in which no page could be read."""
from functions._links import REPORTS, recipients, send_mail, setting

NAME = "mail_report"
DESC = "Mail the saved link summary report (body and .md attachment); a mail that cannot be sent fails the block"
OUTPUTS = [{"name": "mail", "schema": {
    "type": "object",
    "properties": {"sent": {"type": "boolean"}, "note": {"type": "string"}, "to": {"type": "string"}},
    "required": ["sent", "note", "to"]}}]


def run(ctx, inputs):
    request, report = inputs["intake/request"], inputs["writer/report"]
    pages = inputs["reader/notes"]["pages"]
    if not any(p["read"] for p in pages):          # nothing was read: the report would only say so, and the job is not done
        return {"error": "읽은 페이지가 하나도 없어 요약을 보내지 않았습니다: "
                + "; ".join(f"페이지 {p['page']} - {p['problem'] or '이유 없음'}" for p in pages)}
    path = REPORTS / request["report_file"]
    if not path.is_file():
        return {"error": f"보고서 {path.name} 이 reports/ 에 없어 메일을 보내지 않았습니다"}
    text = path.read_text(encoding="utf-8")
    count = len(request["pages"])
    test = "[링크 요약·시험] " if setting("MAIL_TEST_MODE", "1") == "1" else "[링크 요약] "
    subject = f"{test}{report['headline']} (링크 {count}개)"
    to = recipients()
    ok, note = send_mail(to, subject, text + f"\n\n(이 요약은 reports/{path.name}에도 있습니다.)\n",
                         attachments=[(path.name, text)])
    if not ok:
        return {"error": f"요약 메일을 보내지 못했습니다 ({note}). 보고서는 reports/{path.name} 에 있습니다"}
    return {"mail": {"sent": True, "to": to, "note": note}}
