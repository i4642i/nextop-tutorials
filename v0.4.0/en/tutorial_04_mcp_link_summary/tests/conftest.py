"""Test setup: make the project importable, pick a nextop that has MCP servers, offer a scripted LLM.

The tests never call a real model. The three MCP servers (fetch, time, filesystem) run for real, as project.json
starts them, against a temporary copy of the project. The web pages come from a small web server on this computer
(the copy lets the fetch server read local addresses with --allow-private-ips), and the mail goes to a mini mail
server on this computer. The first run needs the internet once, for uvx and npx to download the servers.
"""
import json
import os
import pathlib
import re
import shutil
import socketserver
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")

try:
    import nextop.mcp_servers  # noqa: F401  (MCP servers came with nextop 0.3.0)
except Exception:                      # an older nextop: use the platform checkout for development
    src = os.environ.get("NEXTOP_SRC", "")
    if not (pathlib.Path(src) / "nextop" / "mcp_servers.py").exists():
        pytest.skip("this nextop has no MCP servers; install nextop[mcp]>=0.3.0 or set NEXTOP_SRC",
                    allow_module_level=True)
    for name in [m for m in sys.modules if m == "nextop" or m.startswith("nextop.")]:
        del sys.modules[name]
    sys.path.insert(0, src)
    os.environ["PYTHONPATH"] = src + os.pathsep + os.environ["PYTHONPATH"]

from nextop.adapters import Reply, ToolCall  # noqa: E402
from nextop.core.load import load_project  # noqa: E402

READER, WRITER = "Reader", "Writer"


class FakeLLM:
    """Scripted replies per worker: script = {"reader": [step, ...], "writer": [...]}; a step is a Reply or f(messages)."""

    def __init__(self, script):
        self.script = {k: list(v) for k, v in script.items()}
        self.calls = []                      # (worker, messages) of every request, for assertions

    def chat(self, model, messages, tools=None):
        who = "reader" if READER in messages[0]["content"] else "writer"
        self.calls.append((who, messages))
        step = self.script[who].pop(0)
        return step(messages) if callable(step) else step

    def supports(self, model, feature):
        return False


def call(name, args, call_id="c1"):
    return Reply(tool_calls=[ToolCall(id=call_id, name=name, arguments=args)])


def save(**outputs):
    return call("save_output", outputs, "save")


def adapters(fake):
    return {"llm": {"default": fake}}


def text_of(messages):
    return "\n".join(m["content"] if isinstance(m["content"], str) else json.dumps(m["content"], ensure_ascii=False)
                     for m in messages)


def tool_results(messages):
    """Every tool result so far, as dicts, oldest first."""
    return [json.loads(m["content"]) if isinstance(m["content"], str) else m["content"]
            for m in messages if m["role"] == "tool"]


def report_file(messages):
    return re.search(r"links_\d{8}-\d{6}\.md", text_of(messages)).group(0)


PAGES = {
    "/mcp.html": ("<html><head><title>What is MCP</title></head><body><article><h1>What is MCP</h1>"
                  "<p>The Model Context Protocol is an open standard that connects AI applications to outside tools "
                  "and data. A server offers tools; a client such as an AI app calls them.</p>"
                  "<p>Servers talk over standard input and output or over HTTP.</p></article></body></html>"),
    "/coffee.html": ('<html><head><meta charset="utf-8"><title>How to brew pour-over coffee</title></head><body><article>'
                     "<h1>How to brew pour-over coffee</h1><p>Use 15 grams of coffee for 250 milliliters of water. "
                     "Water at 92 °C works best.</p>"
                     "<p>Let it bloom for the first 30 seconds, then pour the rest of the water in three rounds.</p></article></body></html>"),
}


class LocalPages(BaseHTTPRequestHandler):
    """The web pages the tests summarize (robots.txt is missing, so every page may be fetched)."""
    seen = []

    def do_GET(self):
        LocalPages.seen.append(self.path)
        page = PAGES.get(self.path)
        data = (page or "not found").encode("utf-8")
        self.send_response(200 if page else 404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def site():
    server = ThreadingHTTPServer(("127.0.0.1", 0), LocalPages)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()


@pytest.fixture(scope="session")
def project_dir(tmp_path_factory):
    """A private copy of the project. Its fetch server may read this computer's addresses (the test pages)."""
    dst = tmp_path_factory.mktemp("links") / "proj"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("runs", "tests", "__pycache__", ".env", ".pytest_cache"))
    for f in (dst / "reports").iterdir():
        if f.name != ".gitkeep":
            f.unlink()
    (dst / ".env").write_text("MAIL_TEST_MODE=1\nLLM_API_KEY=test\n", encoding="utf-8")
    cfg = json.loads((dst / "project.json").read_text(encoding="utf-8"))
    cfg["mcp_servers"]["fetch"]["args"].append("--allow-private-ips")
    (dst / "project.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    return dst


@pytest.fixture(scope="session")
def proj(project_dir):
    """The project loaded once: the three MCP servers start once for the whole test session."""
    return load_project(str(project_dir))


@pytest.fixture()
def links(project_dir, monkeypatch):
    """The project's helper module (of the copy) and an empty reports/ folder."""
    import importlib
    monkeypatch.syspath_prepend(str(project_dir))
    for name in [m for m in sys.modules if m in ("functions", "tools") or m.startswith(("functions.", "tools."))]:
        del sys.modules[name]
    for f in (project_dir / "reports").iterdir():
        if f.name != ".gitkeep":
            f.unlink()
    return importlib.import_module("functions._links")


class MiniSMTP(socketserver.StreamRequestHandler):
    """Just enough SMTP (EHLO, AUTH, MAIL, RCPT, DATA, QUIT) to receive mail."""
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
    for k, v in {"SMTP_HOST": "127.0.0.1", "SMTP_PORT": str(server.server_address[1]), "SMTP_USER": "bot@example.com",
                 "SMTP_PASS": "pw", "OFFICE_EMAIL": "office@example.com", "MAIL_TO": "a@example.com,b@example.com",
                 "MAIL_TEST_MODE": "1"}.items():
        monkeypatch.setenv(k, v)
    yield MiniSMTP.mails
    server.shutdown()
    server.server_close()
