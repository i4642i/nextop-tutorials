"""The reception's reply checker: a reply to a customer is written in Japanese only.

The platform calls check_reply(reply, ctx) before a reply is sent. The only rule: no letters of another language.
Hiragana, katakana (with the long vowel mark and half-width katakana) and kanji (with 々, 〆, ヶ and the kanji zero 〇, as in 〇〇駅) are Japanese; any
other letter (Latin, also full-width Latin, Hangul, Cyrillic, Arabic, ...) is refused. Digits, punctuation, prices
(¥8,800), times (14:00), dates and phone numbers have no letters and pass. The menu's own style names (salon.json) are
written as on the menu and pass whatever letters they hold, so a menu name with Latin letters would not be refused.
A refused reply is written again with the reason (checklists.json "texts"); a second refusal sends the fallback reply
(worker.json). Chinese written in Han characters looks like kanji to this check and passes: a letter check cannot tell
the two apart.
"""
import re

from functions._salon import style_names, text

# letters that are not Japanese: \w letters outside hiragana, katakana (and its phonetic extensions), half-width
# katakana, the CJK ideographs (with extension A and the compatibility block) and 々 〆 ヶ 〇
FOREIGN = re.compile(r"[^\W\d_぀-ゟ゠-ヿㇰ-ㇿｦ-ﾟ"
                     r"㐀-䶿一-鿿豈-﫿々〆ヶ〇]+")


def check_reply(reply, ctx):
    rest = str(reply or "")
    for name in sorted(style_names(), key=len, reverse=True):     # menu names pass as written
        rest = rest.replace(name, " ")
    foreign = []
    for part in FOREIGN.finditer(rest):
        if part.group(0) not in foreign:
            foreign.append(part.group(0))
    return [text("reply_foreign", words=", ".join(foreign[:8]))] if foreign else []
