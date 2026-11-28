"""Test setup: make the project importable, pick a nextop that has everything the tutorial uses, offer a scripted LLM.

The tests never call a real model or the real search. FakeLLM answers from a script per worker, and the web search
is replaced by a fixed list of articles. Everything the program does (dedupe, tags, quote check, mail) runs for real,
against a temporary copy of the project.
"""
import json
import os
import pathlib
import re
import shutil
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")

try:
    import nextop.file_server.typed  # noqa: F401  (file servers with type folders: nextop 0.4.0)
except Exception:                      # an older nextop: use the platform checkout for development
    src = os.environ.get("NEXTOP_SRC", "")
    if not (pathlib.Path(src) / "nextop" / "file_server" / "typed.py").exists():
        pytest.skip("this nextop has no file servers with type folders (0.4.0); install a newer nextop or set NEXTOP_SRC",
                    allow_module_level=True)
    for name in [m for m in sys.modules if m == "nextop" or m.startswith("nextop.")]:
        del sys.modules[name]
    sys.path.insert(0, src)
    os.environ["PYTHONPATH"] = src + os.pathsep + os.environ["PYTHONPATH"]

from nextop.adapters import Reply, ToolCall  # noqa: E402
from nextop.core.load import load_project  # noqa: E402

COLLECTOR, ANALYST = "뉴스 수집 담당", "주가 전망 담당"


class FakeLLM:
    """Scripted replies per worker: script = {"collector": [step, ...], "analyst": [...]}; a step is a Reply or f(messages)."""

    def __init__(self, script):
        self.script = {k: list(v) for k, v in script.items()}
        self.calls = []                      # (worker, messages) of every request, for assertions

    def chat(self, model, messages, tools=None):
        who = "collector" if COLLECTOR in messages[0]["content"] else "analyst"
        self.calls.append((who, messages))
        step = self.script[who].pop(0)
        return step(messages) if callable(step) else step

    def supports(self, model, feature):
        return False


def call(name, args, call_id="c1"):
    return Reply(tool_calls=[ToolCall(id=call_id, name=name, arguments=args)])


def save(**outputs):
    return call("save_output", outputs)


def adapters(fake):
    """The scripted model. The run adds the file server's default index (bm25) by itself."""
    return {"llm": {"default": fake}}


def text_of(messages):
    return "\n".join(m["content"] if isinstance(m["content"], str) else json.dumps(m["content"], ensure_ascii=False)
                     for m in messages)


def last_tool_json(messages):
    """The newest tool result, as a dict."""
    for m in reversed(messages):
        if m["role"] == "tool":
            return json.loads(m["content"]) if isinstance(m["content"], str) else m["content"]
    raise AssertionError("no tool result yet")


def addresses(messages):
    """The article addresses the worker was shown (its input cards and tool results; not the examples of its mission)."""
    shown = [m for m in messages if m["role"] != "system"]
    return list(dict.fromkeys(re.findall(r"fs://news/\d+", text_of(shown))))


