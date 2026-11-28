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
    if not any(p["read"] for p in pages):          # nothing was read: the job is not done
        return {"error": '読めたページが1つもないため、要約は送りませんでした: ' + "; ".join(
            f"ページ {p['page']} - {p['problem'] or '理由なし'}" for p in pages)}
    path = REPORTS / request["report_file"]
    if not path.is_file():
        return {"error": f"レポート {path.name} が reports/ にないため、メールを送りませんでした"}
    text = path.read_text(encoding="utf-8")
    count = len(request["pages"])
    test = "[リンク要約・テスト] " if setting("MAIL_TEST_MODE", "1") == "1" else "[リンク要約] "
    subject = f"{test}{report['headline']}（リンク{count}件）"
    to = recipients()
    ok, note = send_mail(to, subject, text + f"\n\n（この要約は reports/{path.name} にも保存されています。）\n",
                         attachments=[(path.name, text)])
    if not ok:
        return {"error": f"要約メールを送れませんでした（{note}）。レポートは reports/{path.name} にあります"}
    return {"mail": {"sent": True, "to": to, "note": note}}
