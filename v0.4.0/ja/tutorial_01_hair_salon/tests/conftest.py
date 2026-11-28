"""Test setup: a private copy of the project per test, its own data folder, and a scripted LLM.

The tests never call a real model. FakeLLM answers from a script per worker, so a chat and the flows can be checked
without an API key. Everything the program does (the navigator, free times, the identity check, the tools and flow
functions that write bookings, consult and customers, SMS outbox, mail) runs for real, in the copy.
"""
import importlib
import importlib.util
import os
import pathlib
import shutil
import sys
import uuid

import pytest

from nextop.adapters import Reply, ToolCall  # noqa: E402
from nextop.core.load import load_project  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
TITLES = {"施術準備": "duri", "カウンセリング要約": "nuri", "受付": "hana"}
REPLY_CHECKER = "ワーカーが相手に送ろうとしている回答1つを"     # how the platform's reply LLM checker call starts (ja pack)


class FakeLLM:
    """Scripted replies per worker: script = {"hana": [step, ...], "nuri": [...]}; a step is a Reply or f(messages)."""

    def __init__(self, script):
        self.script = {k: list(v) for k, v in script.items()}
        self.calls = []                      # (worker, messages) of every request
        self.tools = []                      # (worker, names of the tools offered) of every request

    def chat(self, model, messages, tools=None):
        head = messages[0]["content"]
        if tools is None and head.startswith(REPLY_CHECKER):     # the reception's reply LLM checker (reply_checks)
            self.calls.append(("checker", messages))
            step = self.script["checker"].pop(0) if self.script.get("checker") else Reply(text='{"failed": []}')
            return step(messages) if callable(step) else step
        who = next((v for k, v in TITLES.items() if k in head), "hana")
        self.calls.append((who, messages))
        self.tools.append((who, sorted(getattr(x, "name", None) or x.get("name") or x["function"]["name"]
                                       for x in tools or [])))
        step = self.script[who].pop(0)
        return step(messages) if callable(step) else step

    def supports(self, model, feature):
        return False


def call(name, args, call_id="c1"):
    return Reply(tool_calls=[ToolCall(id=call_id, name=name, arguments=args)])


def say(text):
    """An open-question answer (what an ask worker saves)."""
    return call("save_output", {"answer": {"answer": text}})


def save(**outputs):
    return call("save_output", outputs)


def adapters(fake):
    return {"llm": {"default": fake}}


def rows(**items):
    """put arguments: consult rows; a value (words), a (words, state) pair for a purpose row, or a dict of the row's
    other fields (the style row: {"style": "ツーブロック", "words": "ツーブロックで"})."""
    out = []
    for k, v in items.items():
        if isinstance(v, dict):
            out.append({"item": k, **v})
            continue
        words, state = v if isinstance(v, tuple) else (v, None)
        out.append({"item": k, "words": words, **({"state": state} if state else {})})
    return {"to": "fs://consult", "rows": out}


def _purge():
    for name in [m for m in sys.modules if m in ("functions", "tools", "seed", "navigator")
                 or m.startswith(("functions.", "tools."))]:
        del sys.modules[name]


@pytest.fixture()
def project_dir(tmp_path, monkeypatch):
    """A private copy of the project (its file server stores, runs and data stay in the test's folder)."""
    dst = tmp_path / "proj"
    shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(
        "runs", "memos", "outbox", "tests", "__pycache__", ".env", ".pytest_cache", "schedule.html",
        "store", "video", ".venv"))                  # video/ (the tutorial video's files) and .venv are not the project
    (dst / ".env").write_text("SMS_MODE=outbox\nMAIL_TEST_MODE=1\nLLM_API_KEY=test\nAPPROVE_SECRET=test-secret\n",
                              encoding="utf-8")
    monkeypatch.setenv("SALON_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LLM_API_KEY", "test")
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    _purge()
    sys.path.insert(0, str(dst))
    yield dst
    sys.path.remove(str(dst))
    _purge()


@pytest.fixture()
def salon(project_dir):
    """functions._salon of the copy, with the example bookings seeded (flow seed)."""
    assert importlib.import_module("seed").main(project=str(project_dir)) == 0
    return importlib.import_module("functions._salon")


@pytest.fixture()
def proj(project_dir):
    return load_project(str(project_dir))


class Chat:
    """The file servers of one chat message, opened the way a run opens them (subject: the customer id): put() writes
    consult rows with the reception's own put tool, ctx is what a tool or the navigator gets (the reception's views:
    its rights, the same subject scope), nav() runs the navigator, tool() runs a tool of the project."""

    def __init__(self, project_dir, subject=None):
        from nextop.file_server import FileServerRuntime
        self.project_dir = pathlib.Path(project_dir)
        self.subject = subject or "c-" + uuid.uuid4().hex[:8]
        run_id = "t-" + uuid.uuid4().hex[:8]
        self.rt = FileServerRuntime(load_project(str(project_dir)), {"llm": {}}, self.project_dir / "runs" / run_id,
                                    None, self.subject)
        self._put = {t.name: t for t in self.rt.tools_for("reception", "reception")}["put"]
        self.ctx = {"run_id": run_id, "block": "reception", "subject": self.subject, "project": str(project_dir),
                    "file_servers": self.rt.views_for("reception", "reception", "reception")}

    def put(self, **items):
        res = self._put.run({"block": "reception"}, rows(**items))
        assert not res.get("refused") and "error" not in res, res
        return res

    def put_raw(self, **items):
        return self._put.run({"block": "reception"}, rows(**items))

    def nav(self):
        spec = importlib.util.spec_from_file_location("navigator", self.project_dir / "workers/reception/navigator.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.navigate(dict(self.ctx, worker="reception", question="", history=[], step=None, entered=[]))

    def tool(self, name, args=None):
        return importlib.import_module(f"tools.{name}").run(self.ctx, args or {})

    def rows(self, server):
        from functions._salon import view_rows
        return view_rows(self.ctx, server)
