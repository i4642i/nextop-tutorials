"""The conversation navigator (workers/reception/navigator.py), called the way the platform calls it: the step it
picks and the notice it writes for each situation, from the consult rows the reception recorded, the identity check
and the bookings (read with the reception's rights; the notice shows only free times and the verified customer's own
bookings). Every sentence comes from checklists.json; the items come from checklists.json and salon.json."""
import datetime
import json

from conftest import Chat


def _tomorrow_free(salon, designer="maya", minutes=120):
    """A day and start where the designer is free for `minutes` (from the seeded calendar)."""
    sched = [r["fields"] for r in Chat(salon.ROOT).rows("bookings")]
    for n in range(1, 10):
        day = datetime.date.today() + datetime.timedelta(days=n)
        starts = salon.free_starts(sched, designer, day, minutes)
        if starts:
            return f"{day.isoformat()} {starts[0]}"
    raise AssertionError("no free time")


def _taken(salon, designer="maya"):
    """The start of a seeded booking of the designer: a time that is not free."""
    sched = [r["fields"] for r in Chat(salon.ROOT).rows("bookings")]
    f = next(f for f in sched if f["designer"] == designer)
    return f"{f['date']} {f['time']}"


COLOR = {"color_want": "ash brown, a bit lighter", "color_bleach": "no bleach before", "color_last": "6 months ago",
         "color_allergy": "none"}


def test_no_purpose_is_the_consult_step_and_asks_what_to_help(salon):
    got = Chat(salon.ROOT).nav()
    assert got["step"] == "consult"
    assert salon.text("no_purpose") in got["notice"]
    assert salon.text("today", day=salon.day_label(datetime.date.today())) in got["notice"]


def test_booking_items_are_collected_in_consult_and_named_by_id(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("I'd like to book a color", "open"), service="color")
    got = c.nav()
    assert got["step"] == "consult"
    head = salon.text("collect", label="booking", items="", next="").split("Still missing")[0]
    assert head in got["notice"]
    for item in ("name", "phone", "style", "wish_time", "color_want", "color_bleach", "color_last", "color_allergy"):
        assert f"({item}" in got["notice"]
    assert "perm_history" not in got["notice"]                # only the recorded service's items apply
    assert "service=color" in got["notice"]                       # recorded
    assert "Ask next: name (name" in got["notice"]          # the first open item, in checklist order


def test_booking_step_when_all_but_the_agreement_is_recorded_and_the_time_is_free(salon):
    c = Chat(salon.ROOT)
    when = _tomorrow_free(salon)
    c.put(purpose_booking=("color booking", "open"), service="color", style={"style": "All-over color", "words": "all-over color please"}, name="Grace Lee",
          phone="212 555 0177", wish_time=when, designer="maya", **COLOR)
    got = c.nav()
    assert got["step"] == "booking"
    assert ": free." in got["notice"] and salon.text("agree_open", agree_id="agree") in got["notice"]
    c.put(agree="yes, sounds good")
    got = c.nav()
    assert salon.text("book_now") in got["notice"]


def test_a_taken_wished_time_asks_for_another_time_and_keeps_the_agreement_open(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("color booking", "open"), service="color", style={"style": "All-over color", "words": "all-over color please"}, name="Grace Lee",
          phone="(212) 555-0177", wish_time=_taken(salon), designer="maya", agree="yes", **COLOR)
    got = c.nav()
    assert got["step"] == "booking"
    assert "has another booking" in got["notice"] and "find_times" in got["notice"]
    assert salon.text("book_now") not in got["notice"]
    res = c.tool("book")
    assert "error" in res and "has another booking" in res["error"]          # book refuses the taken slot


def test_the_agreement_counts_only_after_the_last_time_change(salon):
    import time
    c = Chat(salon.ROOT)
    first = _tomorrow_free(salon)
    c.put(purpose_booking=("color booking", "open"), service="color", style={"style": "All-over color", "words": "all-over color please"}, name="Grace Lee",
          phone="(212) 555-0177", wish_time=first, designer="maya", agree="yes", **COLOR)
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
    c.put(purpose_booking=("color booking", "open"), service="color", **COLOR)
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
    c.put(purpose_booking=("haircut booking", "open"), purpose_info=("Is there parking?", "open"))
    got = c.nav()
    assert got["step"] == "consult"
    assert salon.text("info_open", words="Is there parking?") in got["notice"]
    assert "purpose_booking" in got["notice"] and "purpose_info" in got["notice"]


def test_a_recorded_answer_in_the_wrong_form_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("a haircut", "open"), phone="1234", wish_time="Saturday afternoon")
    got = c.nav()
    assert salon.text("why_phone") in got["notice"] and salon.text("why_datetime") in got["notice"]


def test_an_item_that_is_not_in_the_spec_files_is_refused_by_the_core(salon):
    res = Chat(salon.ROOT).put_raw(made_up="x")
    assert res.get("refused") or "error" in res


def test_manage_step_asks_for_name_and_phone_first(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_my_booking=("Please check my booking", "open"))
    got = c.nav()
    assert got["step"] == "manage"
    assert salon.text("verify_first") in got["notice"]
    c.put(name="Emily Carter", phone="(212) 555-0102")                # a phone no booking has
    got = c.nav()
    assert salon.text("verify_failed") in got["notice"] and "-jordan" not in got["notice"]   # no booking id
    c.put(phone="(212) 555-0101")                              # the seeded booking's: the program checks it at once
    got = c.nav()
    assert salon.text("verified", lines="").split(":")[0] in got["notice"] and "Jordan" in got["notice"]


def test_other_customer_never_sees_the_rows(salon):
    a, b = Chat(salon.ROOT), Chat(salon.ROOT)
    a.put(purpose_booking=("color", "open"), name="Grace Lee", phone="(212) 555-0177")
    assert not b.rows("consult")
    assert salon.text("no_purpose") in b.nav()["notice"]
    assert "Grace Lee" not in b.nav()["notice"]


def test_all_purposes_done_asks_for_anything_else(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_info=("opening hours", "done"))
    got = c.nav()
    assert got["step"] == "consult" and salon.text("all_done") in got["notice"]


def test_a_name_with_a_sentence_ending_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("a haircut", "open"), name="I'm Daniel Kim")
    got = c.nav()
    assert salon.text("why_name") in got["notice"]
    c.put(name="Daniel Kim")
    assert salon.text("why_name") not in c.nav()["notice"]
