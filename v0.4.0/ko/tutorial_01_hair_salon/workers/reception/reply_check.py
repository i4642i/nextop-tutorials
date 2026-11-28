"""The reception's reply checker: a reply to a customer is written in Korean only.

The platform calls check_reply(reply, ctx) before a reply is sent. The only rule: no letters of another language.
Any letter that is not Hangul (Han characters, kana, Latin, Arabic, ...) is refused; digits, punctuation, prices
(20,000원), times (14:00), dates and phone numbers have no letters and pass. The Latin letters of the menu's own style
names (salon.json: C컬펌, S컬펌), written as on the menu, are part of a Korean name and pass. A refused reply is written
again with the reason (checklists.json "texts"); a second refusal sends the fallback reply (worker.json).
"""
import re

from functions._salon import style_names, text

HANGUL = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")
FOREIGN = re.compile(r"[^\W\d_ᄀ-ᇿ㄰-㆏가-힣]+")      # letters that are not Hangul


def _menu_parts() -> set[tuple[str, str]]:
    """(non-Hangul part, the Hangul letter right after it) in the menu's style names: ("C", "컬") of C컬펌."""
    return {(m.group(0), name[m.end()]) for name in style_names() for m in FOREIGN.finditer(name)
            if m.end() < len(name) and HANGUL.match(name, m.end())}


def check_reply(reply, ctx):
    allowed = _menu_parts()
    foreign = []
    for part in FOREIGN.finditer(reply):
        word = part.group(0)
        if (word, reply[part.end():part.end() + 1]) in allowed:
            continue
        if word not in foreign:
            foreign.append(word)
    return [text("reply_foreign", words=", ".join(foreign[:8]))] if foreign else []
