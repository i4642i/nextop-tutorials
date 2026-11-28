"""The menu: the customer picks a style per service (salon.json services.<id>.styles), never a hair length. The style
row's style field is a choice of the menu names (the project choice part reads them from salon.json), so a name that
is not on the menu is refused by the core; the navigator checks the names against the chosen services, lists their
menus while the style is open, and turns a request for a recommendation into a notice that asks what look the customer
wants. Prices and minutes come from the chosen styles: price_quote, find_times, book and the designer's mail."""
import datetime
import importlib.util
import json

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


PERM = {"perm_history": "3개월 안에는 안 했어요", "perm_damage": "건강한 편이에요"}
COLOR = {"color_want": "애쉬 브라운", "color_bleach": "없어요", "color_last": "1년 전", "color_allergy": "없어요"}


def test_a_style_that_is_not_on_the_menu_is_refused_by_the_field_type(salon):
    c = Chat(salon.ROOT)
    res = c.put_raw(purpose_booking=("커트 예약", "open"), service="cut", style=style("모히칸컷"))
    assert res.get("refused") or "error" in res
    text = json.dumps(res, ensure_ascii=False)
    assert "투블럭" in text                                       # the refusal names the menu
    assert not [r for r in c.rows("consult") if r["fields"]["item"] == "style"]
    c.put(style=style("투블럭"))                                  # a menu name is written
    assert salon.records(c.rows("consult"))["style"]["style"] == "투블럭"


def test_the_notice_lists_the_menu_of_the_chosen_service_without_gender_labels(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("펌 예약", "open"), service="perm", name="박지훈", phone="010-3456-7890")
    notice = c.nav()["notice"]
    assert "다음에 물을 것: 스타일(style" in notice
    perm = [s["name"] for s in salon.salon()["services"]["perm"]["styles"]]
    assert ", ".join(perm) in notice                              # the whole perm menu, from salon.json
    assert "투블럭" not in notice                                 # only the chosen service's menu
    assert "스타일(style): 시술마다 스타일에 따라 가격과" in notice      # why it is needed (checklists.json need)
    for word in ("남성", "여성", "남자", "여자", "men", "women"):
        assert word not in notice


def test_a_style_of_another_service_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("커트 예약", "open"), service="cut", style=style("히피펌"))
    notice = c.nav()["notice"]
    assert salon.text("why_style_menu", names="히피펌", menus=salon.menu_text(["cut"])) in notice
    assert "error" in c.tool("book")


def test_one_style_per_service_and_a_one_style_menu_takes_its_style(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("커트하고 펌", "open"), service="cut, perm", style=style("투블럭"))
    assert salon.text("why_style_missing", services="펌", menus=salon.menu_text(["perm"])) in c.nav()["notice"]
    c.put(style=style("투블럭", "댄디컷"))
    assert salon.text("why_style_twice", service="커트", names="투블럭, 댄디컷") in c.nav()["notice"]
    c.put(style=style("투블럭", "다운펌"))
    assert "스타일=투블럭, 다운펌" in c.nav()["notice"]
    clinic = Chat(salon.ROOT)
    clinic.put(purpose_booking=("클리닉", "open"), service="clinic")
    assert "(style" not in clinic.nav()["notice"]                 # the clinic menu has one style: nothing to ask
    assert salon.visit_plan(salon.records(clinic.rows("consult")))["styles"] == ["클리닉"]


def test_recommend_asks_what_look_and_names_the_menu(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("커트 예약", "open"), service="cut", style=style("추천", words="잘 모르겠어요, 추천해 주세요"))
    notice = c.nav()["notice"]
    assert salon.text("why_recommend", field="style", menus=salon.menu_text(["cut"])) in notice
    assert "스타일=" not in notice                                # not recorded as a style
    res = c.tool("book")
    assert "error" in res and "style" in res["error"]
    c.put(style=style("리프컷"))
    notice = c.nav()["notice"]
    assert "스타일=리프컷" in notice and "추천을 원합니다" not in notice


