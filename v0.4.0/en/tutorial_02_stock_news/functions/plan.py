"""Start of the flow: which day the outlook is for and which companies it covers (from stocks.json)."""
import datetime

from functions._news import PROBLEMS_FILE, data_dir, day_label, next_trading_day, setup_problems, stocks

NAME = "plan"
DESC = "Name the day the outlook is for and the companies to cover"
START = True
INPUTS = [{"name": "today", "description": "today as YYYY-MM-DD (left out: the computer's date)", "required": False}]
OUTPUTS = [{"name": "brief", "schema": {
    "type": "object",
    "properties": {
        "today": {"type": "string"},
        "target_day": {"type": "string"},
        "companies": {"type": "array", "items": {"type": "object", "properties": {
            "name": {"type": "string"}, "ticker": {"type": "string"}, "listed": {"type": "boolean"}},
            "required": ["name", "listed"]}},
    },
    "required": ["today", "target_day", "companies"]}}]


def run(ctx, inputs):
    setup = setup_problems()                                 # fail now, before any model call is paid for
    if setup:
        return {"error": "Cannot start. Settings missing in .env: " + " ".join(setup)}
    (data_dir() / PROBLEMS_FILE).unlink(missing_ok=True)       # a new run starts with no search problems
    today = datetime.date.fromisoformat(inputs["today"]) if inputs.get("today") else datetime.date.today()
    cfg = stocks()
    return {"brief": {"today": day_label(today), "target_day": day_label(next_trading_day(today)),
                      "companies": [{"name": c["name"], "ticker": c.get("ticker") or "", "listed": bool(c["listed"])}
                                     for c in cfg["companies"]]}}
