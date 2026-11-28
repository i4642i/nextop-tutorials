"""Project field type part "choice" (replaces the official one in this project): one of the values in "of", as
before, or one of the values a spec file of the project names ("from"):

  {"name": "item", "type": "choice", "from": "checklists.json"}
      the consult item ids: purpose_<id> for every purpose of checklists.json, the items of every purpose (except
      computed ones, which only the program decides), and the checklist items of every service in salon.json.
  {"name": "style", "type": "choice", "from": "salon.json", "many": true}
      the menu: every style name of every service in salon.json, and its "recommend" value (the customer wants a
      suggestion). With "many": several, comma separated (one style per service).

The values then live in the spec files only: this part reads them on every check, so an item or a style added there
can be recorded at once, a put with a value that is not one of them is refused by the core, and nothing is copied
into type.json.
"""

from __future__ import annotations

import json
import pathlib

from nextop.parts.field_type import choice as official

ROOT = pathlib.Path(__file__).resolve().parents[2]          # <project>/parts/field_type/choice.py -> <project>
SETTINGS = ("of", "from", "many")
PURPOSE = "purpose_"


def _read(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _item_ids() -> list[str]:
    data = _read("checklists.json")
    ids = [PURPOSE + p for p in data["purposes"]]
    for p in data["purposes"].values():
        ids += [str(i["id"]) for i in p.get("items") or [] if not i.get("computed")]
    for s in _read("salon.json")["services"].values():
        ids += [str(q["id"]) for q in s.get("checklist") or []]
    return ids


def _style_names() -> list[str]:
    salon = _read("salon.json")
    return [str(st["name"]) for s in salon["services"].values() for st in s.get("styles") or []] + [salon["recommend"]]


SOURCES = {"checklists.json": _item_ids, "salon.json": _style_names}


def _ids(field: dict) -> list[str]:
    return list(dict.fromkeys(SOURCES[field["from"]]()))


def _values(value, field: dict) -> list:
    if field.get("many") and isinstance(value, str):
        return [v.strip() for v in value.split(",")]
    return [value]


def check_field(field: dict) -> str | None:
    if "from" not in field:
        if "many" in field:
            return "\"many\" goes with \"from\""
        return official.check_field(field)
    if "of" in field:
        return "a choice takes \"of\" or \"from\", not both"
    name = field["from"]
    if name not in SOURCES:
        return f"\"from\" is one of: {', '.join(SOURCES)}"
    if not isinstance(field.get("many", False), bool):
        return "\"many\" is true or false"
    try:
        ids = _ids(field)
    except (OSError, ValueError, KeyError, TypeError) as e:
        return f"\"from\": cannot read the values of {name} ({e})"
    if not ids:
        return f"\"from\": {name} names no values"
    return None


def check(value, field: dict, context: dict | None = None) -> str | None:
    if "from" not in field:
        return official.check(value, field, context)
    ids = _ids(field)
    got = _values(value, field)
    if got and all(isinstance(v, str) and v in ids for v in got):
        return None
    if field.get("many"):
        return f"use one or more of (comma separated): {', '.join(ids)}"
    return f"use exactly one of: {', '.join(ids)}"


def normalize(value, field: dict | None = None):
    """One spelling: several values joined with ", "; a single value unchanged."""
    if field and field.get("many") and isinstance(value, str):
        return ", ".join(v.strip() for v in value.split(","))
    return value
