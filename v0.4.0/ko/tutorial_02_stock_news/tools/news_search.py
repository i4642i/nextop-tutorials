"""Web news search for one company (Tavily). Saves each new article as a file and lists them."""
import hashlib
import json
import pathlib

from functions import _news

NAME = "news_search"
DESC = ("Search recent news about one company. Each article that is not stored yet is saved as a file (title, date, "
        "page address, text) and returned with its file name, title, date and address; upload the ones that are really "
        "about the company with the file server's upload tool (tags: the company name). Articles already stored or "
        "already returned in this run are left out and only counted in skipped_known. One call is one paid search: "
        "call it once per company.")
GROUP = "news"
SCHEMA = {
    "type": "object",
    "properties": {"company": {"type": "string", "enum": [c["name"] for c in _news.stocks()["companies"]]}},
    "required": ["company"],
}
TIMEOUT = 60


def run(ctx, args):
    cfg = _news.stocks()
    company = next(c for c in cfg["companies"] if c["name"] == args["company"])
    folder = pathlib.Path(ctx["files_dir"])
    folder.mkdir(parents=True, exist_ok=True)
    offered_path = folder / "offered_urls.json"
    offered = set(json.loads(offered_path.read_text(encoding="utf-8"))) if offered_path.exists() else set()
    known = {_news.clean_url(u) for u in ctx["file_servers"]["news"].sources()} | offered     # what the news file server holds
    try:
        search = cfg["search"]
        hits = _news.tavily_search(company["query"], search["days"], search["max_results"], search.get("exclude_domains"))
    except ValueError as e:                        # a setting is missing: calling again cannot help
        _news.note_search(company["name"], str(e))
        return {"error": f"{e}. 다시 불러도 소용없습니다. 검색을 하지 못한 것이지 기사가 없는 것이 아닙니다."}
    except OSError as e:                           # the service could not be asked: not the same as "no articles"
        _news.note_search(company["name"], str(e))
        return {"error": f"{e}. 한 번만 다시 불러 보세요. 또 실패하면 검색을 하지 못했다고 note에 이유를 쓰세요(기사가 없다는 뜻이 아닙니다)."}
    _news.note_search(company["name"])             # the service answered (even with zero articles)
    articles, skipped = [], 0
    for h in hits:
        url = _news.clean_url(h["url"])
        if not url or not h["content"].strip() or _news.blocked(url, cfg["search"].get("exclude_domains", [])):
            continue
        if url in known:
            skipped += 1
            continue
        known.add(url)
        offered.add(url)
        title = _news.clean_title(h["title"])
        path = folder / f"{hashlib.sha1(url.encode()).hexdigest()[:10]}.md"
        path.write_text(_news.article_text(title, h["published_date"], url, h["content"]), encoding="utf-8")
        articles.append({"file": path.name, "title": title, "date": h["published_date"], "source": url})   # a short name: upload finds it in this block's files
    offered_path.write_text(json.dumps(sorted(offered)), encoding="utf-8")
    return {"company": company["name"], "articles": articles, "skipped_known": skipped}
