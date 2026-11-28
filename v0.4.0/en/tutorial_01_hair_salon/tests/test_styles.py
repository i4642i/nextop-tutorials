"""The menu: the customer picks a style per service (salon.json services.<id>.styles), never a hair length. The style
row's style field is a choice of the menu names (the project choice part reads them from salon.json), so a name that
is not on the menu is refused by the core; the navigator checks the names against the chosen services, lists their
menus while the style is open, and turns a request for a recommendation into a notice that asks what look the customer
wants. Prices and minutes come from the chosen styles: price_quote, find_times, book and the designer's mail."""
import datetime
import importlib.util
import json
import re

from conftest import Chat


def style(*names, words=None):
    return {"style": ", ".join(names), "words": words or ", ".join(names)}


def free_time(salon, designer, minutes):
    sched = [r["fields"] for r in Chat(salon.ROOT).rows("bookings")]
    for n in range(1, 12):
        day = datetime.date.today() + datetime.timedelta(days=n)
        starts = salon.free_starts(sched, designer, day, minutes)
        if starts:
            return f"{day.isoformat()} {starts[0]}"
    raise AssertionError("no free time")


PERM = {"perm_history": "nothing in the last 3 months", "perm_damage": "pretty healthy"}
COLOR = {"color_want": "ash brown", "color_bleach": "none", "color_last": "a year ago", "color_allergy": "none"}


def test_a_style_that_is_not_on_the_menu_is_refused_by_the_field_type(salon):
    c = Chat(salon.ROOT)
    res = c.put_raw(purpose_booking=("haircut booking", "open"), service="cut", style=style("Mohawk"))
    assert res.get("refused") or "error" in res
    text = json.dumps(res, ensure_ascii=False)
    assert "Taper fade" in text                                   # the refusal names the menu
    assert not [r for r in c.rows("consult") if r["fields"]["item"] == "style"]
    c.put(style=style("Taper fade"))                              # a menu name is written
    assert salon.records(c.rows("consult"))["style"]["style"] == "Taper fade"


def test_the_notice_lists_the_menu_of_the_chosen_service_without_gender_labels(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("perm booking", "open"), service="perm", name="Daniel Kim", phone="(312) 555-0190")
    notice = c.nav()["notice"]
    assert "Ask next: style (style" in notice
    perm = [s["name"] for s in salon.salon()["services"]["perm"]["styles"]]
    assert ", ".join(perm) in notice                              # the whole perm menu, from salon.json
    assert "Taper fade" not in notice                             # only the chosen service's menu
    assert "style (style): Within a service, the price" in notice   # why it is needed (checklists.json need)
    assert not re.search(r"\b(men|women|male|female|man|woman)\b", notice, re.I)


def test_a_style_of_another_service_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("haircut booking", "open"), service="cut", style=style("Spiral perm"))
    notice = c.nav()["notice"]
    assert salon.text("why_style_menu", names="Spiral perm", menus=salon.menu_text(["cut"])) in notice
    assert "error" in c.tool("book")


def test_one_style_per_service_and_a_one_style_menu_takes_its_style(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("a haircut and a perm", "open"), service="cut, perm", style=style("Taper fade"))
    assert salon.text("why_style_missing", services="Perm / texture", menus=salon.menu_text(["perm"])) in c.nav()["notice"]
    c.put(style=style("Taper fade", "Mid fade"))
    assert salon.text("why_style_twice", service="Haircut", names="Taper fade, Mid fade") in c.nav()["notice"]
    c.put(style=style("Taper fade", "Texture perm"))
    assert "style=Taper fade, Texture perm" in c.nav()["notice"]
    treat = Chat(salon.ROOT)
    treat.put(purpose_booking=("a treatment", "open"), service="treatment")
    assert "(style" not in treat.nav()["notice"]                  # the treatment menu has one style: nothing to ask
    assert salon.visit_plan(salon.records(treat.rows("consult")))["styles"] == ["Bond repair treatment"]


def test_recommend_asks_what_look_and_names_the_menu(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("haircut booking", "open"), service="cut", style=style("recommend", words="not sure, what do you suggest?"))
    notice = c.nav()["notice"]
    assert salon.text("why_recommend", field="style", menus=salon.menu_text(["cut"])) in notice
    assert "style=" not in notice                                  # not recorded as a style
    res = c.tool("book")
    assert "error" in res and "style" in res["error"]
    c.put(style=style("Long layers"))
    notice = c.nav()["notice"]
    assert "style=Long layers" in notice and "wants a style suggestion" not in notice


