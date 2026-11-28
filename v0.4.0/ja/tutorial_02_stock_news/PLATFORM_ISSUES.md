# Platform issues found while building tutorial 2 (Japanese edition)

Found with nextop 0.3.1 installed from PyPI (`pip install "nextop[pdf,mcp]==0.3.1"` in a fresh venv, no platform checkout on the path). Nothing was worked around by changing the platform. The issues of the other editions are in `../../en/tutorial_02_stock_news/PLATFORM_ISSUES.md` and `../../ko/tutorial_02_stock_news/PLATFORM_ISSUES.md`.

## No new platform problem
- The Japanese language pack (`"language": "ja"`), the persistent news file server with tags and expiry, the tool's read-only file server view, `for_each` steps, the `quotes` check part, `record_address` and `FILES_IN` worked as documented in 11 real runs (2026-11-25, local model, mail sent each time) and in the tests (20 passed).
- In the flow the quote check speaks Japanese: `引用が見つかりません: 「...」（outlook.items[0].reasons[0]）は fs://news/001 のテキストにありません。原文を一字一句そのまま引用するか、その主張を削除してください。`

## Notes (not platform problems)
- `check_part("quotes")` called directly in a unit test (no project context) answers in English (`quote not found: ...`). That is expected: the language comes from the project the core passes in. The flow test asserts the Japanese sentence.
- The `nextop` command line prints English (`OK: stock news outlook (...)`, `[error] adapter llm.default: API key missing ...`) in a Japanese project. The language pack covers what workers read, not the CLI. The README says so.
- The model used for the real runs slips into Chinese, Korean, Russian or English words inside Japanese sentences (for example `之后`, `织み込み`, `언급`, `после`, `foldable`). This is the model, not nextop. The tutorial's own program check (`workers/analyst/checks.py`) sends such sentences back: the sentence must have kana, kanji only from JIS X 0208 (plus a short list of Chinese-only characters that JIS X 0208 has), no Hangul or Cyrillic, and no lower-case English word (names such as NVIDIA, iPhone, HBM stay). In the run shown in the README it sent back 3 saves and the analyst fixed them.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5, 2026-11-26)

The tutorial now uses a file server with one type folder (`types/articles/type.json`: md, the example `paragraphs`
splitter copied to `parts/splitter/paragraphs.py`, `first_sentence` map) and the common tools (`upload`, `query`,
`get`). A reason cites one article paragraph (`fs://news/003#1.2`); the program copies that paragraph into the mail
(the worker no longer types a quote), and `checks.py` checks that the address is one body paragraph the worker may read.
The splitter cuts at headings and blank lines only, so it needs no change for Japanese text (the articles of this
edition are English anyway). Checked with the compiled wheel 0.4.0.dev5 (no source on the path): `nextop check` OK and
the offline tests pass. No real run was made for this Japanese edition. Findings 4-7 below come from the real run of the
Korean edition (numbered 6-9 there; same platform code, same tools).

### 4. A `for_each` conversation can write the items of the other conversations (high)
- Happened: in the judge conversation for the last company the analyst saved `outlook.items` for all four companies; the
  final output held duplicates and the mail took the last copy of each, so the earlier per-company judgments were
  replaced by thin ones written in the last conversation.
- Cause: `nextop/steps.py` `focus_widen`: `mine` takes every item of the narrowed save; only the old items whose key is
  in the focus item's values are dropped, so items of other keys are added again.
- Suggested fix: in a for_each conversation a save may only hold items whose key is one of the focus item's values;
  refuse the others with a sentence the worker can act on.

### 5. `get` gives paragraph text without addresses, or addresses without text (medium)
- Happened: with the paragraph splitter an article is one section `#1` with paragraphs `#1.1 ...`. `get fs://news/001`
  answers one card (`#1`); `get fs://news/001#1` answers the paragraph cards without text (more than 3 paragraphs); a
  short article (3 leaves or fewer) comes as one text with no paragraph addresses. The worker cannot see a paragraph's
  text and its address together except through `query` or by opening every paragraph.
- Cause: `nextop/file_server/typed.py` `_open_typed`: the leaf count (`LONG_TEXT_PARTS` = 3) decides between cards and
  the joined text; the joined text drops the leaf addresses; a node with a single child answers that child's card.
- Suggested fix: decide by the length of the text (not the number of leaves), and when the text is given, give it as its
  leaves `[{"address", "text"}]`; a node with one child opens the child.

### 6. A part address that does not exist is answered as "not a file I own" (low)
- Happened: `get fs://news/001#2` (no such part; the unit is readable) is answered as if the file were not the worker's.
  The worker cannot tell a wrong part from a missing right.
