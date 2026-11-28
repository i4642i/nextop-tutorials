"""The designer's answer to a booking: the signed approve / decline links of the designer's mail and the texts the
customer gets. The answer itself is written by the flow `decide` (functions/decide_booking.py): approve (confirmed,
the customer gets the confirmation text) or decline (the slot is free again, the customer gets a short text asking for
another time).

The links carry an HMAC token of the booking id, signed with APPROVE_SECRET from .env, so nobody can answer a booking
without the mail. The same code serves the chat server links and approve.py.
"""
import datetime
import hashlib
import hmac

from functions._notify import designer_address, send_mail, setting
from functions._salon import booking_line, data_dir, day_label, salon


def token(booking_id: str) -> str:
    secret = setting("APPROVE_SECRET")
    if not secret:
        raise ValueError("APPROVE_SECRET is not set in .env (any long random text)")
    return hmac.new(secret.encode(), booking_id.encode(), hashlib.sha256).hexdigest()[:32]


def token_ok(booking_id: str, given: str) -> bool:
    try:
        return hmac.compare_digest(token(booking_id), given or "")
    except ValueError:
        return False


def public_url() -> str:
    return setting("PUBLIC_URL", "http://127.0.0.1:8771").rstrip("/")


def links(booking_id: str) -> tuple[str, str]:
    """(approve link, decline link) for the designer's mail."""
    t, base = token(booking_id), public_url()
    return f"{base}/approve/{booking_id}?t={t}", f"{base}/decline/{booking_id}?t={t}"


def _day(b: dict) -> str:
    return day_label(datetime.date.fromisoformat(b["date"]))


def who(b: dict) -> str:
    return f"{b['name']} 様 {_day(b)} {b['time']}"


def confirmed_text(b: dict) -> str:
    return (f"【{salon()['name']}】ご予約が確定しました。\n{_day(b)} {b['time']} 担当 {b['designer_name']}\n"
            f"{'、'.join(b['service_labels'])}（{'、'.join(b['styles'])}）¥{int(b['price']):,}（税込）・"
            f"約{int(b['minutes'])}分\nご変更・キャンセルは前日までにお願いいたします。")


def declined_text(b: dict) -> str:
    return (f"【{salon()['name']}】申し訳ございません。{_day(b)} {b['time']} のご予約はお受けできませんでした。\n"
            "お手数ですが、別のお時間でもう一度ご予約ください。")


def tell_designer(old: dict, b: dict) -> str:
    """A booking was changed or cancelled (change_booking): mail the designer (for a change of designer the old one
    too) and keep the mail in memos/. A changed booking is pending again, so the mail has the approve / decline links;
    a cancelled one frees the slot. A mail that cannot be sent does not undo the change."""
    test = "[予約・テスト] " if setting("MAIL_TEST_MODE", "1") == "1" else ""
    if b["status"] == "cancelled":
        subject = f"{test}[予約キャンセル] {old['date']} {old['time']} {old['name']}"
        body = f"お客様が予約をキャンセルしました。その時間は空きに戻りました。\n\n- キャンセルされた予約: {booking_line(old)}\n"
    else:
        try:
            yes, no = links(b["booking"])
            answer = f"\n- 承認: {yes}\n- お断り: {no}\n"
        except ValueError as e:
            answer = f"\n（承認リンクを作れませんでした: {e}）\n"
        subject = f"{test}[予約変更の承認のお願い] {b['date']} {b['time']} {b['name']}"
        body = (f"お客様が予約を変更しました。承認すると、お客様に確定のショートメッセージが届きます。\n\n"
                f"- 変更前: {booking_line(old)}\n- 変更後: {booking_line(b)}\n{answer}")
    folder = data_dir() / "memos"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{b['booking']}.change.md").write_text(f"# {subject}\n\n{body}", encoding="utf-8")
    to = sorted({x for x in (designer_address(old["designer"]), designer_address(b["designer"])) if x})
    return "; ".join(send_mail(t, subject, body)[1] for t in to) or "mail is not set up (no address)"


def decide(booking_id: str, approve: bool, given_token: str | None = None, check_token: bool = True,
           project: str | None = None) -> tuple[str, str]:
    """Answer a booking through the flow `decide`. Returns (code, a Japanese sentence for the designer): code "ok",
    "done" (already answered, nothing changed) or "refused" (wrong token or no such booking, nothing changed)."""
    if check_token and not token_ok(booking_id, given_token or ""):
        return "refused", "リンクが正しくありません。メールのリンクをそのまま押してください。"
    from nextop.core.load import load_project
    from nextop.runtime.flow import run_flow
    from functions._salon import ROOT
    res = run_flow(load_project(str(project or ROOT)), "decide", {"booking": booking_id, "approve": bool(approve)})
    if not res.ok:
        return "refused", f"処理できませんでした: {res.reason}"
    d = res.outputs["decide_booking"]["decision"]
    return d["code"], d["message"]
