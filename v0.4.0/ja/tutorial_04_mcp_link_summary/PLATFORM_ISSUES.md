# Platform issues found while building tutorial 4 (Japanese edition)

Found with nextop 0.3.1 installed from PyPI (`pip install "nextop[pdf,mcp]==0.3.1"` in a fresh venv, no platform checkout on the path, no PYTHONPATH). Nothing was worked around by changing the platform. The issues of the earlier editions are in `../../en/tutorial_04_mcp_link_summary/PLATFORM_ISSUES.md` and `../../ko/tutorial_04_mcp_link_summary/PLATFORM_ISSUES.md`.

## No new platform problem
- All three official reference servers (fetch 2026.11.4, time 2026.11.4, filesystem 2.2.0) started on Windows 10 through `mcp_servers` (stdio, `uvx` and `npx`) with the 0.3.1 PyPI build; the flow check said `OK: mcp link summary (workers 2, tools 20, flows 1, file servers 0)`, the 15 tests passed, and the real runs (2026-11-25, local model; the one in the README: run 20261125-212238-1ab6, 7 model calls, about 23 s, mail sent) ended `done`.
- The Japanese language pack (`"language": "ja"`), project `notes` on an MCP tool and the program checks on the saved file worked as documented.

## Notes (not platform problems)
- `nextop check` without a key prints its message in English (`[error] adapter llm.default: API key missing: ...`) also in a `"language": "ja"` project. The language pack is for what workers read; the CLI messages are English in every edition, so the README quotes them as they are.
- In the README run the local model put a Korean word (`위한`) into a Japanese key point twice; the reader's program check (`japanese_errors` in `functions/_links.py`) sent it back both times and the third save was clean. In an earlier run of the same day the writer split one long key point into two bullets; the writer's mission now says one bullet per key point (a mission wording fix, not a platform issue).

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5, 2026-11-26)
- This tutorial has no file server, so the file server rework changed nothing here; only `setup.bat` can now install a
  local nextop wheel (`NEXTOP_WHEEL`, `NEXTOP_EXTRAS=[mcp]`). The guide of 0.4.0 says to start Python MCP servers with
  `uvx --from <package>==<version> <command>` and Node servers with `npx -y <package>@<version>`, as `project.json` does.
- Checked with the compiled wheel 0.4.0.dev5 in the Korean edition's venv: `nextop check` OK and the offline tests
  pass. No real run was made for this Japanese edition. No new platform problem.

## Phase 10: real run with the compiled wheel 0.4.0.dev6 and gpt-5.4-mini (2026-11-26)

Fresh venv with only the wheel (`site-packages`, `.pyd`, 0.4.0.dev6; `nextop[mcp]`, `uv`). Three MCP servers started; the `fetch`, `time` and `filesystem` calls worked. Final run: `C:\Users\SHK\AppData\Local\Temp\claude\61d2a55c1c8ed559\7801ea38-cfcd-4c6c-a551-04091160998b\scratchpad\phase10ja\t04c\runs\20261126-235603-30a0` (5 model calls, 12,351 tokens, 13.1 s). No platform problem found.

- The reader mission now reads at most the first 5000 characters of each page (`fetch__fetch` with `max_length` 5000, no `start_index`). With the first wording (a long sentence that said not to page on) the model still fetched `start_index` 5000 of the Wikipedia page once (`C:\Users\SHK\AppData\Local\Temp\claude\61d2a55c1c8ed559\7801ea38-cfcd-4c6c-a551-04091160998b\scratchpad\phase10ja\t04\runs\20261126-234923-384e`: 6 calls, 17,716 tokens); with "call exactly once ... do not use start_index" it did not (`t04b`, `t04c`). This is mission wording, not the platform.
- The reader copied the page title with its leading `# ` into the report once (`t04b`); the mission now says to leave the `# ` off, and the last run is clean.
- The first 5000 characters of the Wikipedia page are mostly the infobox, so the points for that page are thin (what the page contains, not facts from the text). That is a consequence of the 5000-character limit.

## nextop 0.4.0.dev9 (branch fs-graph, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `15 passed`, one real run with gpt-5.4-mini (evidence in scratchpad
`phase14\realrun\t04_ja`): reader 3 calls (`fetch__fetch` three times: the Wikipedia page again with `start_index` 5000,
although the mission says not to page on; a model mistake, left as it is), writer 3 calls, 17,725 tokens, 21.0 s;
report in Japanese (no Korean letters) and mail made. No tutorial file changed. No new platform problem.
