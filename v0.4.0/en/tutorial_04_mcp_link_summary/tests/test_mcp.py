"""The three MCP servers as nextop loads them: tool names, the flow check, one direct call to each."""
import json

from nextop.validate.precheck import check_project


def test_servers_start_and_tools_are_named_server__tool(proj):
    assert proj.mcp_status == {"fetch": "", "time": "", "filesystem": ""}
    for name in ("fetch__fetch", "time__get_current_time", "filesystem__write_file", "filesystem__read_text_file"):
        assert name in proj.tools, name
        assert proj.tools[name].kind == "mcp"
    assert proj.tools["fetch__fetch"].server == "fetch" and proj.tools["fetch__fetch"].mcp_name == "fetch"
    assert "url" in proj.tools["fetch__fetch"].schema["properties"]


def test_flow_check_is_clean(proj):
    report = check_project(proj, "link_summary")
    assert report.errors == [] and report.warnings == [], (report.errors, report.warnings)


def test_fetch_reads_a_page(proj, site):
    got = proj.tools["fetch__fetch"].run({}, {"url": site + "/coffee.html"})
    assert "error" not in got, got
    assert "15 grams of coffee" in got["text"]


def test_time_answers_in_seoul(proj, links):
    got = proj.tools["time__get_current_time"].run({}, {"timezone": "Asia/Seoul"})
    data = got.get("data") or json.loads(got["text"])
    assert data["timezone"] == "Asia/Seoul" and data["datetime"].endswith("+09:00")
    assert data["datetime"][:10] == links.today_seoul()


def test_filesystem_writes_only_in_reports(proj, project_dir, links):
    got = proj.tools["filesystem__write_file"].run({}, {"path": "probe.md", "content": "# Probe · café\n"})
    assert "error" not in got, got
    assert (project_dir / "reports" / "probe.md").read_text(encoding="utf-8") == "# Probe · café\n"
    outside = proj.tools["filesystem__write_file"].run({}, {"path": str(project_dir / "project.json"), "content": "x"})
    assert "error" in outside
    assert json.loads((project_dir / "project.json").read_text(encoding="utf-8"))["mcp_servers"]
