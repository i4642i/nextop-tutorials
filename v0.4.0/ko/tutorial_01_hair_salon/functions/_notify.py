"""Messages out of the salon: text messages (SMS) to the customer and e-mail to the designer.

Settings come from the environment or .env. SMS has a provider slot: SMS_MODE=outbox (default) writes the message to
outbox/sms_<time>.txt; SMS_MODE=solapi sends it through Solapi. To use another provider (NHN Cloud, ...) add a
function to PROVIDERS. Nothing here raises for a failed send: it returns (ok, note) and the flow goes on.
"""
import datetime
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import ssl
import urllib.request
from email.message import EmailMessage

from nextop.adapters.openai_compat import read_env

from functions._salon import ROOT, data_dir, salon


def setting(name: str, default: str = "") -> str:
    env = ROOT / ".env"
    return os.environ.get(name) or (read_env(env) if env.exists() else {}).get(name) or default


# ---- SMS -------------------------------------------------------------------------------------------------------

def sms_outbox(to: str, text: str) -> str:
    """Default mode: no provider, the message is written to a file so you can see what would have been sent."""
    folder = data_dir() / "outbox"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"sms_{datetime.datetime.now():%Y%m%d-%H%M%S-%f}.txt"
    path.write_text(f"to: {to}\n\n{text}\n", encoding="utf-8")
    return f"written to {path.name}"


def sms_solapi(to: str, text: str) -> str:
    """Solapi REST API (https://developers.solapi.com), HMAC-SHA256 signed. Not tested against the live service."""
    key, secret, sender = (setting(k) for k in ("SOLAPI_API_KEY", "SOLAPI_API_SECRET", "SOLAPI_SENDER"))
    if not (key and secret and sender):
        raise ValueError("SOLAPI_API_KEY, SOLAPI_API_SECRET and SOLAPI_SENDER must be set in .env")
    date, salt = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), secrets.token_hex(16)
    sign = hmac.new(secret.encode(), (date + salt).encode(), hashlib.sha256).hexdigest()
    body = json.dumps({"message": {"to": to.replace("-", ""), "from": sender, "text": text}}).encode()
    req = urllib.request.Request(
        "https://api.solapi.com/messages/v4/send", body, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"HMAC-SHA256 apiKey={key}, date={date}, salt={salt}, signature={sign}"})
    with urllib.request.urlopen(req, timeout=20) as res:
        return f"solapi answered {res.status}"


PROVIDERS = {"outbox": sms_outbox, "solapi": sms_solapi}      # add "nhn": your_function here


def send_sms(to: str, text: str) -> tuple[bool, str]:
    mode = setting("SMS_MODE", "outbox")
    if mode not in PROVIDERS:
        return False, f"SMS_MODE {mode!r} is unknown; use one of {', '.join(PROVIDERS)}"
    try:
        return True, PROVIDERS[mode](to, text)
    except (OSError, ValueError) as e:
        return False, f"{mode}: {type(e).__name__}: {e}"


# ---- mail ------------------------------------------------------------------------------------------------------

def designer_address(designer: str) -> str:
    """The designer's own address; in test mode (MAIL_TEST_MODE=1) every mail goes to OFFICE_EMAIL instead."""
    if setting("MAIL_TEST_MODE", "1") == "1":
        return setting("OFFICE_EMAIL")
    return salon()["designers"][designer]["email"]


def send_mail(to: str, subject: str, body: str, attachments: list[tuple[str, str]] | None = None) -> tuple[bool, str]:
    """Send one mail. attachments: [(file name, text)], attached as UTF-8 text files."""
    cfg = {k: setting(k) for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS")}
    if not to or not all(cfg.values()):
        return False, "mail is not set up: fill SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS and OFFICE_EMAIL in .env"
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["SMTP_USER"], to
    msg.set_content(body)
    for name, text in attachments or []:
        msg.add_attachment(text, subtype="plain", charset="utf-8", cte="base64", filename=name)  # base64: safe for any mail server
    try:
        port = int(cfg["SMTP_PORT"])
        if port == 465:
            smtp = smtplib.SMTP_SSL(cfg["SMTP_HOST"], port, context=ssl.create_default_context(), timeout=20)
        else:
            smtp = smtplib.SMTP(cfg["SMTP_HOST"], port, timeout=20)
            if port == 587:                       # any other port: no encryption (a local test server only)
                smtp.starttls(context=ssl.create_default_context())
        with smtp:
            smtp.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
            smtp.send_message(msg)
        return True, "sent"
    except (OSError, smtplib.SMTPException, ValueError) as e:
        return False, f"{type(e).__name__}: {e}"