- Cause: `nextop/file_server/typed.py` `_open_typed`: `node_at` gives None for a missing part of a readable unit too, and
  the answer is `file_server_no_access`.
- Suggested fix: when the unit is readable, say the part does not exist and name its top parts (nothing leaks).

### 7. A test that hands its own adapters gets no default index, and no `query` tool, silently (low)
- Happened: tests that call `run_flow(..., adapters={"llm": ...})` leave the analyst without a `query` tool, although
  `nextop run` gives it (the default `bm25` index part is added only when the adapters are built from project.json).
- Cause: `nextop/runtime/flow.py` uses the given adapters as they are; `_index_parts` runs only inside `build_adapters`.
- Suggested fix: add the index parts to given adapters too, or have `nextop check` / the run say which file server has no
  index. The tests now name `{"index": {"bm25": make_index("bm25", ROOT)}}` (`tests/conftest.py`).

### Notes (tutorial changes, not platform problems)
- `news_search` returns the file name only (a long path was copied wrong by a model in the Korean run); `upload` finds a
  relative name in the block's files folder.
- `query` matches words: the analyst mission says to ask in the article's language (English here).
- Articles written on Windows have `\r\n` line ends; the paragraph check allows them (`\n\s*\n`).

## Phase 10: real run with the compiled wheel 0.4.0.dev6 and gpt-5.4-mini (2026-11-26)

Fresh venv with only the wheel (loads from `site-packages`, `.pyd`, 0.4.0.dev6), real Tavily search, local test SMTP. Records: `C:\Users\SHK\AppData\Local\Temp\claude\61d2a55c1c8ed559\7801ea38-cfcd-4c6c-a551-04091160998b\scratchpad\phase10ja\t02\runs\20261126-234911-4d1b` (18 model calls, 87,346 tokens, 60.6 s; the 0.4.0.dev5 Korean run had 20 calls and 72,621 tokens).

Status of the earlier items:
- Item 4 (`for_each` conversation writes the other items): fixed. The SpaceX conversation tried to save all four companies and the program refused it: `この会話は スペースX だけを扱います。その分だけを保存してください。...` (`blocks/analyst/attempt-1/tools.jsonl`); the next save held only SpaceX, and the mail has four companies with their own reasons.
- Item 5 (`get` text without addresses): fixed. `get fs://news/001` returns `{"card", "parts": [{"address": "fs://news/001#1.1", "text": ...}, ...]}`; the reasons cite paragraph addresses such as `fs://news/002#1.2` and the program copies the paragraph into the mail.
- Item 6 (missing part answered as "not a file I own"): not exercised in this run.
- Item 7 (no default `query` for given adapters): fixed in the platform; the tests pass (20).

New observations (not platform bugs):
- `query` with a Japanese question over an English article can return nothing (`passages: []`, "この索引には質問に合うものがありません。推測しないでください。"; three Micron articles) while the same kind of question found paragraphs for the SpaceX articles. The mission already asks for the question in the article's language; the model wrote Japanese anyway. The note in the answer is good: it made the model open the article with `get` instead.
- A cited paragraph can be page furniture that the search service put into the article text (`2. Best 0% APR Cards.`, `increase; green up pointing triangle`). The program copies it as it is. Cleaning articles belongs to `news_search` or the splitter of this project, not to the platform.
- The mission says to use different paragraphs when one article is used twice; for Apple (one article) both reasons cite `fs://news/010#1.2` and nothing refused it. Not checked by the program on purpose (no extra checks).

## nextop 0.4.0.dev9 (branch fs-graph, the new paragraphs splitter, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `20 passed`, one real run with gpt-5.4-mini and Tavily (the key from the Korean
tutorial's `.env`, in the process only; evidence in scratchpad `phase14\realrun\t02_ja`).

- Ported from the Korean edition: `parts/splitter/paragraphs.py` is the new nextop example; the tests no longer name the
  index part (the run adds the default bm25 index by itself); the analyst mission says `get` on an article gives all its
  paragraphs with addresses. On this run's 6 articles: 19 paragraphs, longest 659 characters, none over 800, none under
  15.
- The Korean edition's `tavily.com` exclusion is not needed here: `search.include_domains` keeps the search to the US news
  sites of `stocks.json`, and `news_search` drops any other site.
- Run: 27 model calls (collector 4, analyst 23), 120,713 tokens, 56.5 s; 4 analyst saves refused (another company's
  items 3 times, 3 reasons for a "thin" company once); mail sent in Japanese (no Korean letters; the cited paragraphs are
  the English articles' own text). README sample replaced with this mail.
- Tutorial notes (not platform): each company's two reasons often cite the same paragraph (Apple, Micron; the mission
  asks for different paragraphs, not checked).
- No new platform problem.
