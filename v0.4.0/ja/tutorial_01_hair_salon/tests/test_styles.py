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


PERM = {"perm_history": "3か月以内はしていません", "perm_damage": "健康なほうです"}
COLOR = {"color_want": "アッシュブラウン", "color_bleach": "ありません", "color_last": "1年前", "color_allergy": "ありません"}


def test_a_style_that_is_not_on_the_menu_is_refused_by_the_field_type(salon):
    c = Chat(salon.ROOT)
    res = c.put_raw(purpose_booking=("カットの予約", "open"), service="cut", style=style("モヒカン"))
    assert res.get("refused") or "error" in res
    text = json.dumps(res, ensure_ascii=False)
    assert "ツーブロック" in text                                 # the refusal names the menu
    assert not [r for r in c.rows("consult") if r["fields"]["item"] == "style"]
    c.put(style=style("ツーブロック"))                            # a menu name is written
    assert salon.records(c.rows("consult"))["style"]["style"] == "ツーブロック"


def test_the_notice_lists_the_menu_of_the_chosen_service_without_gender_labels(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("パーマの予約", "open"), service="perm", name="佐々木 健太", phone="080-3456-7890")
    notice = c.nav()["notice"]
    assert "次に伺うこと: スタイル（style" in notice
    perm = [s["name"] for s in salon.salon()["services"]["perm"]["styles"]]
    assert ", ".join(perm) in notice                              # the whole perm menu, from salon.json
    assert "ツーブロック" not in notice                           # only the chosen service's menu
    assert "スタイル（style）: 同じメニューでもスタイルによって" in notice   # why it is needed (checklists.json need)
    for word in ("男性", "女性", "メンズ", "レディース"):
        assert word not in notice
    assert not re.search(r"\b(men|women|common)\b", notice, re.I)


