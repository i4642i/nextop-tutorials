"""End of the flow: builds the deck from the outline and the written slides, saves the .pptx and its previews, mails it when mail is set up.

Every value on a slide that is not the writer's sentence (the document title, table cells, figure pictures, captions,
page numbers, the agenda, slide numbers) is placed here by the program from the report. The slides are saved first. Mail is optional: when the
mail settings are missing the run still ends well and says clearly that no mail was sent; when the settings are there but
the mail cannot be sent, the block fails with the server and the reason.
"""
from functions._common import mail_problems, recipients, send_mail, setting
from functions._deck import THEMES, compose
from functions._render import save_deck

NAME = "deliver"
DESC = "Build the slides, save the .pptx and PNG previews in output/, and mail them when mail is set up"
OUTPUTS = [{"name": "mail", "schema": {
    "type": "object",
    "properties": {"sent": {"type": "boolean"}, "note": {"type": "string"}},
    "required": ["sent", "note"]}}]
PPTX_TYPE = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def run(ctx, inputs):
    brief, report = inputs["intake/brief"], inputs["classify/report"]
    written = inputs["gather/gathered"]            # one written slide per outline slide, in outline order
    if len(written) != len(inputs["planner/outline"]["slides"]):
        return {"error": f"{len(written)} written slides for {len(inputs['planner/outline']['slides'])} outline slides"}
    deck = compose(brief, report, inputs["planner/outline"], {"slides": written})
    saved = save_deck(deck, brief["theme"], brief["file"].rsplit(".", 1)[0])
    theme = THEMES[brief["theme"]]["name"]
    print(f"saved {saved['pptx']} and {len(saved['previews'])} previews ({theme} theme)")
    problems = mail_problems()
    if problems:                                   # optional: no mail settings is not a failure, but it is said clearly
        note = '메일 설정이 없어 메일을 보내지 않았습니다. ' + " ".join(problems) + " " + '슬라이드는 output/ 에 저장했습니다.'
        print(note)
        return {"mail": {"sent": False, "note": note}}
    prefix = "[PDF 발표·시험] " if setting("MAIL_TEST_MODE", "1") == "1" else "[PDF 발표] "
    subject = f"{prefix}{brief['file']} 발표 자료 ({len(deck['slides'])}장, {theme} 테마)"
    titles = "\n".join(f"{s['no']}. {s['title']}" for s in deck["slides"])
    body = f"{deck['doc_title']}\n{brief['file']}로 만든 발표 자료를 첨부했습니다.\n\n{titles}\n"
    ok, note = send_mail(recipients(), subject, body, [
        (saved["pptx"].name, PPTX_TYPE, saved["pptx"].read_bytes()),
        (saved["overview"].name, "image/png", saved["overview"].read_bytes())])
    if not ok:
        return {"error": f"발표 자료 메일을 보내지 못했습니다 ({note}). 슬라이드는 output/ 에 있습니다"}
    print("mail sent")
    return {"mail": {"sent": True, "note": note}}
