# Platform issues found while building tutorial 2

Found with the platform checkout on branch naw-steps (nextop 0.3.0, not published yet). Nothing was worked around by changing the platform.

## 1. The published "nextop 0.2.0" wheel has none of the features this tutorial uses (blocker for readers until 0.3.0 is released)
- Tried: `python -c "from nextop.parts import check_part"` with the PyPI wheel (Python 3.11, no PYTHONPATH).
- Happened: `ModuleNotFoundError: No module named 'nextop.parts'`. The quote check part (`quotes`), upload `tags` and the `for_each` step exist only on the branch.
- Expected: a release that has them before the tutorial goes on the homepage (README says "nextop 0.3.0 이상").
- Reproduce: the line above.
- Tutorial impact: high until release. The tests fall back to the platform checkout (`NEXTOP_SRC`) for our own development, same as tutorial 1.

## 2. A tool cannot ask a persistent file server what it already holds (dedupe by page address)
- Tried: dedupe news by page address across runs. A tool (`tools/news_search.py`) has `ctx` with `project`, `files_dir`, `run_id`, `block`, and no file server access.
- Happened: the tool reads `file_servers/news/store/items/*.json` and the article files directly. That depends on the store's folder layout, which the guides tell nobody to touch ("do not edit by hand").
- Expected: a supported way to ask "is this `source` already stored?" (a tool helper, or an upload that merges items with the same `source`). Today the store treats the same content under the same title as one item; a page seen again with other words is a new item.
- Reproduce: store an item with `source` X, run a tool that needs to know X is there.
- Tutorial impact: medium. The tool is read-only on the store and the tests cover it, but a layout change would break it silently (every article would look new).

## 3. Replacing a helper module in a test does not reach tools (low)
- Tried: `monkeypatch.setattr(functions._news, "tavily_search", fake)` before `load_project`, and after it.
- Happened: the real search ran (HTTP 401). `load_project` drops the project's imported modules and imports them again for each tool, so the tool holds its own copy of the helper. This is described in the guides (2026-11-24 note) but easy to miss.
- Expected: nothing to fix; a test hint would help ("fake the outside service, not the module").
- Tutorial impact: low. The tests run a small local HTTP server and point `TAVILY_URL` at it, which also tests the real request and answer handling.

## 4. `nextop resume --from <block>` after a share line changed gives the function nothing, without a word (low)
- Tried: added a share line `analyst -> mail_outlook` (the function has `FILES_IN = True`), then `nextop resume <run> --from mail_outlook`.
- Happened: the run finished; `inputs["files/news"]` was empty, so the mail named every article "not found". The analyst had ended before the share line existed, so it never handed its files on. `--from analyst` fixed it.
- Expected: a warning that a share line's sender already ended, or the share being made again on resume.
- Tutorial impact: low (only when editing a finished run).

## 5. A cited address may be a part address (`fs://news/003#p1`); functions must cut it themselves (low)
- Happened: the model often cites `fs://news/001#p3` (the map lists parts). The quote check accepts it, but a function that wants the article behind it has to split on `#`.
- Expected: a helper such as `nextop.file_server.base_address()` (or the file record lookup accepting a part address).
- Tutorial impact: low. `functions/mail_outlook.py` does `address.split("#")[0]`.

## Fixed on branch naw-steps
- Issue 2 (tool cannot ask a file server): fixed in 9a63576 (ctx["file_servers"][name].exists_source(url) and more, read-only, same read rule as the worker).
- Issue 3 (helper module replaced in a test): fixed in 9a63576 (unchanged helpers keep identity across load_project).
- Issue 4 (resume --from after a share line changed): fixed in 9a63576 (ended senders share with the new receiver; event share_lines_changed).
- Issue 5 (part address): fixed in 9a63576 (nextop.file_server.record_address; quote check and sources.text accept #p3, #P3, spaces).
- Issue 1 (PyPI 0.2.0): left to the release.

The tutorial now uses these fixes (verified on 9a63576): `tools/news_search.py` asks `ctx["file_servers"]["news"].sources()`, `functions/mail_outlook.py` uses `record_address`, the store-reading helpers and the part-address cutting are gone. No new platform problem found in the real run (2026-11-25).

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)

