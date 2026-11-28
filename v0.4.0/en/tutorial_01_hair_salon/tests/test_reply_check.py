"""The reception's reply checks: reply_check.py keeps every reply English (no Hangul, Han characters, kana, ...;
digits, prices, times and phone numbers are fine), the reply LLM checker (worker.json "reply_checks") gets the step
notice, and the notice says why each missing required item is needed (checklists.json "need")."""
import importlib.util
import json

from conftest import Chat, FakeLLM, adapters, say
from nextop.adapters import Reply
from nextop.runtime.flow import run_ask


def _check(project_dir):
    spec = importlib.util.spec_from_file_location("reply_check", project_dir / "workers/reception/reply_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.check_reply


def test_an_english_reply_with_numbers_passes(project_dir):
    check = _check(project_dir)
    assert check("A Taper fade is $40 and takes 30 min. We'll text (555) 010-7777 about Dec 3 at 2:00 PM. Café-style!", {}) == []


def test_letters_of_any_other_language_are_refused_with_the_words_named(project_dir):
    check = _check(project_dir)
    got = check("Your booking 时间 is tomorrow. よろしく! 예약 then? ذهب", {})
    assert len(got) == 1 and "letters of another language" in got[0]
    for word in ("时间", "よろしく", "예약", "ذهب"):
        assert word in got[0]


def test_the_notice_says_why_a_missing_item_is_needed(salon):
    c = Chat(salon.ROOT, "c-need")
    c.put(purpose_booking=("haircut booking", "open"), service="cut", style={"style": "Box bob", "words": "a box bob"}, name="Chloe Park")
    notice = c.nav()["notice"]
    assert "mobile number (phone): We text the confirmation to it" in notice
    assert "cannot go on to picking a time (booking by phone works too)" in notice
    assert "name (name): The booking" not in notice                     # recorded: not named again


def test_a_mixed_reply_is_written_again_and_the_checker_sees_the_notice(proj, salon):
    c = Chat(salon.ROOT, "c-mix")
    c.put(purpose_booking=("haircut booking", "open"))
    fake = FakeLLM({"hana": [say("Which 시술 would you like?"), say("Which service would you like?")]})
    res = run_ask(proj, "reception", "I'd like to book", adapters=adapters(fake), subject="c-mix")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["answer"] == "Which service would you like?"
    checker = [m for who, m in fake.calls if who == "checker"]
    assert len(checker) == 1                                       # the first reply never reached the LLM check
    sent = checker[0][0]["content"]
    assert "Which service would you like?" in sent and "Still missing:" in sent        # the reply and the step notice
    rows = [json.loads(x) for x in (res.run_dir / "blocks/reception/attempt-1/reply_checks.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    assert rows[0]["checker"] == "program" and "시술" in rows[0]["reasons"][0]


def test_two_failed_replies_send_the_fallback(proj, salon):
    fake = FakeLLM({"hana": [say("はい!"), say("OK, 좋아요")]})
    res = run_ask(proj, "reception", "Hi", adapters=adapters(fake), subject="c-fb")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["answer"].startswith("Sorry, I can't answer that right away")
    fake2 = FakeLLM({"hana": [say("A haircut is $15."), say("I'll check the price with the price tool.")],
                     "checker": [Reply(text=json.dumps({"failed": [{"check": 1, "reason": "$15 is nowhere"}]})),
                                 Reply(text='{"failed": []}')]})
    res2 = run_ask(proj, "reception", "How much is a haircut?", adapters=adapters(fake2), subject="c-llm")
    assert res2.ok and res2.outputs["reception"]["answer"]["answer"] == "I'll check the price with the price tool."
