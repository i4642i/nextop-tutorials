"""The tools and the flows, run for real (a scripted LLM only where a worker answers): booking only in the booking
step, the book tool's writes (bookings, consult, customers) with the reception's rights, the identity check by name and
phone (never the browser's customer id), what the tools and the notice may say before and after it (nothing about any
booking before; only the customer's own after), change and cancel (with the customer's confirmation) of the verified
customer's own bookings only, the summary worker and the designer's mail, the designer's answer, and the end of the
chat."""
import datetime
import json
import socketserver
import threading

import pytest
from conftest import Chat, FakeLLM, adapters, call, rows, save, say
from nextop.runtime.flow import run_ask, run_flow

COLOR = {"color_want": "애쉬 브라운, 밝게", "color_bleach": "탈색은 안 했어요", "color_last": "6개월 전",
         "color_allergy": "없어요"}
SEEDED = {"name": "김하늘", "phone": "010-0000-1001"}          # data/seed_bookings.json: jisu's perm


def owner_rows(project_dir, server):
    """Every row of a file server, read as a function with read all (the tests' look behind the reception)."""
    from nextop.core.load import load_project
    from nextop.file_server import FileServerRuntime
    from functions._salon import rows_of
    rt = FileServerRuntime(load_project(str(project_dir)), {"llm": {}}, project_dir / "runs" / "t-owner", None, "")
    principal = {"bookings": "load_visit", "customers": "person:owner"}[server]
    got = rt.servers[[s.fs.name for s in rt.servers].index(server)].rows(principal, None, "files", log=False)
    return [r["fields"] for r in rows_of(got)]


def free_time(salon, designer="minho", minutes=120, skip=0):
    sched = [r["fields"] for r in Chat(salon.ROOT).rows("bookings")]
    found = []
    for n in range(1, 12):
        day = datetime.date.today() + datetime.timedelta(days=n)
        found += [f"{day.isoformat()} {t}" for t in salon.free_starts(sched, designer, day, minutes)]
        if len(found) > skip:
            return found[skip]
    raise AssertionError("no free time")


def ready_booking(c, salon, agree=True):
    c.put(purpose_booking=("염색 예약하고 싶어요", "open"), service="color", style={"style": "전체 염색", "words": "전체 염색이요"}, name="윤서연",
          phone="010-0000-7777", wish_time=free_time(salon), designer="minho", **COLOR)
    if agree:
        c.put(agree="네 좋아요")


def _tool_rows(run_dir, name):
    out = []
    for path in run_dir.rglob("tools.jsonl"):
        out += [r for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r.get("name") == name]
    return out


def test_book_is_only_offered_in_the_booking_step(proj, salon):
    c = Chat(salon.ROOT, "c-step")
    c.put(purpose_booking=("커트 예약", "open"))
    fake = FakeLLM({"hana": [say("어떤 시술을 원하세요?")]})
    res = run_ask(proj, "reception", "예약하고 싶어요", adapters=adapters(fake), subject="c-step")
    assert res.ok, res.reason
    assert res.outputs["reception"]["answer"]["step"] == "consult"
    offered = fake.tools[0][1]
    assert "book" not in offered and "change_booking" not in offered and "find_times" not in offered
    assert "put" in offered and "price_quote" in offered


