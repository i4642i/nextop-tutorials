"""Shared helpers: the company list, settings (.env), web search (Tavily) and mail (SMTP).

Settings come from the environment or .env. Nothing here prints a key. Search and mail return (ok, note)
style results or raise OSError, so the caller can tell the worker or the operator what went wrong.
"""
import datetime
import json
import os
import pathlib
import re
import smtplib
import ssl
import urllib.error
import urllib.request
from email.message import EmailMessage

from nextop.adapters.openai_compat import read_env

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEEKDAY = "월화수목금토일"
TAVILY_URL = "https://api.tavily.com/search"
MISSING_KEY = "TAVILY_API_KEY 가 없습니다. 프로젝트 폴더의 .env 에 TAVILY_API_KEY=... 를 넣어 주세요 (https://tavily.com)"
MAIL_KEYS = ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS")


def setting(name: str, default: str = "") -> str:
    env = ROOT / ".env"
    return os.environ.get(name) or (read_env(env) if env.exists() else {}).get(name) or default


PROBLEMS_FILE = "search_problems.json"


def search_problems() -> list[dict]:
    """Companies whose search could not be asked in this run: [{company, problem}]. Written by the search tool, cleared
    at the start of a run, read at the end (a failed search must never look like "no news")."""
    path = data_dir() / PROBLEMS_FILE
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else []


def note_search(company: str, problem: str = "") -> None:
    """Record that the search for `company` failed (problem), or, with no problem, that it worked now."""
    rows = [r for r in search_problems() if r["company"] != company]
    if problem:
        rows.append({"company": company, "problem": problem})
    (data_dir() / PROBLEMS_FILE).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def stocks() -> dict:
    return json.loads((ROOT / "stocks.json").read_text(encoding="utf-8"))


def data_dir() -> pathlib.Path:
    """Where outlooks/ is written (NEWS_DATA_DIR lets tests use a private folder)."""
    return pathlib.Path(os.environ.get("NEWS_DATA_DIR") or ROOT)


def next_trading_day(today: datetime.date) -> datetime.date:
    """Tomorrow, or Monday when tomorrow is a weekend. Public holidays are not known here."""
    day = today + datetime.timedelta(days=1)
    while day.weekday() >= 5:
        day += datetime.timedelta(days=1)
    return day


def day_label(day: datetime.date) -> str:
    return f"{day.isoformat()} ({WEEKDAY[day.weekday()]})"


# ---- web search -------------------------------------------------------------------------------------------------

def tavily_search(query: str, days: int, max_results: int, exclude_domains: list[str] | None = None) -> list[dict]:
    """One Tavily news search. Returns [{title, url, content, published_date}]. Costs one search credit.

    An empty list means Tavily answered and found no article (a real result). When Tavily could not be asked, this
    raises: ValueError for a missing key (a setting), OSError for an HTTP error, a timeout or an unusable answer."""
    key = setting("TAVILY_API_KEY")
    if not key:
        raise ValueError(MISSING_KEY)
    body = json.dumps({"query": query, "topic": "news", "days": days, "max_results": max_results,
                       "search_depth": "basic", "include_answer": False,
                       "exclude_domains": exclude_domains or []}).encode()
    req = urllib.request.Request(setting("TAVILY_URL", TAVILY_URL), body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise OSError(f"Tavily 뉴스 검색이 HTTP {e.code} {e.reason} 로 답했습니다 (키가 틀렸거나 한도를 넘었을 수 있습니다)") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise OSError(f"Tavily 뉴스 검색에 연결하지 못했습니다 ({getattr(e, 'reason', e)})") from e
    except ValueError as e:
        raise OSError(f"Tavily 뉴스 검색의 답을 읽을 수 없습니다 ({e})") from e
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise OSError("Tavily 뉴스 검색의 답에 results 목록이 없습니다")
    return [{"title": r.get("title") or "", "url": r.get("url") or "", "content": r.get("content") or "",
             "published_date": day_of(r.get("published_date") or "")} for r in data["results"]]


def day_of(text: str) -> str:
    """'Mon, 23 Nov 2026 06:38:47 GMT' or '2026-11-23T06:38:47Z' -> '2026-11-23'; anything else stays as it is."""
    from email.utils import parsedate_to_datetime
    text = text.strip()
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError):
        return text[:10] if len(text) >= 10 and text[4] == "-" and text[7] == "-" else text


