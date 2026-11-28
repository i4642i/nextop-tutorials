"""The conversation navigator (workers/reception/navigator.py), called the way the platform calls it: the step it
picks and the notice it writes for each situation, from the consult rows the reception recorded, the identity check
and the bookings (read with the reception's rights; the notice shows only free times and the verified customer's own
bookings). Every sentence comes from checklists.json; the items come from checklists.json and salon.json."""
import datetime
import json

from conftest import Chat


def _tomorrow_free(salon, designer="nakamura", minutes=120):
    """A day and start where the designer is free for `minutes` (from the seeded calendar)."""
    sched = [r["fields"] for r in Chat(salon.ROOT).rows("bookings")]
    for n in range(1, 10):
        day = datetime.date.today() + datetime.timedelta(days=n)
        starts = salon.free_starts(sched, designer, day, minutes)
        if starts:
            return f"{day.isoformat()} {starts[0]}"
    raise AssertionError("no free time")


def _taken(salon, designer="nakamura"):
    """The start of a seeded booking of the designer: a time that is not free."""
    sched = [r["fields"] for r in Chat(salon.ROOT).rows("bookings")]
    f = next(f for f in sched if f["designer"] == designer)
    return f"{f['date']} {f['time']}"


COLOR = {"color_want": "アッシュブラウンで明るめ", "color_bleach": "ブリーチはしていません", "color_last": "半年前",
         "color_allergy": "ありません"}


def test_no_purpose_is_the_consult_step_and_asks_what_to_help(salon):
    got = Chat(salon.ROOT).nav()
    assert got["step"] == "consult"
    assert salon.text("no_purpose") in got["notice"]
    assert salon.text("today", day=salon.day_label(datetime.date.today())) in got["notice"]