def test_a_booking_in_the_chat_writes_every_record(proj, salon, project_dir):
    c = Chat(salon.ROOT, "c-book")
    ready_booking(c, salon, agree=False)
    fake = FakeLLM({"hana": [call("put", rows(agree="네 좋아요"), "p1"), call("book", {}, "b1"),
                             say("담당 민호 실장님이 확인하신 뒤 예약 확정 문자를 보내 드릴게요.")]})
    res = run_ask(proj, "reception", "네 좋아요", adapters=adapters(fake), subject="c-book")
    assert res.ok, res.reason
    assert "book" in fake.tools[0][1]                          # the question started in the booking step
    booked = _tool_rows(res.run_dir, "book")[0]["result"]
    assert booked["booked"] is True and booked["status"] == "pending"
    b = next(f for f in owner_rows(project_dir, "bookings") if f["booking"] == booked["booking"])
    assert b["status"] == "pending" and b["name"] == "윤서연" and b["designer"] == "minho"
    assert "애쉬 브라운" in b["answers"]
    rec = salon.records(c.rows("consult"))
    assert rec["purpose_booking"]["state"] == "done"           # the program marked it, not the worker
    assert rec["agree"]["words"]                               # the answers stay until the chat ends
    cust = [r["fields"] for r in c.rows("customers")]
    assert cust and "탈색은 안 했어요" in cust[0]["hair_note"]
    notice = fake.calls[-1][1][0]["content"]                     # the consult step after the booking
    assert b["booking"] in notice and "pending" in notice       # the customer's own booking, as it is now
    assert res.outputs["reception"]["answer"]["step"] == "consult"   # after the booking: anything else?


def test_book_refuses_before_the_agreement_and_names_what_is_missing(salon):
    c = Chat(salon.ROOT)
    ready_booking(c, salon, agree=False)
    res = c.tool("book")
    assert "error" in res and "agree" in res["error"]
    c2 = Chat(salon.ROOT)
    c2.put(purpose_booking=("커트", "open"), service="cut")
    res = c2.tool("book")
    for item in ("name", "phone", "style", "wish_time", "cut_bangs"):
        assert item in res["error"]


def _booking_words(project_dir) -> list[str]:
    """Values of every booking that would show that a booking exists: ids, names, phones."""
    return [x for f in owner_rows(project_dir, "bookings") for x in (f["booking"], f["name"], f["phone"])]


def _says_nothing_of_bookings(project_dir, value) -> None:
    text = json.dumps(value, ensure_ascii=False)
    assert not [w for w in _booking_words(project_dir) if w in text], text


def test_a_lookup_before_the_identity_check_says_nothing(salon, project_dir):
    c = Chat(salon.ROOT)
    c.put(purpose_my_booking=("제 예약 확인", "open"))
    _says_nothing_of_bookings(project_dir, c.tool("verify_customer"))          # no name and phone yet
    _says_nothing_of_bookings(project_dir, c.tool("change_booking"))
    seeded = next(f for f in owner_rows(project_dir, "bookings") if f["name"] == SEEDED["name"])
    moved = c.tool("find_times", {"booking": seeded["booking"]})
    assert "error" in moved and "days" not in moved                            # someone else's id: no minutes, no slot
    _says_nothing_of_bookings(project_dir, c.nav())


def test_identity_check_wrong_phone_reveals_nothing(salon, project_dir):
    c = Chat(salon.ROOT)
    c.put(purpose_my_booking=("제 예약 확인", "open"), name=SEEDED["name"], phone="010-9999-9999")
    res = c.tool("verify_customer")
    assert res == {"verified": False, "note": "no booking has this name and phone"}
    got = c.nav()
    assert got["step"] == "manage" and salon.text("verify_failed") in got["notice"]
    assert "jisu" not in got["notice"] and "지수" not in got["notice"]
    _says_nothing_of_bookings(project_dir, {"tool": res, "notice": got})


def test_a_verified_customer_sees_only_their_own_bookings(salon, project_dir):
    every = owner_rows(project_dir, "bookings")
    mine = [f for f in every if f["name"] == SEEDED["name"]]
    others = [f for f in every if f["name"] != SEEDED["name"]]
    assert mine and others
    c = Chat(salon.ROOT)
    c.put(purpose_my_booking=("제 예약 확인", "open"), name=SEEDED["name"], phone=SEEDED["phone"])
    res, got = c.tool("verify_customer"), c.nav()
    seen = json.dumps({"tool": res, "notice": got}, ensure_ascii=False)
    assert all(b["booking"] in seen for b in mine)
    assert not [w for f in others for w in (f["booking"], f["name"], f["phone"]) if w in seen]


