"""Start of the flow: takes 1 to 3 web addresses and names the report file the writer will save in reports/."""
from functions._links import REPORTS, mail_problems, now_seoul, parse_links

NAME = "intake"
DESC = "Read the web addresses of the run input (1 to 3) and name the report file"
START = True
INPUTS = [{"name": "links", "description": "1 to 3 web page addresses (http:// or https://), one per line", "required": True}]
OUTPUTS = [{"name": "request", "schema": {
    "type": "object",
    "properties": {
        "pages": {"type": "array", "items": {"type": "object", "properties": {
            "page": {"type": "integer"}, "url": {"type": "string"}}, "required": ["page", "url"]}},
        "report_file": {"type": "string"}},
    "required": ["pages", "report_file"]}}]


def run(ctx, inputs):
    links, problems = parse_links(inputs.get("links", ""))
    setup = mail_problems()                                 # fail now, before any model call is paid for
    if setup:
        return {"error": "開始できません。.env の設定が空です: " + " ".join(setup)}
    if problems:
        return {"error": "; ".join(problems)}
    if not REPORTS.is_dir():
        return {"error": f"the folder {REPORTS} is missing; the filesystem MCP server may only write there (create it)"}
    return {"request": {"pages": [{"page": i, "url": u} for i, u in enumerate(links, 1)],
                        "report_file": f"links_{now_seoul():%Y%m%d-%H%M%S}.md"}}
