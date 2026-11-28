# Platform issues found while building tutorial 4

Found with the platform checkout on branch naw-steps (nextop 0.3.0, not published yet). Nothing was worked around by changing the platform.

All three official reference servers (fetch 2026.11.4, time 2026.11.4, filesystem 2.2.0) started and worked on Windows 10 through `project.json` `mcp_servers` (stdio, `uvx` and `npx`). None was dropped.

## 1. The published "nextop 0.2.0" wheel has no MCP servers (blocker for readers until 0.3.0 is released)
- Tried: `python -c "import nextop.mcp_servers"` with the PyPI wheel (Python 3.11, no PYTHONPATH).
- Happened: `ModuleNotFoundError: No module named 'nextop.mcp_servers'`. `mcp_servers` in project.json and the `<server>__<tool>` tools exist only on the branch.
- Expected: a release that has them before the tutorial goes on the homepage (README says "nextop 0.3.0 이상", `pip install "nextop[mcp]"`).
- Reproduce: the line above.
- Tutorial impact: high until release. The tests fall back to the platform checkout (`NEXTOP_SRC`), same as tutorials 1-3.

## 2. The official Python reference servers need a newer `mcp` than nextop's floor (low, a guide hint)
- Tried: `pip download --no-deps mcp-server-fetch==2026.11.4 mcp-server-time==2026.11.4` and read their requirements.
- Happened: both need `mcp>=2.3,<3`; `nextop[mcp]` asks for `mcp>=2.2,<3`, and this computer had mcp 2.2.0. `pip install mcp-server-fetch` into nextop's Python would upgrade the `mcp` that nextop itself uses (still inside nextop's range, so not wrong, but it changes nextop's environment as a side effect).
- Expected: the MCP guide (tools/README.md "MCP tools", manual tools/mcp) could say: run Python servers with `uvx --from <package>==<version> <command>` (or `npx -y <package>@<version>` for Node servers) so each server gets its own environment and an exact version. That is what this tutorial does.
- Reproduce: the line above.
- Tutorial impact: low. project.json starts the Python servers with `uvx`; nothing is installed into nextop's Python.

## Notes (not platform problems)
- The filesystem server resolves a relative path inside its allowed folder: `reports/x.md` becomes `reports/reports/x.md` and fails. In the first real run the writer tried that once, read the error and wrote the bare file name. A project note (`mcp_servers.filesystem.notes.write_file`) now says so, and the second real run wrote it right the first time. The platform's notes feature was enough.
- None of the three servers sends `instructions`, so only the tool descriptions (and the note above) reach the workers.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)
- Issue 2 (the guide did not say to run Python MCP servers with `uvx`): fixed in `f2f5206` (tools/README.md "MCP tools"
  and the manual's MCP unit say to start Python servers with `uvx --from <package>==<version> <command>` and Node servers
  with `npx -y <package>@<version>`); `fs-graph` has it.
- This tutorial has no file server, so the file server rework changed nothing here. Checked with the compiled wheel in a
  fresh venv: `nextop check` OK (`tools 20`, `file servers 0`), tests pass, one real run with gpt-5.4-mini (run
  `20261126-225130-2ecf`: the three MCP servers started, 8 model calls, 30,380 tokens, 28.7 s; the 0.3.0 run had 6 calls,
  16,968 tokens, 15.2 s; the reader made 5 calls this time). No new platform problem.

## nextop 0.4.0.dev6 (branch fs-graph `044087f`, R1-R8 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev6 in a fresh venv (nextop imported from the installed `.pyd`, no source on the path): `nextop check` OK, tests pass, one real run with gpt-5.4-mini (evidence in scratchpad `phase10ko`).

- No R-item concerns this tutorial (no file server).
- Mission change (owner agreed): the reader fetches each page once with `max_length` 5000 and does not follow
  `start_index`. Run: 5 model calls (reader 2, writer 3), 11,371 tokens, 13.9 s (dev5: 8 calls, 30,380 tokens, 28.7 s,
  the Wikipedia page read in four 5,000-character pieces); report and mail OK (run `20261126-235248-90b9`).
- No new platform problem.
