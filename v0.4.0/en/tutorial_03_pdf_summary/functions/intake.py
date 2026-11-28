"""Start of the flow: takes the path of one PDF and puts it on the file server `pdf`, where it is read into parts."""
import datetime
import pathlib

from functions._pdf import ROOT, mail_problems

NAME = "intake"
DESC = "Upload the PDF the person gave (its path is the run input) to the pdf file server"
START = True
FILES_OUT = True                      # it uploads (_uploads) and shares the file with the next blocks
INPUTS = [{"name": "pdf_path", "description": "path of the PDF to summarize (absolute, or relative to the project folder)", "required": True}]
OUTPUTS = [{"name": "brief", "schema": {
    "type": "object",
    "properties": {"file": {"type": "string"}, "today": {"type": "string"}},
    "required": ["file", "today"]}}]


def run(ctx, inputs):
    path = pathlib.Path(inputs["pdf_path"])
    path = path if path.is_absolute() else ROOT / path
    if not path.is_file() or path.suffix.lower() != ".pdf":
        return {"error": f"pdf_path must be an existing .pdf file: {inputs['pdf_path']}"}
    setup = mail_problems()                                 # fail now, before any model call is paid for
    if setup:
        return {"error": "Cannot start. Settings missing in .env: " + " ".join(setup)}
    return {"brief": {"file": path.name, "today": datetime.date.today().isoformat()},
            "_uploads": [{"file_server": "pdf", "file": str(path), "title": path.name, "source": f"PDF given to the flow: {path.name}"}]}
