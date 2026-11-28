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
        note = 'No mail was sent because the mail settings are missing. ' + " ".join(problems) + " " + 'The slides are saved in output/.'
        print(note)
        return {"mail": {"sent": False, "note": note}}
    prefix = "[PDF deck TEST] " if setting("MAIL_TEST_MODE", "1") == "1" else "[PDF deck] "
    subject = f"{prefix}{brief['file']} as slides ({len(deck['slides'])} slides, {theme} theme)"
    titles = "\n".join(f"{s['no']}. {s['title']}" for s in deck["slides"])
    body = f"{deck['doc_title']}\nThe slides made from {brief['file']} are attached.\n\n{titles}\n"
    ok, note = send_mail(recipients(), subject, body, [
        (saved["pptx"].name, PPTX_TYPE, saved["pptx"].read_bytes()),
        (saved["overview"].name, "image/png", saved["overview"].read_bytes())])
    if not ok:
        return {"error": f"the slides mail was not sent ({note}); the slides are in output/"}
    print("mail sent")
    return {"mail": {"sent": True, "note": note}}
