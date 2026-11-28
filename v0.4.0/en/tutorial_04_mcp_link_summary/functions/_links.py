"""Shared helpers: settings (.env), the links of the run input, today in Seoul, the report folder and mail.

Plain program work (no model). Settings come from the environment or .env; nothing prints a key.
"""
import datetime
import os
import pathlib
import re
import smtplib
import ssl
from email.message import EmailMessage

from nextop.adapters.openai_compat import read_env

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"              # the only folder the filesystem MCP server may touch (project.json)
MAX_LINKS = 3
SEOUL = datetime.timezone(datetime.timedelta(hours=9), "Asia/Seoul")     # Korea has no daylight saving time
# Letters of Chinese, Japanese and Korean: a model sometimes slips them into English text
CJK = re.compile("[\u3040-\u30ff\u3131-\u318e\uac00-\ud7a3\u3400-\u4dbf\u4e00-\u9fff\uff66-\uff9f]")


def setting(name: str, default: str = "") -> str:
    env = ROOT / ".env"
    return os.environ.get(name) or (read_env(env) if env.exists() else {}).get(name) or default


def now_seoul() -> datetime.datetime:
    return datetime.datetime.now(SEOUL)


def today_seoul() -> str:
    return now_seoul().date().isoformat()


def parse_links(text: str) -> tuple[list[str], list[str]]:
    """The web addresses in the run input (one per line, or separated by spaces or commas) -> (links, problems)."""
    links, problems = [], []
    for word in re.split(r"[\s,]+", str(text or "").strip()):
        if not word:
            continue
        if not re.match(r"^https?://[^/\s]+", word):
            problems.append(f"not a web address (http:// or https://): {word}")
        elif word not in links:
            links.append(word)
    if not links and not problems:
        problems.append("give 1 to 3 web addresses, one per line")
    if len(links) > MAX_LINKS:
        problems.append(f"give at most {MAX_LINKS} web addresses; got {len(links)}")
    return links, problems


def cjk_errors(where: str, text: str) -> list[str]:
    found = sorted(set(CJK.findall(text or "")))
    return [f"{where} has Chinese, Japanese or Korean letters ({''.join(found)}); write it in English only"] if found else []


def recipients() -> str:
    """Test mode (MAIL_TEST_MODE=1): everything goes to OFFICE_EMAIL. Otherwise to MAIL_TO."""
    if setting("MAIL_TEST_MODE", "1") == "1":
        return setting("OFFICE_EMAIL")
    return setting("MAIL_TO")


MAIL_KEYS = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS")


def mail_problems() -> list[str]:
    """What is missing for sending mail, one sentence per gap; an empty list means mail can be sent."""
    out = [f"{k} is empty. Put {k}=... in .env." for k in MAIL_KEYS if not setting(k)]
    if not recipients():
        name = "OFFICE_EMAIL" if setting("MAIL_TEST_MODE", "1") == "1" else "MAIL_TO"
        out.append(f"There is no recipient. Put {name}=... in .env.")
    return out


def send_mail(to: str, subject: str, body: str, attachments: list[tuple[str, str]] | None = None) -> tuple[bool, str]:
    """Send one mail with a plain text body and text attachments [(file name, text)]. Returns (ok, note); never raises."""
    cfg = {k: setting(k) for k in MAIL_KEYS}
    problems = mail_problems()
    if not to or problems:
        return False, "Mail is not set up: " + " ".join(problems)
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["SMTP_USER"], to
    msg.set_content(body, cte="base64")                  # base64: safe for any mail server
    for name, text in attachments or []:
        msg.add_attachment(text, subtype="markdown", charset="utf-8", cte="base64", filename=name)
    try:
        port = int(cfg["SMTP_PORT"])
        if port == 465:
            smtp = smtplib.SMTP_SSL(cfg["SMTP_HOST"], port, context=ssl.create_default_context(), timeout=30)
        else:
            smtp = smtplib.SMTP(cfg["SMTP_HOST"], port, timeout=30)
            if port == 587:                       # any other port: no encryption (a local test server only)
                smtp.starttls(context=ssl.create_default_context())
        with smtp:
            smtp.login(cfg["SMTP_USER"], cfg["SMTP_PASS"])
            smtp.send_message(msg)
        return True, "sent"
    except (OSError, smtplib.SMTPException, ValueError) as e:
        return False, f"SMTP server {cfg['SMTP_HOST']}:{cfg['SMTP_PORT']} could not send the mail ({type(e).__name__}: {e})"