def test_booking_items_are_collected_in_consult_and_named_by_id(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カラーの予約をしたいです", "open"), service="color")
    got = c.nav()
    assert got["step"] == "consult"
    head = salon.text("collect", label="ご予約", items="", next="").split("残り")[0]
    assert head in got["notice"]
    for item in ("name", "phone", "style", "wish_time", "color_want", "color_bleach", "color_last", "color_allergy"):
        assert f"（{item}" in got["notice"]
    assert "perm_history" not in got["notice"]                # only the recorded service's items apply
    assert "メニュー=color" in got["notice"]                       # recorded
    assert "次に伺うこと: お名前（name" in got["notice"]          # the first open item, in checklist order


def test_booking_step_when_all_but_the_agreement_is_recorded_and_the_time_is_free(salon):
    c = Chat(salon.ROOT)
    when = _tomorrow_free(salon)
    c.put(purpose_booking=("カラーの予約", "open"), service="color", style={"style": "全体カラー", "words": "全体カラーでお願いします"}, name="松本 彩",
          phone="090 0000 7777", wish_time=when, designer="nakamura", **COLOR)
    got = c.nav()
    assert got["step"] == "booking"
    assert ": 空いています。" in got["notice"] and salon.text("agree_open", agree_id="agree") in got["notice"]
    c.put(agree="はい、お願いします")
    got = c.nav()
    assert salon.text("book_now") in got["notice"]


def test_a_taken_wished_time_asks_for_another_time_and_keeps_the_agreement_open(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カラーの予約", "open"), service="color", style={"style": "全体カラー", "words": "全体カラーでお願いします"}, name="松本 彩",
          phone="090-0000-7777", wish_time=_taken(salon), designer="nakamura", agree="はい", **COLOR)
    got = c.nav()
    assert got["step"] == "booking"
    assert "ほかの予約があります" in got["notice"] and "find_times" in got["notice"]
    assert salon.text("book_now") not in got["notice"]
    res = c.tool("book")
    assert "error" in res and "ほかの予約があります" in res["error"]          # book refuses the taken slot


def test_the_agreement_counts_only_after_the_last_time_change(salon):
    import time
    c = Chat(salon.ROOT)
    first = _tomorrow_free(salon)
    c.put(purpose_booking=("カラーの予約", "open"), service="color", style={"style": "全体カラー", "words": "全体カラーでお願いします"}, name="松本 彩",
          phone="090-0000-7777", wish_time=first, designer="nakamura", agree="はい", **COLOR)
    assert salon.text("book_now") in c.nav()["notice"]
    time.sleep(1.1)                                            # row times have seconds
    later = (datetime.datetime.strptime(first, "%Y-%m-%d %H:%M") + datetime.timedelta(minutes=30))
    c.put(wish_time=f"{later:%Y-%m-%d %H:%M}")                 # the customer moves the time after agreeing
    got = c.nav()
    assert salon.text("book_now") not in got["notice"]
    assert salon.text("why_agree_stale") in got["notice"]
    assert "error" in c.tool("book")


def test_overwrite_keeps_the_final_value_and_switches_the_service_items(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カラーの予約", "open"), service="color", **COLOR)
    c.put(service="perm")                                      # the customer changes their mind
    rec = salon.records(c.rows("consult"))
    assert rec["service"]["words"] == "perm"
    got = c.nav()
    assert "perm_history" in got["notice"] and "color_want" not in got["notice"]
    row = next(r for r in c.rows("consult") if r["fields"]["item"] == "service")
    full = c.ctx["file_servers"]["consult"].get(row["address"])
    assert "color" in json.dumps(full, ensure_ascii=False)     # the old value is in the row's history


def test_two_purposes_in_one_message_are_both_in_the_notice(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カットの予約", "open"), purpose_info=("駐車場はありますか？", "open"))
    got = c.nav()
    assert got["step"] == "consult"
    assert salon.text("info_open", words="駐車場はありますか？") in got["notice"]
    assert "purpose_booking" in got["notice"] and "purpose_info" in got["notice"]


def test_a_recorded_answer_in_the_wrong_form_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カット", "open"), phone="1234", wish_time="土曜日の午後")
    got = c.nav()
    assert salon.text("why_phone") in got["notice"] and salon.text("why_datetime") in got["notice"]


def test_an_item_that_is_not_in_the_spec_files_is_refused_by_the_core(salon):
    res = Chat(salon.ROOT).put_raw(made_up="x")
    assert res.get("refused") or "error" in res


def test_manage_step_asks_for_name_and_phone_first(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_my_booking=("予約を確認したいです", "open"))
    got = c.nav()
    assert got["step"] == "manage"
    assert salon.text("verify_first") in got["notice"]
    c.put(name="佐藤 美咲", phone="090-0000-1002")                # a phone no booking has
    got = c.nav()
    assert salon.text("verify_failed") in got["notice"] and "-takahashi" not in got["notice"]   # no booking id
    c.put(phone="090-0000-1001")                              # the seeded booking's: the program checks it at once
    got = c.nav()
    assert salon.text("verified", lines="").split(":")[0] in got["notice"] and "高橋" in got["notice"]


def test_other_customer_never_sees_the_rows(salon):
    a, b = Chat(salon.ROOT), Chat(salon.ROOT)
    a.put(purpose_booking=("カラー", "open"), name="松本 彩", phone="090-0000-7777")
    assert not b.rows("consult")
    assert salon.text("no_purpose") in b.nav()["notice"]
    assert "松本 彩" not in b.nav()["notice"]


def test_all_purposes_done_asks_for_anything_else(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_info=("営業時間", "done"))
    got = c.nav()
    assert got["step"] == "consult" and salon.text("all_done") in got["notice"]


def test_a_name_with_a_sentence_ending_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カット", "open"), name="佐々木 健太です")
    got = c.nav()
    assert salon.text("why_name") in got["notice"]
    c.put(name="佐々木 健太")
    assert salon.text("why_name") not in c.nav()["notice"]
