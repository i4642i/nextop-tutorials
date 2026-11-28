# Platform issues found while building tutorial 2 (US edition)

Found with nextop 0.3.0 installed from PyPI (`pip install nextop==0.3.0` in a fresh venv, no platform checkout on the path). Nothing was worked around by changing the platform. The issues found while building the Korean edition (on the platform branch before the release) are in `../../ko/tutorial_02_stock_news/PLATFORM_ISSUES.md`; the ones marked fixed there are fixed in 0.3.0.

## No new platform problem
- The English language pack, the persistent news file server with tags and expiry, the tool's read-only file server view (`ctx["file_servers"]["news"].sources()`), `for_each` steps, the `quotes` check part, `record_address` and `FILES_IN` worked as documented in the real run (2026-11-25, local model, 20 model calls, mail sent) and in the tests.
- The quote check's message comes from the project's language: in this English project it reads `quote not found: "..." (outlook.items[0].reasons[0]) is not in the text at fs://news/001. Quote the source word for word, or remove the claim.`

## Note (not a platform problem)
- In the real run Quinn (collector) called `news_get` on the article file the search tool had just written (`fs://news/9e37ef30f5.md`) and got `You do not own 'fs://news/9e37ef30f5.md'; only files listed in your input can be read.` twice. Harmless (it went on and uploaded the files), and the message says what is wrong. Quinn has no reason to open files; the mission does not ask it to.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)

The tutorial now uses a file server with one type folder (`types/articles/type.json`: md, the example `paragraphs` splitter copied to `parts/splitter/paragraphs.py`, `first_sentence` map) and the common tools (`upload`, `query`, `get`). A reason cites one article paragraph (`fs://news/003#1.2`); the program copies that paragraph into the mail (the worker no longer types a quote), and `checks.py` checks that the address is one body paragraph the worker may read. Checked with the compiled wheel 0.4.0.dev5 in a fresh venv: `nextop check` OK and the offline tests pass. Issues 1 to 4 below were found in the real run of the Korean edition (`../../ko/tutorial_02_stock_news/PLATFORM_ISSUES.md`, issues 6 to 9: same platform code, not dependent on the language); this edition was not run against a real model for 0.4.0.

### 1. A `for_each` conversation can write the items of the other conversations (high) - fixed in 0.4.0.dev6, verified in the real run
- Happened: in the judge conversation for the last company the analyst saved `outlook.items` for all four companies. The final output held 7 items (three companies twice); the mail took the last copy of each, so the earlier per-company judgments were replaced by thin ones written in the last conversation.
- Cause: `nextop/steps.py` `focus_widen` (about line 562-590): `mine` takes every item of the narrowed save; only the old items whose key is in the focus item's values are dropped, so items of other keys are added again.
- Suggested fix: in a for_each conversation a save may only hold items whose key is one of the focus item's values; refuse the others with a sentence the worker can act on ("this conversation is about SpaceX; save only its item").

### 2. `get` gives paragraph text without addresses, or addresses without text (medium) - fixed in 0.4.0.dev6, verified in the real run
- Happened: with the paragraph splitter an article is one section `#1` with paragraphs `#1.1 ...`. `get fs://news/001` answers one card (`#1`); `get fs://news/001#1` answers the paragraph cards without text (4 paragraphs > 3); a short article (3 leaves or fewer) comes as one text with no paragraph addresses. The worker cannot see a paragraph's text and its address together except through `query` or by opening every paragraph.
- Cause: `nextop/file_server/typed.py` `_open_typed` (about line 213-226): the leaf count (`LONG_TEXT_PARTS` = 3, `nextop/file_server/__init__.py:151`) decides between cards and the joined text; the joined text drops the leaf addresses; a node with a single child answers that child's card.
- Suggested fix: decide by the length of the text (not the number of leaves), and when the text is given, give it as its leaves `[{"address", "text"}]`; a node with one child opens the child.

### 3. A part address that does not exist is answered as "not a file I own" (low) - fixed in 0.4.0.dev6 (not met in the real run; covered by the platform's test)
- Happened: `get fs://news/001#2` (no such part; the unit is readable) answered that the address is not a file the worker owns and that only files listed in its input can be read. The worker cannot tell a wrong part from a missing right.
- Cause: `nextop/file_server/typed.py:206-209`: `node_at` gives None for a missing part of a readable unit too, and the answer is `file_server_no_access`.
- Suggested fix: when the unit is readable, say the part does not exist and name its top parts (nothing leaks).