def test_a_style_before_the_service_does_not_count(salon):
    """A style (or 추천) recorded before the service cannot be matched with a menu yet: the notice asks for the service,
    and once it is recorded a recommendation is asked for with that service's menu."""
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("커트 예약, 추천해 주세요", "open"), style=style("추천", words="모르겠어요"))
    notice = c.nav()["notice"]
    assert salon.text("why_style_service", service="service") in notice and "스타일=" not in notice
    c.put(service="cut")
    assert salon.text("why_recommend", field="style", menus=salon.menu_text(["cut"])) in c.nav()["notice"]


def test_price_and_minutes_come_from_the_styles(salon):
    c = Chat(salon.ROOT)
    menu = {s["name"]: s for sv in salon.salon()["services"].values() for s in sv["styles"]}
    got = c.tool("price_quote", {"styles": ["투블럭"]})
    assert (got["price"], got["minutes"]) == (menu["투블럭"]["price"], menu["투블럭"]["minutes"])
    got = c.tool("price_quote", {"styles": ["히피펌", "전체 염색"]})
    assert got["price"] == menu["히피펌"]["price"] + menu["전체 염색"]["price"]
    assert got["minutes"] == menu["히피펌"]["minutes"] + menu["전체 염색"]["minutes"]
    assert got["services"] == ["펌", "염색"]
    assert "error" in c.tool("price_quote", {"styles": ["투블럭", "댄디컷"]})     # two cuts in one visit
    listed = c.tool("price_quote", {"services": ["perm"]})["menu"][0]
    assert listed["service"] == "펌" and {"name": "히피펌", "price": menu["히피펌"]["price"],
                                         "minutes": menu["히피펌"]["minutes"]} in listed["styles"]
    assert c.tool("find_times", {"styles": ["히피펌"]})["minutes"] == menu["히피펌"]["minutes"]


def test_the_booking_takes_the_styles_price_and_minutes(salon):
    hippie = next(s for s in salon.salon()["services"]["perm"]["styles"] if s["name"] == "히피펌")
    c = Chat(salon.ROOT)
    when = free_time(salon, "jisu", hippie["minutes"])
    c.put(purpose_booking=("히피펌 예약", "open"), service="perm", style=style("히피펌"), name="김민지",
          phone="010-5555-1234", wish_time=when, designer="jisu", **PERM)
    c.put(agree="네 좋아요")
    res = c.tool("book")
    assert res["booked"] is True, res
    b = next(r["fields"] for r in c.rows("bookings") if r["fields"]["booking"] == res["booking"])
    assert b["styles"] == ["히피펌"] and b["services"] == ["perm"]
    assert (int(b["price"]), int(b["minutes"])) == (hippie["price"], hippie["minutes"])
    assert "펌(히피펌)" in res["line"]
    start = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
    sched = [r["fields"] for r in c.rows("bookings")]
    held = salon.busy(sched, "jisu", start.date())
    assert (start, start + datetime.timedelta(minutes=hippie["minutes"])) in held    # the slot holds the style's time


def test_a_wished_time_too_short_for_the_style_is_not_free(salon):
    """The slot check uses the style's minutes: a long perm does not fit right before closing."""
    jisu = salon.salon()["designers"]["jisu"]
    day = datetime.date.today()
    while True:
        day += datetime.timedelta(days=1)
        if day.weekday() in jisu["days"]:
            break
    close = datetime.datetime.combine(day, datetime.time(*map(int, jisu["close"].split(":"))))
    late = close - datetime.timedelta(minutes=60)
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("펌", "open"), service="perm", style=style("히피펌"), name="김민지", phone="010-5555-1234",
          wish_time=f"{late:%Y-%m-%d %H:%M}", designer="jisu", **PERM)
    assert "근무 시간" in c.nav()["notice"]
    c.put(service="cut", style=style("버즈컷"))
    c.put(cut_bangs="짧게요")
    assert salon.text("agree_open", agree_id="agree") in c.nav()["notice"]   # a 30-minute cut fits


def test_menu_names_with_latin_letters_pass_the_korean_only_check(project_dir):
    spec = importlib.util.spec_from_file_location("reply_check", project_dir / "workers/reception/reply_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check_reply("C컬펌이나 S컬펌, 글램(볼륨) 펌은 어떠세요? C컬로 하시면 90,000원이에요.", {}) == []
    assert mod.check_reply("C로 할까요?", {})                      # a lone letter is still refused
