"""Web news search for one company (Tavily). Saves each new article as a file and lists them."""
import hashlib
import json
import pathlib

from functions import _news

NAME = "news_search"
DESC = ("一社の最近のニュースを検索します。まだ保存されていない記事はファイル（タイトル、日付、ページのアドレス、本文）として"
        "保存され、そのファイル名、タイトル、日付、アドレスが返ります。本当にその会社についての記事だけを、ファイルサーバーの"
        "アップロードツールで上げてください（タグ: 会社名）。すでに保存されている記事やこの実行ですでに返した記事は外され、"
        "skipped_known に数だけが入ります。一回の呼び出しが有料の検索一回です。会社ごとに一回だけ呼んでください。")
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
        hits = _news.tavily_search(company["query"], search["days"], search["max_results"], search.get("exclude_domains"),
                                   search.get("include_domains"))
    except ValueError as e:                        # a setting is missing: calling again cannot help
        _news.note_search(company["name"], str(e))
        return {"error": f"{e}。もう一度呼んでも役に立ちません。検索ができなかったのであって、記事がないわけではありません。"}
    except OSError as e:                           # the service could not be asked: not the same as "no articles"
        _news.note_search(company["name"], str(e))
        return {"error": f"{e}。もう一度だけ呼んでください。また失敗したら、その会社の status は none にして、note にこの理由を書いてください（記事がないという意味ではありません）。"}
    _news.note_search(company["name"])             # the service answered (even with zero articles)
    articles, skipped = [], 0
    for h in hits:
        url = _news.clean_url(h["url"])
        if not url or not h["content"].strip() or _news.blocked(url, search.get("exclude_domains", []),
                                                                 search.get("include_domains")):
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
