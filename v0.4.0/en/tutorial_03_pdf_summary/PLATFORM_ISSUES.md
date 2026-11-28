# Platform issues found while building tutorial 3 (English edition)

Found with nextop 0.3.0 installed from PyPI (`pip install "nextop[pdf]==0.3.0"` in a fresh venv, no platform checkout on the path). Nothing was worked around by changing the platform. The issues found while building the Korean edition (on the platform branch before the release), with what was fixed and what is still open for the PDF reader, are in `../../ko/tutorial_03_pdf_summary/PLATFORM_ISSUES.md`.

## No new platform problem
- The English language pack, the doc file server and `pdf_text` (the paper: 43 text parts, Tables 1-4 with captions, Figures 1 and 2 at their own resolution with whole captions), `FILES_IN` / `FILES_OUT`, the `quotes` check part and `record_address` worked as documented in the real runs (2026-11-25, local model: paper 7 model calls, made-up report 3, both mailed) and in the tests.
- The quote check's message follows the project's language: `quote not found: "..." (summary.key_points[0]) is not in the text at fs://pdf/003. Quote the source word for word, or remove the claim.`

## Note for the Korean edition
- On PyPI 0.3.0 the paper gives 43 text parts (the Korean edition's README, written on the platform branch at 7be49ed, says 44) and Figure 1 / Figure 2 are 911×1343 and 1216×769 pixels (4350f1d cut them at their own resolution). The Korean edition was run again on 0.3.0; its README has the new numbers.

## Not a platform problem, for the record
- A mail subject with a non-ASCII separator (`·`) came back from Python's own mail parser with an extra space before it in the test (`parts  · 2 tables`): the encoded words of the header were folded next to plain words. The English edition uses plain ASCII subjects (`(43 text parts, 4 tables, 2 figures)`); the body keeps `·`.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)

The tutorial now uses a file server with type folders: `types/pages/type.json` (pdf, reader `pdf_text`, the example `paragraphs` splitter copied to `parts/splitter/paragraphs.py`, `route` of figure parts to `types/figures`, an image type). `classify` reads the PDF's part tree from the FILES_IN row (`parts`: sections, paragraphs, tables with `columns`/`rows`, figures with `image`/`width`/`height`, `caption`, `pages`); the report lists each section's paragraph addresses, and a key point cites one paragraph (`fs://pdf/001#3.1`) with a quote that the `quotes` check finds in that paragraph. Checked with the compiled wheel 0.4.0.dev5 in a fresh venv: `nextop check` OK and the offline tests pass. The real run of the Korean edition (`../../ko/tutorial_03_pdf_summary/PLATFORM_ISSUES.md`) on `samples/sample_report.pdf` needed 2 model calls, and every quote passed on the first save; this English edition was not run against a real model for 0.4.0.

- The part tree now comes to a FILES_IN function as data (`parts`), not as files; the tutorial reads no store files.
- A model cannot read a figure yet; 0.4.0 has a place for it (a figure type can name a reader that describes the picture; the example part is `examples/parts/reader/image_describe.py`). This tutorial keeps the caption rule.
- The quote check still compares a table part with its cells; key points here cite paragraphs, and tables are chosen by address only.

### 1. Paragraph text and paragraph addresses do not come together from `get` (medium) - fixed in 0.4.0.dev6, verified in the real run
Same as tutorial 2, issue 2: `get` on a section with more than 3 paragraphs gives paragraph cards without text, and on a smaller one the joined text without the paragraph addresses. This tutorial puts the paragraph addresses into the report (`sections[].paragraphs`, by the program), so the worker opens a paragraph by address; in the real run of the Korean edition it opened 9 nodes for a 2-page report. A long paper means many `get` calls. Cause and suggested fix: tutorial 2, issue 2 (`nextop/file_server/typed.py` `_open_typed`, `LONG_TEXT_PARTS`).

### 2. A test that hands its own adapters gets no default index (low)
Same as tutorial 2, issue 4 (`nextop/runtime/flow.py:139`, `:771`). The tests name the bm25 index part in `tests/conftest.py`.

## nextop 0.4.0.dev6: real run on 2026-11-26 (compiled wheel from the fs-graph branch, a fresh venv per tutorial, gpt-5.4-mini)

Checked: `nextop check` OK, 19 offline tests passed, then two real runs: the made-up report (scratchpad `phase10en\t03_sample`) and the paper (`phase10en\t03`), with a local test mail server.

- Verified fixed: `get fs://pdf/001#3` on a section answers `{"card": ..., "parts": [{"address": "fs://pdf/001#3.1", "text": ...}, ...]}`; a part without sub-parts answers one object with `text`, `section`, `pages`, `format` and `original` (the unit address, no local path). The summarizer made 9 `get` calls (sample) and 10 (paper), no `query`.
- Result: sample 3 model calls, 13,444 tokens, about 10 s, passed at the first save; paper 7 model calls, 91,838 tokens, about 21 s, one A4 refusal then passed; every quote was checked against its paragraph. The mail and the summary PDFs are in `README.md` and `example_output/`.

### New findings (not platform problems)
- The first text part of the paper (the Google permission note on page 1) now has no title in the report (`(no title)`); in the 0.3.0 run its first words were the title. Low.
- Table 2 and Table 3 of the paper still have empty header cells (`columns:  | BLEU | ...`); the summary draws them as they are.

## nextop 0.4.0.dev9 (branch fs-graph, the new paragraphs splitter, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `19 passed`, one real run on the paper with gpt-5.4-mini (evidence in scratchpad
`phase14\realrun\t03_en`).

- Ported from the Korean edition: `parts/splitter/paragraphs.py` is the new nextop example; the tests no longer name the
  index part (the run adds the default bm25 index by itself). The sample report's addresses did not move, so the tests and
  the mission are unchanged.
- Run: 4 model calls, 49,363 tokens, 27.5 s (dev6: 7 calls, 91,838 tokens, about 21 s); 8 `get` calls; first save past one
  page by about 1,586 characters, second passed; 3 key points citing paragraphs, every quote passed; Table 2 and Table 4,
  no figure; mail sent.
- No new platform problem.
