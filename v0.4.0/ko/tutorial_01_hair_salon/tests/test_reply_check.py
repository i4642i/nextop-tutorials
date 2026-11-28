"""The reception's reply checks: reply_check.py keeps every reply Korean (no Han characters, kana or Latin words;
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


def test_a_korean_reply_with_numbers_passes(project_dir):
    check = _check(project_dir)
    assert check("커트는 22,000원이고 40분 걸려요. 12월 3일 14:00, 010-1234-5678로 문자 드릴게요!", {}) == []


def test_letters_of_any_other_language_are_refused_with_the_words_named(project_dir):
    check = _check(project_dir)
    got = check("예약 时间은 내일이에요. よろしく! color로 할까요? ذهب", {})
    assert len(got) == 1 and "한국어가 아닌 글자" in got[0]
    for word in ("时间", "よろしく", "color", "ذهب"):
        assert word in got[0]


def test_the_notice_says_why_a_missing_item_is_needed(salon):
    c = Chat(salon.ROOT, "c-need")
    c.put(purpose_booking=("커트 예약", "open"), service="cut", style={"style": "단발(보브)", "words": "단발로요"}, name="최유나")
    notice = c.nav()["notice"]
    assert "휴대폰 번호(phone): 확정 문자를 보내고 본인 확인을 하는 데 필요합니다" in notice
    assert "시간 고르기로 넘어갈 수 없습니다(전화로도 예약할 수 있습니다)" in notice
    assert "성함(name): 예약을" not in notice                     # recorded: not named again


def test_a_mixed_reply_is_written_again_and_the_checker_sees_the_notice(proj, salon):
    c = Chat(salon.ROOT, "c-mix")
    c.put(purpose_booking=("커트 예약", "open"))
    fake = FakeLLM({"hana": [say("어떤 service를 원하세요?"), say("어떤 시술을 원하세요?")]})
    res = run_ask(proj, "reception", "예약하고 싶어요", adapters=adapters(fake), subject="c-mix")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["answer"] == "어떤 시술을 원하세요?"
    checker = [m for who, m in fake.calls if who == "checker"]
    assert len(checker) == 1                                       # the first reply never reached the LLM check
    sent = checker[0][0]["content"]
    assert "어떤 시술을 원하세요?" in sent and "남은 것:" in sent        # the reply and the step notice
    rows = [json.loads(x) for x in (res.run_dir / "blocks/reception/attempt-1/reply_checks.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    assert rows[0]["checker"] == "program" and "service" in rows[0]["reasons"][0]


def test_two_failed_replies_send_the_fallback(proj, salon):
    fake = FakeLLM({"hana": [say("OK!"), say("OK, 좋아요")]})
    res = run_ask(proj, "reception", "안녕하세요", adapters=adapters(fake), subject="c-fb")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["answer"].startswith("죄송해요, 지금은 답을 바로 드리기 어려워요")
    fake2 = FakeLLM({"hana": [say("가격은 15,000원이에요."), say("가격은 가격 도구로 알려 드릴게요.")],
                     "checker": [Reply(text=json.dumps({"failed": [{"check": 1, "reason": "15,000원은 어디에도 없음"}]})),
                                 Reply(text='{"failed": []}')]})
    res2 = run_ask(proj, "reception", "커트 얼마예요?", adapters=adapters(fake2), subject="c-llm")
    assert res2.ok and res2.outputs["reception"]["answer"]["answer"] == "가격은 가격 도구로 알려 드릴게요."