### 4. A test that hands its own adapters gets no default index, and no `query` tool, silently (low) - fixed in 0.4.0.dev6 (the tests still name the index part; harmless)
- Happened: the tutorial tests call `run_flow(..., adapters={"llm": ...})`; the analyst had no `query` tool, although `nextop run` gives it (the default `bm25` index part is added only when the adapters are built from project.json).
- Cause: `nextop/runtime/flow.py:139` and `:771` use the given adapters as they are; `_index_parts` runs only inside `build_adapters` (`flow.py:105`).
- Suggested fix: add the index parts to given adapters too (a part, not an adapter), or `nextop check` / the run says which file server has no index. The tests now name `{"index": {"bm25": make_index("bm25", ROOT)}}` (`tests/conftest.py`).

### Notes (tutorial changes from the Korean edition's real run, not platform problems)
- The collector copied one long file path wrong (a part of the scratch folder name was dropped) and that article was refused. `news_search` now returns the file name only; `upload` finds a relative name in the block's files folder.
- `query` with a Korean question found no paragraph in an English article (bm25 matches words). The mission now says to ask in the article's language.
- Articles written on Windows have `\r\n` line ends; the paragraph check first missed a whole section (`#1`) because its blank-line rule did not allow `\r`. Fixed in `checks.py` (and a test with `\r\n`).

## nextop 0.4.0.dev6: real run on 2026-11-26 (compiled wheel from the fs-graph branch, a fresh venv per tutorial, gpt-5.4-mini)

Checked: `nextop check` OK, 20 offline tests passed, then one real run with the real Tavily search (the key from the tutorial's `.env`) and a local test mail server (records `runs/20261126-235152-afa0` of the scratchpad copy `phase10en\t02`).

- Verified fixed 1: three times the analyst tried to save all four companies' items in one conversation and the program refused (`This conversation is only about NVIDIA; save only its share. Not taken, each of these has its own conversation: outlook.items`, analyst `tools.jsonl`); the final output has 4 items (3, 2, 3, 3 reasons), none overwritten.
- Verified fixed 2: `get fs://news/005` answers `card` plus `parts`, each paragraph with address and text (`fs://news/005#1.2`). The analyst made 10 `get` and 25 `query` calls.
- Result: 22 model calls (Quinn 3, Dana 19), 92,739 tokens, about 50 s. The mail is in `README.md`.

### New findings (not platform problems)
- The model's habit of saving every company in each conversation costs calls (3 refused saves, then more queries). The mission could say "save only this company's item"; not changed, so this run stays as it was.
- A news page's stored text has no blank lines, so one "paragraph" (`#1.2`) is often the whole article body, with page furniture in front of it for some sites ("2. Best 0% APR Cards. ..."). That is how the tutorial's `paragraphs` splitter and the search text behave, not the platform.
- `grep` with the pattern `NVIDIA|Micron|SpaceX` answered no hits: the tool matches literally unless `regex` is true, and the model did not set it. Not a problem; the parameter description says it.

## nextop 0.4.0.dev9 (branch fs-graph, the new paragraphs splitter, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `20 passed`, one real run with gpt-5.4-mini and Tavily (the key from the Korean
tutorial's `.env`, in the process only; evidence in scratchpad `phase14\realrun\t02_en`).

- Ported from the Korean edition: `parts/splitter/paragraphs.py` is the new nextop example (a block over 800 characters
  is cut at sentence ends into paragraphs of about 400, a fragment under 15 characters that ends no sentence joins its
  neighbour, a long "#" line is text); the tests no longer name the index part (the run adds the default bm25 index by
  itself; this was "4." of the dev6 notes, now used as fixed); the analyst mission says `get` on an article gives all its
  paragraphs with addresses. On this run's 11 articles: 42 paragraphs, longest 710 characters, none over 800, none under
  15.
- The Korean edition's `tavily.com` exclusion is not needed here: `search.include_domains` keeps the search to the US news
  sites of `stocks.json`, and `news_search` drops any other site, so a `tavily.com` profile page never comes in.
- Run: 22 model calls (collector 5, analyst 17), 93,399 tokens, 64.3 s (dev6: 22, 92,739, about 50 s); 3 analyst saves
  refused (another company's items in the conversation); mail sent (README sample replaced with this mail).
- Tutorial notes (not platform): Apple's only article was Yahoo Finance's quote page `finance.yahoo.com/quote/AAPL` (a
  company profile with tables, on an allowed site), so Apple got Flat with one reason saying there is no news, the same
  kind of page the Korean edition excluded as `tavily.com`; two Micron reasons cite one article; some paragraphs still
  carry site furniture at the start ("2. Best 0% APR Cards.").
- No new platform problem.
