# Platform issues found while building tutorial 4 (English edition)

Found with nextop 0.3.0 installed from PyPI (`pip install "nextop[mcp]==0.3.0"` in a fresh venv, no platform checkout on the path). Nothing was worked around by changing the platform. The issues found while building the Korean edition (on the platform branch before the release) are in `../../ko/tutorial_04_mcp_link_summary/PLATFORM_ISSUES.md`.

## No new platform problem
- All three official reference servers (fetch 2026.11.4, time 2026.11.4, filesystem 2.2.0) started on Windows 10 through `mcp_servers` (stdio, `uvx` and `npx`) with the PyPI build; the flow check said `OK: mcp link summary (workers 2, tools 20, flows 1, file servers 0)`, and the real run (2026-11-25, local model, 5 model calls, about 16 s, mail sent) and the 14 tests passed.
- The English language pack, project `notes` on an MCP tool and the program checks on the saved file worked as documented.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)
- This tutorial has no file server, so the file server rework changed nothing here; only `setup.bat` changed (it can install a local nextop wheel). Checked with the compiled wheel 0.4.0.dev5 in a fresh venv: `nextop check` OK and the offline tests pass. The real run of the Korean edition (`../../ko/tutorial_04_mcp_link_summary/PLATFORM_ISSUES.md`) started the three MCP servers and finished with no new platform problem; this English edition was not run against a real model for 0.4.0.

## nextop 0.4.0.dev6: real run on 2026-11-26 (compiled wheel from the fs-graph branch, a fresh venv per tutorial, gpt-5.4-mini)

Checked: `nextop check` OK (three MCP servers started), 14 offline tests passed, then two real runs with a local test mail server.

- The three servers (`fetch`, `time`, `filesystem`) started and answered. No new platform problem.
- Tutorial change: the reader mission now says to fetch each page once with `max_length` 5000 (at most the first 5,000 characters) and never to page on with `start_index`. In the first run the model paged on for Wikipedia although the mission said not to (6 model calls, 14,987 tokens); after the mission said "even when the result ends with a note that the content was cut", the second run fetched each page once: 5 model calls, 10,356 tokens, about 12 s, passed at the first save, mail made.

## nextop 0.4.0.dev9 (branch fs-graph, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `14 passed`, one real run with gpt-5.4-mini (evidence in scratchpad
`phase14\realrun\t04_en`): reader 2 calls (`fetch__fetch` twice, first 5,000 characters, no `start_index`), writer 3
calls, 10,264 tokens, 18.0 s; report and mail made. No tutorial file changed (the Korean edition has no change after
0.4.0.dev6 either). No new platform problem.
