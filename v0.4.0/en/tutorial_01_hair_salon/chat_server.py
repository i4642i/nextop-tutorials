"""A customer chat page for one worker: python chat_server.py, then open http://127.0.0.1:8771

Each message is one `nextop ask` (run_ask) with the chat so far as history, so every answer is recorded in runs/.
The reception is an ask worker with a conversation navigator (workers/reception/navigator.py): before each question
the navigator picks the step (consult, booking, manage) and the step notice from what is recorded.
The tools read and write the file servers themselves, with the reception's rights (book and change_booking write
bookings; the reception's model never sees bookings, the tools filter). When the book tool made a booking, the flow
`booking_notes` runs in the background with the whole chat (the booking waits as pending; nuri summarizes, duri writes
the designer's prep memo, mail_designer mails it with approve and decline links; the customer is texted only after the
designer answers). When the customer ends the chat (POST /api/end), the flow `chat_end` deletes the chat's consult
rows; rows of a chat that is never ended go one day after they were written.
The page keeps the chat and a customer id in the browser and sends both with every message; the server keeps nothing
between messages. The customer id is the subject of every run of the chat: the reception reads and writes only that
id's rows of consult and customers. Bookings are found by name and phone (the identity check), not by it.
GET /schedule shows schedule.html, the bookings per day and designer.
GET /approve/<id>?t=<token> and /decline/<id>?t=<token> are the links in the designer's mail (flow `decide`).

  --worker reception    which worker answers (default reception)
  --host / --port    where to listen (default 127.0.0.1:8771; use 0.0.0.0 to reach it from other computers)
"""
import argparse
import json
import pathlib
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from nextop.core.load import load_project
from nextop.runtime.flow import FlowError, run_ask, run_flow

from functions._approval import decide
from functions._salon import data_dir

HERE = pathlib.Path(__file__).resolve().parent
PAGE = (HERE / "chat.html").read_bytes()
MAX_TURNS = 20          # messages of history sent with a question (older ones are dropped)


def booking_made(run_dir: pathlib.Path) -> str | None:
    """The booking id when the worker's book tool made a booking in this answer, else None."""
    for path in run_dir.rglob("tools.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            rec = json.loads(line)
            result = rec.get("result")
            if rec.get("name") == "book" and rec.get("ok") and isinstance(result, dict) and result.get("booked"):
                return result["booking"]
    return None


def notes(transcript: list, booking: str) -> None:
    """The booking is made (pending): run the flow booking_notes (summary, prep memo, mail to the designer)."""
    res = run_flow(load_project(str(HERE)), "booking_notes", {"transcript": transcript, "booking": booking})
    print(f"booking {booking}: flow run {res.run_id} {'done' if res.ok else 'failed: ' + str(res.reason)}")


def answer(worker: str, message: str, history: list, subject: str, background: bool = True) -> dict:
    """One chat message: one run, with the chat's customer id as its subject (the same id for every message)."""
    proj = load_project(str(HERE))
    run_id = time.strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]
    res = run_ask(proj, worker, message, history=history[-MAX_TURNS:], subject=subject, run_id=run_id)
    if not res.ok:
        return {"error": "Sorry, no answer could be made. Please send it again in a moment.", "run": res.run_id}
    out = res.outputs[worker]["answer"]
    reply = out.get("answer", "")
    booking = booking_made(pathlib.Path(res.run_dir))
    if booking:
        transcript = history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]
        if background:
            threading.Thread(target=notes, args=(transcript, booking), daemon=True).start()
        else:
            notes(transcript, booking)
    return {"answer": reply, "run": res.run_id, "step": out.get("step", ""), "booking": booking}


def end_chat(subject: str) -> dict:
    """The customer ended the chat: the flow chat_end deletes the chat's consult rows."""
    res = run_flow(load_project(str(HERE)), "chat_end", {"_subject": subject})
    return {"ended": res.ok, **({} if res.ok else {"error": str(res.reason)})}


def answer_page(message: str) -> bytes:
    import html
    return ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'><title>Booking answer</title></head>"
            "<body style='font-family:system-ui,sans-serif;padding:32px;font-size:1.2rem'>"
            f"<p>{html.escape(message)}</p></body></html>").encode()


class Handler(BaseHTTPRequestHandler):
    worker = "reception"

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, PAGE, "text/html; charset=utf-8")
        elif self.path.startswith(("/approve/", "/decline/")):
            url = urllib.parse.urlsplit(self.path)
            action, _, booking_id = url.path.strip("/").partition("/")
            token = urllib.parse.parse_qs(url.query).get("t", [""])[0]
            code, message = decide(urllib.parse.unquote(booking_id), action == "approve", token)
            self._send(403 if code == "refused" else 200, answer_page(message), "text/html; charset=utf-8")
        elif self.path == "/schedule" and (data_dir() / "schedule.html").exists():
            self._send(200, (data_dir() / "schedule.html").read_bytes(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path not in ("/api/chat", "/api/end"):
            return self._send(404, b"not found", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if self.path == "/api/end":
                subject = "".join(str(body.get("customer", "")).split())[:200] or "guest"
                return self._send(200, json.dumps(end_chat(subject)).encode(), "application/json; charset=utf-8")
            message = str(body["message"]).strip()
            history = [{"role": h["role"], "content": str(h["content"])} for h in body.get("history", [])
                       if h.get("role") in ("user", "assistant")]
            if not message:
                raise ValueError("empty message")
            subject = "".join(str(body.get("customer", "")).split())[:200] or "guest"    # a subject has no spaces
            out = answer(self.worker, message, history, subject)
        except (KeyError, ValueError, TypeError) as e:
            out = {"error": f"bad request: {e}"}
        except FlowError as e:
            out = {"error": str(e)}
        self._send(200, json.dumps(out, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def log_message(self, fmt, *args):
        pass


def main() -> None:
    ap = argparse.ArgumentParser(description="customer chat page for one worker")
    ap.add_argument("--worker", default="reception")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8771)
    a = ap.parse_args()
    Handler.worker = a.worker
    print(f"chat page: http://{a.host}:{a.port}  (worker {a.worker}; Ctrl+C stops)")
    ThreadingHTTPServer((a.host, a.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