The tutorial now uses a file server with one type folder (`types/articles/type.json`: md, the example `paragraphs`
splitter copied to `parts/splitter/paragraphs.py`, `first_sentence` map) and the common tools (`upload`, `query`,
`get`). A reason cites one article paragraph (`fs://news/003#1.2`); the program copies that paragraph into the mail
(the worker no longer types a quote), and `checks.py` checks that the address is one body paragraph the worker may read.
Issue 5 above (part addresses) is now the normal case: `normalize_address` / `record_address` and the `parts` of
FILES_IN rows (fs-graph `ba54649`) give the paragraph text to the mail function. Checked with the compiled wheel in a
fresh venv: `nextop check` OK, tests pass, one real run with Tavily and gpt-5.4-mini (run `20261126-224308-b154`:
20 model calls, 72,621 tokens, 54.8 s; the 0.3.0 run had 24 calls, 126,067 tokens, about 102 s).

### 6. A `for_each` conversation can write the items of the other conversations (high)
- Happened: in the judge conversation for SpaceX (the last item), the analyst saved `outlook.items` for all four
  companies. The final output holds 7 items (Samsung, SK hynix and NVIDIA twice); the mail took the last copy of each, so
  the earlier per-company judgments (their own articles opened and read) were replaced by thin ones written in the
  SpaceX conversation.
- Evidence: scratchpad `phase9\realrun\t02\runs\20261126-224308-b154\blocks\analyst\attempt-1\output.json`
  (7 items) and `tools.jsonl` (the last `save_output`, step judge, item SpaceX in `steps.jsonl`).
- Cause: `nextop/steps.py` `focus_widen` (about line 562-590): `mine` takes every item of the narrowed save; only the old
  items whose key is in the focus item's values are dropped, so items of other keys are added again.
- Suggested fix: in a for_each conversation a save may only hold items whose key is one of the focus item's values;
  refuse the others with a sentence the worker can act on ("this conversation is about SpaceX; save only its item").

### 7. `get` gives paragraph text without addresses, or addresses without text (medium)
- Happened: with the paragraph splitter an article is one section `#1` with paragraphs `#1.1 ...`. `get fs://news/001`
  answers one card (`#1`); `get fs://news/001#1` answers the paragraph cards without text (4 paragraphs > 3); a short
  article (3 leaves or fewer) comes as one text with no paragraph addresses. The worker cannot see a paragraph's text
  and its address together except through `query` or by opening every paragraph. In the real run the analyst guessed
  `fs://news/001#2`, `#3`, `#4` after the cards (refused, see 8).
- Evidence: `tools.jsonl` of the run above (steps scan and judge); the program-side test in scratchpad `phase9\exp\t02_get.py`.
- Cause: `nextop/file_server/typed.py` `_open_typed` (about line 213-226): the leaf count (`LONG_TEXT_PARTS` = 3,
  `nextop/file_server/__init__.py:151`) decides between cards and the joined text; the joined text drops the leaf
  addresses; a node with a single child answers that child's card.
- Suggested fix: decide by the length of the text (not the number of leaves), and when the text is given, give it as
  its leaves `[{"address", "text"}]`; a node with one child opens the child.

### 8. A part address that does not exist is answered as "not a file I own" (low)
- Happened: `get fs://news/001#2` (no such part; the unit is readable) answered "'fs://news/001#2'는 내가 소유한 파일이
  아닙니다. 입력에 적힌 파일만 읽을 수 있습니다." The worker cannot tell a wrong part from a missing right.
- Cause: `nextop/file_server/typed.py:206-209`: `node_at` gives None for a missing part of a readable unit too, and the
  answer is `file_server_no_access`.
- Suggested fix: when the unit is readable, say the part does not exist and name its top parts (nothing leaks).

### 9. A test that hands its own adapters gets no default index, and no `query` tool, silently (low)
- Happened: the tutorial tests call `run_flow(..., adapters={"llm": ...})`; the analyst had no `query` tool
  ("'query' 도구는 없습니다"), although `nextop run` gives it (the default `bm25` index part is added only when the adapters
  are built from project.json).
- Cause: `nextop/runtime/flow.py:139` and `:771` use the given adapters as they are; `_index_parts` runs only inside
  `build_adapters` (`flow.py:105`).
- Suggested fix: add the index parts to given adapters too (a part, not an adapter), or `nextop check` / the run says
  which file server has no index. The tests now name `{"index": {"bm25": make_index("bm25", ROOT)}}` (`tests/conftest.py`).