def test_a_taken_time_says_whose_designer_never_whose_booking(salon, project_dir):
    taken = next(f for f in owner_rows(project_dir, "bookings") if f["designer"] == "minho")
    c = Chat(salon.ROOT)
    c.put(purpose_booking=("염색 예약", "open"), service="color", style={"style": "전체 염색", "words": "전체 염색이요"}, name="윤서연",
          phone="010-0000-7777", wish_time=f"{taken['date']} {taken['time']}", designer="minho", agree="네", **COLOR)
    res, got = c.tool("book"), c.nav()
    assert "error" in res and "다른 예약이 있습니다" in res["error"]
    for value in (res, got, c.tool("find_times", {"styles": ["전체 염색"], "designer": "minho"})):
        text = json.dumps(value, ensure_ascii=False)
        assert taken["name"] not in text and taken["phone"] not in text and taken["booking"] not in text


def test_the_model_never_gets_bookings(proj, salon):
    fake = FakeLLM({"hana": [say("무엇을 도와드릴까요?")]})
    res = run_ask(proj, "reception", "안녕하세요", adapters=adapters(fake), subject="c-model")
    assert res.ok, res.reason
    sent = json.dumps(fake.calls[0][1], ensure_ascii=False)
    assert "fs://bookings" not in sent and SEEDED["phone"] not in sent and SEEDED["name"] not in sent
    assert proj.file_servers["bookings"].type_tools("reception") == {"booking": []}   # no common tool on bookings


def test_identity_check_finds_the_booking_from_another_browser(salon):
    c = Chat(salon.ROOT, "c-other-browser")                    # not the subject the booking was made with
    c.put(purpose_my_booking=("제 예약 확인", "open"), name="김 하늘", phone="01000001001")
    res = c.tool("verify_customer")
    assert res["verified"] is True and len(res["bookings"]) == 1 and "지수 원장" in res["bookings"][0]
    got = c.nav()
    assert salon.text("verified", lines="") in got["notice"] and salon.text("my_booking_now") in got["notice"]
    c.put(phone="010-0000-1002")                               # the phone changes after the check
    got = c.nav()
    assert salon.text("verify_failed") in got["notice"] and "지수 원장" not in got["notice"]


def test_change_is_refused_before_verification_and_for_another_customers_booking(salon, project_dir):
    seeded = next(f for f in owner_rows(project_dir, "bookings") if f["name"] == SEEDED["name"])
    other = next(f for f in owner_rows(project_dir, "bookings") if f["name"] != SEEDED["name"])
    c = Chat(salon.ROOT)
    c.put(purpose_change=("예약 취소할게요", "open"), name=SEEDED["name"], phone="010-1111-2222",
          change_booking=seeded["booking"], change_action="cancel")
    res = c.tool("change_booking")
    assert "error" in res and "identity check failed" in res["error"]
    c.put(phone=SEEDED["phone"], change_booking=other["booking"])        # verified, but not this customer's booking
    res = c.tool("change_booking")
    assert "error" in res and "change_booking" in res["error"]
    assert next(f for f in owner_rows(project_dir, "bookings") if f["booking"] == other["booking"])["status"] == "confirmed"


