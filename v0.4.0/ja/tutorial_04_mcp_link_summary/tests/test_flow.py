"""The whole flow (intake -> reader -> writer -> mail_report) with a scripted model.

The MCP servers do the real work: fetch reads the local test pages, time gives today in Seoul, filesystem saves the
report in reports/. The checks read the saved file and the mail sends it.
"""
import email
import email.policy
import json

from conftest import FakeLLM, adapters, call, report_file, save, tool_results
from nextop.runtime.flow import run_flow

NOTES = {"pages": [
    {"page": 1, "read": True, "title": "What is MCP",
     "points": ["MCPは、AIアプリを外部のツールやデータにつなぐオープンな標準である。",
                "サーバーがツールを提供し、AIアプリがそれを呼び出す。", "標準入出力またはHTTPでやり取りする。"],
     "problem": ""},
    {"page": 2, "read": True, "title": "ハンドドリップコーヒーの淹れ方",
     "points": ["コーヒー豆15グラムに対してお湯250ミリリットルを使う。", "お湯の温度は92度くらいがちょうどよい。",
                "最初の30秒は蒸らす。"],
     "problem": ""}]}


def reader_steps(site):
    def save_notes(messages):
        texts = [r.get("text", "") for r in tool_results(messages)]
        assert any("open standard" in t for t in texts) and any("コーヒー豆15グラム" in t for t in texts), texts
        return save(notes=NOTES)
    return [call("fetch__fetch", {"url": site + "/mcp.html"}, "f1"),
            call("fetch__fetch", {"url": site + "/coffee.html"}, "f2"),
            save_notes]


def report_text(today, site, skip_second_url=False):
    lines = [f"# リンク要約 · {today} (水)", "", "## 1. What is MCP", f"アドレス: {site}/mcp.html"]
    lines += [f"- {p}" for p in NOTES["pages"][0]["points"]]
    lines += ["", "## 2. ハンドドリップコーヒーの淹れ方", "アドレス: " + ("（なし）" if skip_second_url else f"{site}/coffee.html")]
    lines += [f"- {p}" for p in NOTES["pages"][1]["points"]]
    lines += ["", "## ひとことで", "MCPとは何か、そしてハンドドリップコーヒーの淹れ方をまとめた。"]
    return "\n".join(lines) + "\n"


def writer_steps(site, first_misses_url=False):
    def write(messages, skip=False):
        today = next(r["data"]["datetime"][:10] for r in tool_results(messages) if "datetime" in r.get("data", {}))
        return call("filesystem__write_file", {"path": report_file(messages), "content": report_text(today, site, skip)},
                    f"w{len(messages)}")

    steps = [call("time__get_current_time", {"timezone": "Asia/Seoul"}, "t1"),
             lambda m: write(m, skip=first_misses_url)]
    if first_misses_url:
        steps += [lambda m: save(report={"file": report_file(m), "headline": "MCPとコーヒーの2ページを要約しました"}),
                  lambda m: write(m)]
    steps += [lambda m: save(report={"file": report_file(m), "headline": "MCPとコーヒーの2ページを要約しました"})]
    return steps


def _run(proj, site, first_misses_url=False):
    fake = FakeLLM({"reader": reader_steps(site), "writer": writer_steps(site, first_misses_url)})
    res = run_flow(proj, "link_summary", {"links": f"{site}/mcp.html\n{site}/coffee.html"}, adapters=adapters(fake))
    return res, fake


def test_whole_flow_reads_writes_and_mails(proj, project_dir, site, links, smtp_server):
    res, fake = _run(proj, site)
    assert res.ok, res.failed
    request = res.outputs["intake"]["request"]
    assert [p["url"] for p in request["pages"]] == [f"{site}/mcp.html", f"{site}/coffee.html"]
    saved = (project_dir / "reports" / request["report_file"]).read_text(encoding="utf-8")
    assert saved.startswith(f"# リンク要約 · {links.today_seoul()}")
    assert res.outputs["mail_report"]["mail"] == {"sent": True, "to": "office@example.com", "note": "sent"}

    to, raw = smtp_server[0]
    mail = email.message_from_string(raw, policy=email.policy.default)
    assert mail["Subject"] == "[リンク要約・テスト] MCPとコーヒーの2ページを要約しました（リンク2件）"
    body = mail.get_body(preferencelist=("plain",)).get_content()
    assert f"アドレス: {site}/coffee.html" in body and "コーヒー豆15グラムに対してお湯250ミリリットルを使う。" in body

    assert all(w == "reader" for w, _ in fake.calls[:3]) and all(w == "writer" for w, _ in fake.calls[3:])
    records = (res.run_dir / "blocks" / "writer" / "attempt-1" / "tools.jsonl").read_text(encoding="utf-8")
    assert "time__get_current_time" in records and "filesystem__write_file" in records


def test_report_without_an_address_goes_back_to_the_writer(proj, project_dir, site, links, smtp_server):
    res, fake = _run(proj, site, first_misses_url=True)
    assert res.ok, res.failed
    refused = [m for w, msgs in fake.calls if w == "writer" for m in msgs if m["role"] == "tool"]
    assert any(f"lacks the address of page 2: {site}/coffee.html" in (m["content"] if isinstance(m["content"], str)
                                                                       else json.dumps(m["content"], ensure_ascii=False))
               for m in refused)
    request = res.outputs["intake"]["request"]
    assert f"{site}/coffee.html" in (project_dir / "reports" / request["report_file"]).read_text(encoding="utf-8")


def test_missing_mail_settings_stop_the_run_before_any_model_call(proj, project_dir, site, links, monkeypatch):
    for k in ("SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS", "OFFICE_EMAIL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(links, "ROOT", links.ROOT / "no_env_here")
    res, fake = _run(proj, site)
    assert not res.ok and "intake" in res.failed and "SMTP_HOST" in json.dumps(res.failed, ensure_ascii=False) and fake.calls == []
