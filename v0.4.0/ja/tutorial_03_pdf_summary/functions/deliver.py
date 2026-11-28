"""End of the flow: draws the one-page A4 summary, checks by program that it is one page, and mails it.

The mail body is the classification report; the summary PDF is attached. The PDF is also saved in summaries/.
"""
from functions._pdf import data_dir, page_count, recipients, render_summary, report_text, send_mail, setting

NAME = "deliver"
DESC = "Draw the A4 summary, check it is one page and mail it with the classification report"
OUTPUTS = []


def run(ctx, inputs):
    brief, report, summary = inputs["intake/brief"], inputs["classify/report"], inputs["summarizer/summary"]
    pdf = render_summary(summary, report, brief["today"])
    pages = page_count(pdf)
    if pages != 1:                                    # the worker's check refuses this earlier; this is the last guard
        return {"error": f"the summary is {pages} pages, not one A4 page; it was not mailed"}
    stem = brief["file"].rsplit(".", 1)[0]
    folder = data_dir() / "summaries"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{stem}_summary.pdf").write_bytes(pdf)
    body = report_text(report)
    (folder / f"{stem}_report.txt").write_text(body, encoding="utf-8")
    c = report["counts"]
    prefix = "[PDF要約・テスト] " if setting("MAIL_TEST_MODE", "1") == "1" else "[PDF要約] "
    subject = f"{prefix}{brief['file']} の A4 要約（本文 {c['text']}、表 {c['table']}、図 {c['figure']}）"
    text = f"{summary['title']}\nA4 一枚の要約を添付しました。\n\n{body}"
    ok, note = send_mail(recipients(), subject, text, [(f"要約_{stem}.pdf", pdf)])
    if not ok:
        return {"error": f"the summary mail was not sent ({note}); the summary is in summaries/{stem}_summary.pdf"}
    return {}