def test_a_style_before_the_service_does_not_count(salon):
    """A style (or recommend) recorded before the service cannot be matched with a menu yet: the notice asks for the service,
    and once it is recorded a recommendation is asked for with that service's menu."""
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("a haircut, please suggest one", "open"), style=style("recommend", words="no idea"))
    notice = c.nav()["notice"]
    assert salon.text("why_style_service", service="service") in notice and "style=" not in notice
    c.put(service="cut")
    assert salon.text("why_recommend", field="style", menus=salon.menu_text(["cut"])) in c.nav()["notice"]


def test_price_and_minutes_come_from_the_styles(salon):
    c = Chat(salon.ROOT)
    menu = {s["name"]: s for sv in salon.salon()["services"].values() for s in sv["styles"]}
    got = c.tool("price_quote", {"styles": ["Taper fade"]})
    assert (got["price"], got["minutes"]) == (menu["Taper fade"]["price"], menu["Taper fade"]["minutes"])
    got = c.tool("price_quote", {"styles": ["Spiral perm", "All-over color"]})
    assert got["price"] == menu["Spiral perm"]["price"] + menu["All-over color"]["price"]
    assert got["minutes"] == menu["Spiral perm"]["minutes"] + menu["All-over color"]["minutes"]
    assert got["services"] == ["Perm / texture", "Color"]
    assert "error" in c.tool("price_quote", {"styles": ["Taper fade", "Mid fade"]})     # two cuts in one visit
    listed = c.tool("price_quote", {"services": ["perm"]})["menu"][0]
    assert listed["service"] == "Perm / texture" and {"name": "Spiral perm", "price": menu["Spiral perm"]["price"],
                                                    "minutes": menu["Spiral perm"]["minutes"]} in listed["styles"]
    assert c.tool("find_times", {"styles": ["Spiral perm"]})["minutes"] == menu["Spiral perm"]["minutes"]


def test_the_booking_takes_the_styles_price_and_minutes(salon):
    spiral = next(s for s in salon.salon()["services"]["perm"]["styles"] if s["name"] == "Spiral perm")
    c = Chat(salon.ROOT)
    when = free_time(salon, "jordan", spiral["minutes"])
    c.put(purpose_booking=("spiral perm booking", "open"), service="perm", style=style("Spiral perm"), name="Mia Kim",
          phone="(312) 555-0134", wish_time=when, designer="jordan", **PERM)
    c.put(agree="yes, sounds good")
    res = c.tool("book")
    assert res["booked"] is True, res
    b = next(r["fields"] for r in c.rows("bookings") if r["fields"]["booking"] == res["booking"])
    assert b["styles"] == ["Spiral perm"] and b["services"] == ["perm"]
    assert (int(b["price"]), int(b["minutes"])) == (spiral["price"], spiral["minutes"])
    assert "Perm / texture (Spiral perm)" in res["line"]
    start = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
    sched = [r["fields"] for r in c.rows("bookings")]
    held = salon.busy(sched, "jordan", start.date())
    assert (start, start + datetime.timedelta(minutes=spiral["minutes"])) in held    # the slot holds the style's time


def test_a_wished_time_too_short_for_the_style_is_not_free(salon):
    """The slot check uses the style's minutes: a long perm does not fit right before closing."""
    jordan = salon.salon()["designers"]["jordan"]
    day = datetime.date.today()
    while True:
        day += datetime.timedelta(days=1)
        if day.weekday() in jordan["days"]:
            break
    close = datetime.datetime.combine(day, datetime.time(*map(int, jordan["close"].split(":"))))
    late = close - datetime.timedelta(minutes=60)
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("a perm", "open"), service="perm", style=style("Spiral perm"), name="Mia Kim", phone="(312) 555-0134",
          wish_time=f"{late:%Y-%m-%d %H:%M}", designer="jordan", **PERM)
    assert "outside Jordan's hours" in c.nav()["notice"]
    c.put(service="cut", style=style("Buzz cut"))
    c.put(cut_bangs="short please")
    assert salon.text("agree_open", agree_id="agree") in c.nav()["notice"]   # a 30-minute cut fits


def test_menu_names_and_accents_pass_the_english_only_check(project_dir):
    spec = importlib.util.spec_from_file_location("reply_check", project_dir / "workers/reception/reply_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check_reply("How about a Modern shag or Long layers? A Balayage is $250, and the café next door is nice.", {}) == []
    assert mod.check_reply("How about a 투블럭?", {})                # a style name in another language is refused