def test_cancel_frees_the_slot_and_marks_the_purpose_done(salon, project_dir):
    seeded = next(f for f in owner_rows(project_dir, "bookings") if f["name"] == SEEDED["name"])
    c = Chat(salon.ROOT)
    c.put(purpose_change=("예약 취소", "open"), name=SEEDED["name"], phone=SEEDED["phone"])
    c.tool("verify_customer")
    c.put(change_booking=seeded["booking"], change_action="cancel", cancel_reason="일정이 생겼어요")
    got = c.nav()
    assert "cancel_agree" in got["notice"] and salon.text("change_now") not in got["notice"]
    refused = c.tool("change_booking")
    assert "error" in refused and "cancel_agree" in refused["error"]           # not without the customer's yes
    c.put(cancel_agree="네 취소해 주세요")
    assert salon.text("change_now") in c.nav()["notice"]
    res = c.tool("change_booking")
    assert res["changed"] is True and res["status"] == "cancelled", res
    assert next(f for f in owner_rows(project_dir, "bookings") if f["booking"] == seeded["booking"])["status"] == "cancelled"
    day = datetime.date.fromisoformat(seeded["date"])
    sched = [r["fields"] for r in c.rows("bookings")]
    assert seeded["time"] in salon.free_starts(sched, "jisu", day, 40)
    assert len([f for f in sched if f["booking"] == seeded["booking"]]) == 1   # the same row, its status cancelled
    rec = salon.records(c.rows("consult"))
    assert rec["purpose_change"]["state"] == "done"
    assert (salon.data_dir() / "memos" / f"{seeded['booking']}.change.md").exists()


def test_change_time_goes_back_to_pending(salon, project_dir):
    seeded = next(f for f in owner_rows(project_dir, "bookings") if f["name"] == SEEDED["name"])
    c = Chat(salon.ROOT)
    c.put(purpose_change=("시간 바꿀게요", "open"), name=SEEDED["name"], phone=SEEDED["phone"])
    c.tool("verify_customer")
    times = c.tool("find_times", {"booking": seeded["booking"], "designer": "jisu"})
    day = next(d for d in times["days"] if isinstance(d["free"], dict))
    new = f"{day['day'][:10]} {next(iter(day['free'].values()))[0]}"
    c.put(change_booking=seeded["booking"], change_action="change", change_time=new)
    assert salon.text("agree_open", agree_id="change_agree") in c.nav()["notice"]
    assert "error" in c.tool("change_booking")                 # no agreement yet
    c.put(change_agree="네 그 시간 좋아요")
    res = c.tool("change_booking")
    assert res["changed"] is True and res["status"] == "pending", res
    b = next(f for f in owner_rows(project_dir, "bookings") if f["booking"] == seeded["booking"])
    assert b["status"] == "pending" and f"{b['date']} {b['time']}" == new


class MiniSMTP(socketserver.StreamRequestHandler):
    """Just enough SMTP (EHLO, AUTH PLAIN, MAIL, RCPT, DATA, QUIT) to receive mail."""
    mails = []

    def handle(self):
        w = lambda s: self.wfile.write(s.encode() + b"\r\n")
        w("220 test ready")
        to = []
        while line := self.rfile.readline().decode("utf-8", "replace").rstrip("\r\n"):
            cmd = line.upper()
            if cmd.startswith("EHLO"):
                self.wfile.write(b"250-test\r\n250 AUTH PLAIN\r\n")
            elif cmd.startswith("AUTH"):
                w("235 ok")
            elif cmd.startswith("RCPT"):
                to.append(line.split(":", 1)[1].strip(" <>"))
                w("250 ok")
            elif cmd == "DATA":
                w("354 go")
                lines = []
                while (l := self.rfile.readline().decode("utf-8", "replace").rstrip("\r\n")) != ".":
                    lines.append(l)
                MiniSMTP.mails.append((to, "\n".join(lines)))
                w("250 queued")
            elif cmd == "QUIT":
                w("221 bye")
                return
            else:
                w("250 ok")


@pytest.fixture()
def smtp_server(monkeypatch):
    MiniSMTP.mails.clear()
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), MiniSMTP)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    for k, v in {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(server.server_address[1]), "SMTP_USER": "salon@example.com",
                 "SMTP_PASS": "pw", "OFFICE_EMAIL": "office@example.com", "MAIL_TEST_MODE": "1"}.items():
        monkeypatch.setenv(k, v)
    yield MiniSMTP.mails
    server.shutdown()
    server.server_close()