def test_a_style_of_another_service_is_asked_again(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カットの予約", "open"), service="cut", style=style("デジタルパーマ"))
    notice = c.nav()["notice"]
    assert salon.text("why_style_menu", names="デジタルパーマ", menus=salon.menu_text(["cut"])) in notice
    assert "error" in c.tool("book")


def test_one_style_per_service_and_a_one_style_menu_takes_its_style(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カットとパーマ", "open"), service="cut, perm", style=style("ツーブロック"))
    assert salon.text("why_style_missing", services="パーマ", menus=salon.menu_text(["perm"])) in c.nav()["notice"]
    c.put(style=style("ツーブロック", "マッシュ"))
    assert salon.text("why_style_twice", service="カット", names="ツーブロック, マッシュ") in c.nav()["notice"]
    c.put(style=style("ツーブロック", "ニュアンスパーマ"))
    assert "スタイル=ツーブロック, ニュアンスパーマ" in c.nav()["notice"]
    treat = Chat(salon.ROOT)
    treat.put(purpose_booking=("トリートメント", "open"), service="treatment")
    assert "（style" not in treat.nav()["notice"]                 # the treatment menu has one style: nothing to ask
    assert salon.visit_plan(salon.records(treat.rows("consult")))["styles"] == ["トリートメント"]


def test_recommend_asks_what_look_and_names_the_menu(salon):
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カットの予約", "open"), service="cut", style=style("おまかせ", words="よくわからないので、おすすめしてください"))
    notice = c.nav()["notice"]
    assert salon.text("why_recommend", field="style", menus=salon.menu_text(["cut"])) in notice
    assert "スタイル=" not in notice                              # not recorded as a style
    res = c.tool("book")
    assert "error" in res and "style" in res["error"]
    c.put(style=style("ハッシュカット"))
    notice = c.nav()["notice"]
    assert "スタイル=ハッシュカット" in notice and "おすすめを望んでいます" not in notice


def test_a_style_before_the_service_does_not_count(salon):
    """A style (or おまかせ) recorded before the service cannot be matched with a menu yet: the notice asks for the service,
    and once it is recorded a recommendation is asked for with that service's menu."""
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("カットの予約、おすすめしてください", "open"), style=style("おまかせ", words="わかりません"))
    notice = c.nav()["notice"]
    assert salon.text("why_style_service", service="service") in notice and "スタイル=" not in notice
    c.put(service="cut")
    assert salon.text("why_recommend", field="style", menus=salon.menu_text(["cut"])) in c.nav()["notice"]


def test_price_and_minutes_come_from_the_styles(salon):
    c = Chat(salon.ROOT)
    menu = {s["name"]: s for sv in salon.salon()["services"].values() for s in sv["styles"]}
    got = c.tool("price_quote", {"styles": ["ツーブロック"]})
    assert (got["price"], got["minutes"]) == (menu["ツーブロック"]["price"], menu["ツーブロック"]["minutes"])
    got = c.tool("price_quote", {"styles": ["デジタルパーマ", "全体カラー"]})
    assert got["price"] == menu["デジタルパーマ"]["price"] + menu["全体カラー"]["price"]
    assert got["minutes"] == menu["デジタルパーマ"]["minutes"] + menu["全体カラー"]["minutes"]
    assert got["services"] == ["パーマ", "カラー"]
    assert "error" in c.tool("price_quote", {"styles": ["ツーブロック", "マッシュ"]})     # two cuts in one visit
    listed = c.tool("price_quote", {"services": ["perm"]})["menu"][0]
    assert listed["service"] == "パーマ" and {"name": "デジタルパーマ", "price": menu["デジタルパーマ"]["price"],
                                            "minutes": menu["デジタルパーマ"]["minutes"]} in listed["styles"]
    assert c.tool("find_times", {"styles": ["デジタルパーマ"]})["minutes"] == menu["デジタルパーマ"]["minutes"]


def test_the_booking_takes_the_styles_price_and_minutes(salon):
    digital = next(s for s in salon.salon()["services"]["perm"]["styles"] if s["name"] == "デジタルパーマ")
    c = Chat(salon.ROOT)
    when = free_time(salon, "takahashi", digital["minutes"])
    c.put(purpose_booking=("デジタルパーマの予約", "open"), service="perm", style=style("デジタルパーマ"), name="木村 美月",
          phone="070-5555-1234", wish_time=when, designer="takahashi", **PERM)
    c.put(agree="はい、お願いします")
    res = c.tool("book")
    assert res["booked"] is True, res
    b = next(r["fields"] for r in c.rows("bookings") if r["fields"]["booking"] == res["booking"])
    assert b["styles"] == ["デジタルパーマ"] and b["services"] == ["perm"]
    assert (int(b["price"]), int(b["minutes"])) == (digital["price"], digital["minutes"])
    assert "パーマ（デジタルパーマ）" in res["line"]
    start = datetime.datetime.strptime(when, "%Y-%m-%d %H:%M")
    sched = [r["fields"] for r in c.rows("bookings")]
    held = salon.busy(sched, "takahashi", start.date())
    assert (start, start + datetime.timedelta(minutes=digital["minutes"])) in held    # the slot holds the style's time


def test_a_wished_time_too_short_for_the_style_is_not_free(salon):
    """The slot check uses the style's minutes: a long perm does not fit right before closing."""
    takahashi = salon.salon()["designers"]["takahashi"]
    day = datetime.date.today()
    while True:
        day += datetime.timedelta(days=1)
        if day.weekday() in takahashi["days"]:
            break
    close = datetime.datetime.combine(day, datetime.time(*map(int, takahashi["close"].split(":"))))
    late = close - datetime.timedelta(minutes=60)
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("パーマ", "open"), service="perm", style=style("デジタルパーマ"), name="木村 美月", phone="070-5555-1234",
          wish_time=f"{late:%Y-%m-%d %H:%M}", designer="takahashi", **PERM)
    assert "勤務時間" in c.nav()["notice"]
    c.put(service="cut", style=style("前髪カット"))
    c.put(cut_bangs="短めに")
    assert salon.text("agree_open", agree_id="agree") in c.nav()["notice"]   # a 30-minute cut fits


def test_menu_names_pass_and_latin_is_refused_by_the_japanese_only_check(project_dir):
    spec = importlib.util.spec_from_file_location("reply_check", project_dir / "workers/reception/reply_check.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.check_reply("ウルフカットや韓国風レイヤーカットはいかがですか？インナーカラーは¥11,000です。", {}) == []
    assert mod.check_reply("Wolf cut はいかがですか？", {})        # a style name in another language is refused
