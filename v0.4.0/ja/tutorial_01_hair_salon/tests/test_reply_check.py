"""The reception's reply checks: reply_check.py keeps every reply Japanese (no Latin words, Hangul, ...;
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


def test_a_japanese_reply_with_numbers_passes(project_dir):
    check = _check(project_dir)
    assert check("ウルフカットは¥6,600で60分です。12月3日 14:00、090-1234-5678 へショートメッセージをお送りします！ｶﾀｶﾅ、々、ヶ月、〇〇駅", {}) == []


def test_letters_of_any_other_language_are_refused_with_the_words_named(project_dir):
    check = _check(project_dir)
    got = check("ご予約は明日です。안녕하세요! booking でよろしいですか？ＡＢＣ ذهب", {})
    assert len(got) == 1 and "ほかの言語の文字" in got[0]
    for word in ("안녕하세요", "booking", "ＡＢＣ", "ذهب"):
        assert word in got[0]


def test_the_notice_says_why_a_missing_item_is_needed(salon):
    c = Chat(salon.ROOT, "c-need")
    c.put(purpose_booking=("カットの予約", "open"), service="cut", style={"style": "ボブ", "words": "ボブで"}, name="井上 真央")
    notice = c.nav()["notice"]
    assert "携帯電話番号（phone）: 確定のショートメッセージをお送りし、ご本人確認をするために必要です" in notice
    assert "時間選びに進めません（お電話でもご予約いただけます）" in notice
    assert "お名前（name）: ご予約を" not in notice                     # recorded: not named again


def test_a_mixed_reply_is_written_again_and_the_checker_sees_the_notice(proj, salon):
    c = Chat(salon.ROOT, "c-mix")
    c.put(purpose_booking=("カットの予約", "open"))
    fake = FakeLLM({"hana": [say("どの service になさいますか？"), say("どのメニューになさいますか？")]})
    res = run_ask(proj, "reception", "予約したいです", adapters=adapters(fake), subject="c-mix")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["answer"] == "どのメニューになさいますか？"
    checker = [m for who, m in fake.calls if who == "checker"]
    assert len(checker) == 1                                       # the first reply never reached the LLM check
    sent = checker[0][0]["content"]
    assert "どのメニューになさいますか？" in sent and "残り:" in sent        # the reply and the step notice
    rows = [json.loads(x) for x in (res.run_dir / "blocks/reception/attempt-1/reply_checks.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    assert rows[0]["checker"] == "program" and "service" in rows[0]["reasons"][0]


def test_two_failed_replies_send_the_fallback(proj, salon):
    fake = FakeLLM({"hana": [say("OK!"), say("OK、いいですよ")]})
    res = run_ask(proj, "reception", "こんにちは", adapters=adapters(fake), subject="c-fb")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["answer"].startswith("申し訳ございません、今はすぐにお答えできません")
    fake2 = FakeLLM({"hana": [say("カットは¥1,500です。"), say("料金は料金ツールでお調べします。")],
                     "checker": [Reply(text=json.dumps({"failed": [{"check": 1, "reason": "¥1,500はどこにもない"}]})),
                                 Reply(text='{"failed": []}')]})
    res2 = run_ask(proj, "reception", "カットはいくらですか？", adapters=adapters(fake2), subject="c-llm")
    assert res2.ok and res2.outputs["reception"]["answer"]["answer"] == "料金は料金ツールでお調べします。"
