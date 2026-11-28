"""The reception's reply checker: a reply to a customer is written in English only.

The platform calls check_reply(reply, ctx) before a reply is sent. The only rule: no letters of another language.
Any letter that is not Latin (Hangul, Han characters, kana, Cyrillic, Arabic, ...) is refused; Latin letters with
accents (café, Zoë) are English enough and pass, and digits, punctuation, prices ($75), times (2:30 PM), dates and
phone numbers have no other letters and pass. The menu's own style names (salon.json) are written as on the menu and
pass whatever letters they hold, so a menu name in another script (none today) would not be refused. A refused reply is
written again with the reason (checklists.json "texts"); a second refusal sends the fallback reply (worker.json).
"""
import re

from functions._salon import style_names, text

# letters that are not Latin: \w letters outside Basic Latin, Latin-1, Latin Extended A/B and the IPA/Latin Extended
# Additional blocks
FOREIGN = re.compile(r"[^\W\d_A-Za-zÀ-ɏḀ-ỿ]+")


def check_reply(reply, ctx):
    rest = str(reply or "")
    for name in sorted(style_names(), key=len, reverse=True):     # menu names pass as written
        rest = rest.replace(name, " ")
    foreign = []
    for part in FOREIGN.finditer(rest):
        if part.group(0) not in foreign:
            foreign.append(part.group(0))
    return [text("reply_foreign", words=", ".join(foreign[:8]))] if foreign else []