ARTICLES = {                                    # query keyword -> what the fake search finds
    "삼성전자": [
        {"title": "삼성전자, HBM4 공급 확대", "url": "https://news.example.com/a/1?utm_source=x",
         "content": "삼성전자가 HBM4 공급을 확대한다고 밝혔다. 증권가는 4분기 영업이익이 늘 것으로 본다.", "published_date": "2026-11-24"},
        {"title": "삼성전자 파운드리 수주", "url": "https://news.example.com/a/2",
         "content": "삼성전자가 미국 고객사와 파운드리 계약을 맺었다. 계약 규모는 공개되지 않았다.", "published_date": "2026-11-23"},
        {"title": "삼성전자 HBM4 공급 확대 (재전송)", "url": "https://news.example.com/a/1/",
         "content": "같은 기사가 다른 주소 표기로 다시 왔다.", "published_date": "2026-11-24"},
    ],
    "SK하이닉스": [
        {"title": "SK하이닉스 HBM 점유율 1위 유지", "url": "https://news.example.com/b/1",
         "content": "SK하이닉스가 HBM 시장 점유율 1위를 지켰다. 다만 공급 과잉 우려가 남아 있다.", "published_date": "2026-11-24"},
        {"title": "SK하이닉스 설비 투자 확대", "url": "https://news.example.com/b/2",
         "content": "SK하이닉스는 내년 설비 투자를 늘린다. 비용 부담이 커질 수 있다는 분석이 있다.", "published_date": "2026-11-22"},
    ],
    "NVIDIA": [
        {"title": "NVIDIA shares slip before earnings", "url": "https://news.example.com/c/1",
         "content": "NVIDIA shares fell 2% ahead of earnings. Analysts warn that expectations are very high.", "published_date": "2026-11-24"},
        {"title": "NVIDIA unveils new AI chip", "url": "https://news.example.com/c/2",
         "content": "NVIDIA unveiled a new AI chip for data centers. Orders are said to be strong.", "published_date": "2026-11-23"},
    ],
    "SpaceX": [
        {"title": "SpaceX fan post", "url": "https://www.instagram.com/p/abc",
         "content": "SpaceX photos of the day. Follow for more.", "published_date": "2026-11-24"},
        {"title": "SpaceX Starship test flight set", "url": "https://news.example.com/d/1",
         "content": "SpaceX set the next Starship test flight for next week. The company says the vehicle is ready.", "published_date": "2026-11-24"},
    ],
}


@pytest.fixture(scope="session")
def project_dir(tmp_path_factory):
    """A private copy of the project (runs/ and the news store stay out of the real folder)."""
    dst = tmp_path_factory.mktemp("news") / "proj"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(
        "runs", "outlooks", "tests", "__pycache__", ".env", ".pytest_cache", "store"))
    (dst / ".env").write_text("MAIL_TEST_MODE=1\nLLM_API_KEY=test\nTAVILY_API_KEY=test\n", encoding="utf-8")
    return dst


class FakeTavily(BaseHTTPRequestHandler):
    """A local stand-in for the search service: answers from ARTICLES by the keyword in the query, counts searches."""
    searches = []
    fail = False

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeTavily.searches.append(body["query"])
        if FakeTavily.fail:
            self.send_response(500)
            self.end_headers()
            return
        results = next(([dict(i) for i in items] for k, items in ARTICLES.items() if k in body["query"]), [])
        data = json.dumps({"results": results}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture()
def news(project_dir, tmp_path, monkeypatch):
    """The project's helper module, a local fake search service, a fresh store and outlooks folder per test."""
    import importlib
    monkeypatch.syspath_prepend(str(project_dir))
    for name in [m for m in sys.modules if m in ("functions", "tools") or m.startswith(("functions.", "tools."))]:
        del sys.modules[name]
    FakeTavily.searches.clear()
    FakeTavily.fail = False
    server = ThreadingHTTPServer(("127.0.0.1", 0), FakeTavily)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    monkeypatch.setenv("TAVILY_URL", f"http://127.0.0.1:{server.server_address[1]}/search")
    monkeypatch.setenv("TAVILY_API_KEY", "test")
    monkeypatch.setenv("NEWS_DATA_DIR", str(tmp_path))
    mod = importlib.import_module("functions._news")
    mod.searches = FakeTavily.searches
    mod.server = FakeTavily
    store = project_dir / "file_servers" / "news" / "store"
    shutil.rmtree(store, ignore_errors=True)
    yield mod
    server.shutdown()
    server.server_close()
    shutil.rmtree(store, ignore_errors=True)


def views(proj, project_dir):
    """What a tool of the collector gets as ctx["file_servers"]: read-only views of the persistent file servers."""
    from nextop.file_server import FileServerRuntime
    runtime = FileServerRuntime(proj, {"llm": {}}, project_dir / "runs" / "view")
    return runtime.views_for("collector", "collector", "collector")


@pytest.fixture()
def proj(project_dir, news):
    return load_project(str(project_dir))
