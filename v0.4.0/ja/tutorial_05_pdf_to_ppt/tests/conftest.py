"""Test setup: make the project importable, offer a scripted LLM (nextop from PyPI).

The tests never call a real model. FakeLLM answers from a script in call order; SlideLLM answers the planner in order
and each copy of the writer (one per slide) from that slide's own script. Everything
the program does (reading the PDF into parts, the classification, the checks, the slides, the .pptx, the previews and
the mail) runs for real, on a temporary copy of the project, with a mini mail server on this computer.
"""
import json
import os
import pathlib
import shutil
import socketserver
import sys
import threading

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["PYTHONPATH"] = str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", "")

from nextop.adapters import Reply, ToolCall  # noqa: E402
from nextop.core.load import load_project  # noqa: E402


class FakeLLM:
    """Scripted replies for the summarizer: a step is a Reply or f(messages) -> Reply."""

    def __init__(self, steps):
        self.steps = list(steps)
        self.calls = []                      # messages of every request, for assertions

    def chat(self, model, messages, tools=None):
        self.calls.append(messages)
        step = self.steps.pop(0)
        return step(messages) if callable(step) else step

    def supports(self, model, feature):
        return False


class SlideLLM:
    """Scripted replies when the writer writes one slide per conversation (copies of the writer run at the same time):
    planner: the planner's replies in order; slides: {slide number: that slide's writer replies in order}. A writer
    call is told apart by the slide number in its piece (slide.no)."""

    def __init__(self, planner, slides):
        import threading
        self.planner, self.slides = list(planner), {n: list(v) for n, v in slides.items()}
        self.calls, self.by_slide, self._lock = [], {}, threading.Lock()

    def chat(self, model, messages, tools=None):
        import re
        with self._lock:
            self.calls.append(messages)
            if "みなと" in text_of(messages[:1]):
                step = self.planner.pop(0)
            else:
                no = int(re.search(r'"no":\s*(\d+),\s*"of":', text_of(messages)).group(1))
                self.by_slide.setdefault(no, []).append(messages)
                step = self.slides[no].pop(0)
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


@pytest.fixture(scope="session")
def sample_pdf(tmp_path_factory):
    """The tutorial's own sample PDF, made fresh (make_sample_pdf.py)."""
    import make_sample_pdf
    path = tmp_path_factory.mktemp("sample") / "sample_report.pdf"
    path.write_bytes(make_sample_pdf.make_pdf())
    return path


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    """A private copy of the project (runs/ and output/ stay out of the real folder)."""
    dst = tmp_path / "proj"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("runs", "output", "tests", "__pycache__", ".env",
                                                             ".pytest_cache", "store", "samples", "example_output"))
    (dst / ".env").write_text("MAIL_TEST_MODE=1\nLLM_API_KEY=test\n", encoding="utf-8")
    monkeypatch.setenv("DECK_DATA_DIR", str(tmp_path / "out"))
    return dst


@pytest.fixture()
def proj(project_dir):
    return load_project(str(project_dir))