def test_summary_worker_and_the_designers_mail(proj, salon, project_dir, smtp_server):
    c = Chat(salon.ROOT, "c-notes")
    ready_booking(c, salon)
    booked = c.tool("book")
    assert booked["booked"], booked
    summary = {"text": "윤서연 님이 민호 실장님께 애쉬 브라운 염색을 예약했습니다.", "wishes": ["애쉬 브라운, 밝게"]}
    fake = FakeLLM({"nuri": [save(summary=summary)],
                    "duri": [save(prep={"ready": ["애쉬 브라운 약제"], "ask_first": ["원하는 밝기"], "care": []})]})
    transcript = [{"role": "user", "content": "애쉬 브라운으로 염색하고 싶어요"}, {"role": "assistant", "content": "네"}]
    res = run_flow(proj, "booking_notes", {"transcript": transcript, "booking": booked["booking"]}, adapters=adapters(fake))
    assert res.ok, res.reason
    assert res.outputs["nuri"]["summary"] == summary
    seen = json.dumps(fake.calls[0][1], ensure_ascii=False)
    assert "애쉬 브라운" in seen and "transcript" in seen      # the summary worker reads the chat and the booking
    memo = (salon.data_dir() / "memos" / f"{booked['booking']}.memo.md").read_text(encoding="utf-8")
    assert summary["text"] in memo and "/approve/" in memo and "애쉬 브라운 약제" in memo
    assert len(smtp_server) == 1


def test_the_designer_approves_once(salon, project_dir):
    from functions._approval import decide, links
    c = Chat(salon.ROOT)
    ready_booking(c, salon)
    bid = c.tool("book")["booking"]
    token = links(bid)[0].split("t=")[1]
    assert decide(bid, True, "wrong")[0] == "refused"
    code, msg = decide(bid, True, token, project=str(project_dir))
    assert code == "ok" and "확정" in msg
    assert next(f for f in owner_rows(project_dir, "bookings") if f["booking"] == bid)["status"] == "confirmed"
    assert list((salon.data_dir() / "outbox").glob("sms_*.txt"))
    assert decide(bid, False, token, project=str(project_dir))[0] == "done"     # a second click changes nothing


def test_the_end_of_the_chat_deletes_only_this_chats_rows(salon):
    a, b = Chat(salon.ROOT), Chat(salon.ROOT)
    a.put(purpose_my_booking=("확인", "open"), name=SEEDED["name"], phone=SEEDED["phone"])
    a.tool("verify_customer")
    b.put(purpose_info=("주차", "open"))
    res = run_flow(__import__("nextop.core.load", fromlist=["load_project"]).load_project(str(salon.ROOT)),
                   "chat_end", {"_subject": a.subject})
    assert res.ok, res.reason
    assert not a.rows("consult")
    assert b.rows("consult")


def test_the_worker_modes(proj):
    assert proj.workers["reception"].mode == "ask" and proj.workers["summarizer"].mode == "task"


def test_after_a_cancel_in_the_chat_the_notice_says_what_was_just_done(proj, salon, project_dir):
    seeded = next(f for f in owner_rows(project_dir, "bookings") if f["name"] == SEEDED["name"])
    c = Chat(salon.ROOT, "c-cancel-chat")
    c.put(purpose_change=("예약 취소", "open"), name=SEEDED["name"], phone=SEEDED["phone"])
    c.tool("verify_customer")
    c.put(change_booking=seeded["booking"], change_action="cancel")
    c.put(cancel_agree="네")
    fake = FakeLLM({"hana": [call("change_booking", {}, "x1"), say("취소해 드렸어요.")]})
    res = run_ask(proj, "reception", "네 취소해 주세요", adapters=adapters(fake), subject="c-cancel-chat")
    assert res.ok, res.reason
    assert "change_booking" in fake.tools[0][1]                  # the question started in the manage step
    last_system = fake.calls[-1][1][0]["content"]                 # the consult step after the switch
    assert "방금 예약 변경이나 취소(purpose_change)을 처리했습니다" in last_system
    assert "cancelled" in last_system and seeded["booking"] in last_system
    assert res.outputs["reception"]["answer"]["step"] == "consult"