### Notes (tutorial changes from the real run, not platform problems)
- The collector copied one long file path wrong (a part of the scratch folder name was dropped) and that article was
  refused. `news_search` now returns the file name only; `upload` finds a relative name in the block's files folder.
- `query` with a Korean question found no paragraph in an English article (bm25 matches words). The mission now says
  to ask in the article's language.
- Articles written on Windows have `\r\n` line ends; the paragraph check first missed a whole section (`#1`) because
  its blank-line rule did not allow `\r`. Fixed in `checks.py` (and a test with `\r\n`).

## nextop 0.4.0.dev6 (branch fs-graph `044087f`, R1-R8 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev6 in a fresh venv (nextop imported from the installed `.pyd`, no source on the path): `nextop check` OK, tests pass, one real run with gpt-5.4-mini (evidence in scratchpad `phase10ko`).

- 6 (`for_each` writes other items): fixed in `4152c31` (R1), confirmed live. In the Samsung and SK hynix
  conversations the analyst first saved all four companies; the save was refused with "이 대화는 삼성전자만 다룹니다. 그 몫만
  저장하세요. 받지 않음 (저마다 자기 대화가 있습니다): outlook.items: SK하이닉스; ..." and the next save held only that company.
  The output has 4 items, one per company, each with its own 2 reasons and paragraphs (run `20261127-000558-4555`,
  `blocks\analyst\attempt-1\output.json`, `tools.jsonl`).
- 7 (`get` text without addresses): fixed in `ccf42ab` (R3), confirmed: `get fs://news/002` answers `parts` with every
  paragraph's address and text (the article's single section is opened for it). The mission now says so.
- 8 (missing part answered as "not mine"): fixed in `ccf42ab` (R5); no missing part address was used in this run.
- 9 (given adapters without index): fixed in `9f2c9c3` (R6); `tests/conftest.py` no longer names the index; `19 passed`.
- Run: 24 model calls (collector 3, analyst 21), 93,452 tokens, 59.7 s; mail sent; reasons carry program-attached
  paragraphs (README sample replaced with this mail).
- Tutorial change (not platform): Tavily now also returns company profile pages (`https://tavily.com/knowledge/company/...`,
  no date). In the first run of the day the collector uploaded them for NVIDIA and SpaceX (and an unrelated "SPCX Pvt.
  Ltd." profile), and the mail cited profile lines as reasons (scratchpad `phase10ko\realrun\t02_profiles`). `tavily.com`
  is now in `stocks.json` `search.exclude_domains` (sent to Tavily and filtered again by `news_search`).
- Tutorial notes: one article's paragraph holds the site's menu text (the search result content has no blank lines);
  Samsung's two reasons cite the same paragraph (the mission asks for different paragraphs; not checked).
- No new platform problem.

## nextop 0.4.0.dev7 (branch fs-graph, F1-F6 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev7 in a fresh venv (nextop imported from the installed `.pyd`, version
0.4.0.dev7, no source on the path): `nextop check` OK, `19 passed`, one real run with gpt-5.4-mini and Tavily
(`tavily.com` excluded as before; evidence in scratchpad `phase11ko\realrun\t02`).

- `parts/splitter/paragraphs.py` is the new example (F2): a block over 800 characters is cut at sentence ends into
  paragraphs of about 400 characters, a fragment under 15 characters that ends no sentence joins its neighbour, a "#"
  line over 200 characters is text. On this run's 4 articles: 38 paragraphs, longest 718 characters, none over 800, none
  under 15 (the old splitter on the same files: 40 paragraphs, longest 1,218, one over 800, 3 under 15). On the dev6
  run's articles: longest 1,218 -> 718. The article's first paragraph `#1.1` is still the date and address lines, so
  the paragraph addresses in the tests, mission and checks did not change.
- Run: 26 model calls (collector 4, analyst 22), 98,961 tokens, 61.5 s (dev6: 24, 93,452, 59.7 s); 4 of 9 analyst
  saves refused (another company's part once, 3 reasons for a "thin" company 3 times); mail sent (README sample
  replaced with this mail). Each reason cites a body paragraph of a few sentences; the Samsung paragraph still starts
  with one line of the site's menu (no sentence end between the menu and the article's first sentence).
- Tutorial notes: Samsung's and NVIDIA's two reasons each cite the same paragraph (the mission asks for different
  paragraphs; not checked).
- No new platform problem.
