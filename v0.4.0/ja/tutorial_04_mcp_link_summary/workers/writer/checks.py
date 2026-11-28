from functions._links import REPORTS, japanese_errors, today_seoul

RULES = [
    "report.file is the request's report_file, and that file is saved in reports/.",
    "The saved report has every address of the request, word for word, and today's date (Asia/Seoul).",
    "The headline and the report are Japanese: no Korean letters, no simplified Chinese characters (a page title may have them).",
]


def check(outputs, inputs):
    request, report = inputs["request"], outputs["report"]
    errors = []
    if report["file"] != request["report_file"]:
        errors.append(f"report.file must be the request's report_file {request['report_file']!r}, not {report['file']!r}")
    path = REPORTS / request["report_file"]
    if not path.is_file():
        return errors + [f"the report {request['report_file']} is not saved yet; save it with filesystem__write_file "
                         f"(path = {request['report_file']!r})"]
    text = path.read_text(encoding="utf-8")
    for p in request["pages"]:
        if p["url"] not in text:
            errors.append(f"the saved report lacks the address of page {p['page']}: {p['url']} (copy it word for word)")
    today = today_seoul()
    if today not in text:
        errors.append(f"the saved report lacks today's date {today} (from time__get_current_time, Asia/Seoul)")
    titles = [p.get("title", "") for p in (inputs.get("notes") or {}).get("pages", []) if p.get("title")]
    body = text
    for t in titles:                                   # a page's own title may be in any language
        body = body.replace(t, "")
    errors += japanese_errors("report.headline", report["headline"])
    errors += japanese_errors("the saved report", body, need_kana=True)
    return errors