# ---- mail -------------------------------------------------------------------------------------------------------

def recipients() -> str:
    """Test mode (MAIL_TEST_MODE=1): everything goes to OFFICE_EMAIL. Otherwise to MAIL_TO."""
    if setting("MAIL_TEST_MODE", "1") == "1":
        return setting("OFFICE_EMAIL")
    return setting("MAIL_TO")


def mail_problems() -> list[str]:
    """What is missing for sending mail, one sentence per gap; an empty list means mail can be sent."""
    out = [f"{k} 가 비어 있습니다. .env 에 {k}=... 를 넣어 주세요." for k in MAIL_KEYS if not setting(k)]
    if not recipients():
        name = "OFFICE_EMAIL" if setting("MAIL_TEST_MODE", "1") == "1" else "MAIL_TO"
        out.append(f"받는 사람이 없습니다. .env 에 {name}=... 를 넣어 주세요.")
    return out


def setup_problems() -> list[str]:
    """Everything this tutorial needs from .env before it can do its job (search key and mail)."""
    return ([MISSING_KEY] if not setting("TAVILY_API_KEY") else []) + mail_problems()


def send_mail(to: str, subject: str, text: str, html: str = "") -> tuple[bool, str]:
    """Send one mail: plain text, plus an HTML version when given."""
    cfg = {k: setting(k) for k in MAIL_KEYS}
    problems = mail_problems()
    if not to or problems:
        return False, "메일 설정이 비어 있습니다: " + " ".join(problems)
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg["SMTP_USER"], to
    msg.set_content(text, cte="base64")                 # base64: safe for any mail server
    if html:
        msg.add_alternative(html, subtype="html", cte="base64")
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
        return False, f"SMTP 서버 {cfg['SMTP_HOST']}:{cfg['SMTP_PORT']} 에서 메일을 보내지 못했습니다 ({type(e).__name__}: {e})"


# ---- articles ---------------------------------------------------------------------------------------------------

def blocked(url: str, domains: list[str]) -> bool:
    """True for a page of a site that is not news (social media): its own domain or any sub-domain."""
    host = (url.split("//", 1)[-1].split("/", 1)[0].split("?", 1)[0]).lower()
    return any(host == d or host.endswith("." + d) for d in domains)


def clean_title(title: str) -> str:
    """A search result title as people read it: HTML comments and tags dropped, spaces folded (some sites leave
    markup such as <!-- --> in their titles)."""
    title = re.sub(r"<!--.*?-->", "", title or "", flags=re.S)
    title = re.sub(r"<[^>]+>", "", title)
    return " ".join(title.split())


def clean_url(url: str) -> str:
    """The same page under another spelling (tracking parameters, #fragment, trailing slash) is one address."""
    from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
    p = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urlunsplit((p.scheme.lower(), p.netloc.lower(), p.path.rstrip("/"), urlencode(query), ""))


def article_text(title: str, date: str, url: str, content: str) -> str:
    """The file a collected article becomes. The program writes it, so the address line is always exact."""
    return f"# {title.strip()}\n\n날짜: {date or '알 수 없음'}\n주소: {url}\n\n{content.strip()}\n"


def article_parts(text: str) -> dict:
    """title, date and url back out of article_text()."""
    out = {"title": "", "date": "", "url": ""}
    for line in text.splitlines():
        if line.startswith("# ") and not out["title"]:
            out["title"] = line[2:].strip()
        elif line.startswith("날짜: "):
            out["date"] = line[4:].strip()
        elif line.startswith("주소: "):
            out["url"] = line[4:].strip()
    return out
