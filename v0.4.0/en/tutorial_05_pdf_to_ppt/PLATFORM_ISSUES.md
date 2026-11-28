# Platform issues found while building tutorial 5 (English edition)

Found with nextop 0.3.0 installed from PyPI (`pip install "nextop[pdf]==0.3.0"` in a fresh venv, no platform checkout on the path). Nothing was worked around by changing the platform. The issues found while building the Korean edition (on the platform branch before the release; both fixed in 4350f1d, which is in 0.3.0) are in `../../ko/tutorial_05_pdf_to_ppt/PLATFORM_ISSUES.md`.

## No new platform problem
- The English language pack, the doc file server and `pdf_text` (Figures 1 and 2 cut at their own resolution, 911×1343 and 1216×769, with whole captions), `FILES_IN` / `FILES_OUT`, the `quotes` check part (also on quotes nested in `slides[].columns[].bullets[]`) and the flow check worked as documented in the real run (2026-11-25, local model, 9 model calls, about 131 s, mail sent) and in the 21 tests.
- The quote check's message follows the project's language: `quote not found: "..." (writing.slides[10].bullets[1]) is not in the text at fs://pdf/043. Quote the source word for word, or remove the claim.`

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)

The tutorial now uses the same file server as tutorial 3 (type folders `pages` and `figures`, the example `paragraphs` splitter in `parts/splitter/`); `classify` reads the part tree from the FILES_IN row, the report lists each section's paragraphs, a bullet cites one paragraph of its slide's parts and its quote is checked in that paragraph; the speaker notes name the paragraph's section and page (`_deck.compose`). Checked with the compiled wheel 0.4.0.dev5 in a fresh venv: `nextop check` OK and `21 passed`. The real run of the Korean edition (`../../ko/tutorial_05_pdf_to_ppt/PLATFORM_ISSUES.md`) on the paper made 9 model calls; this English edition was not run against a real model for 0.4.0.

### 1. Paragraph text and paragraph addresses do not come together from `get` (medium) - fixed in 0.4.0.dev6, verified in the real run
Same as tutorial 2, issue 2. In the Korean edition's real run the writer made 58 `get` calls (sections, then their paragraphs one by one), cited a whole section once (its text came joined, without the paragraph addresses) and was sent back with the list of its paragraphs. Cause and suggested fix: tutorial 2, issue 2 (`nextop/file_server/typed.py` `_open_typed`).

### 2. A test that hands its own adapters gets no default index (low)
Same as tutorial 2, issue 4. The tests name the bm25 index part in `tests/conftest.py`.

### Notes (not platform problems, from the Korean edition's real run)
- The 2-page sample report gives `slides 7, sections 2`: only one outline fits (cover, agenda, section, content, section, content, closing). The model missed it 10 times and the planner stopped. The paper (12 slides) works. A change for later: let intake give one section for a short document, or say the one fitting order in the brief.
- After a refusal ("not a paragraph of this slide's parts") the writer once kept its point and moved the citation to a paragraph of the slide that does not say it. The program checks that the quote is in the paragraph, not that it supports the point.

## nextop 0.4.0.dev6: real run on 2026-11-26 (compiled wheel from the fs-graph branch, a fresh venv per tutorial, gpt-5.4-mini)

Checked: `nextop check` OK, 21 offline tests passed, then one real run (the paper, Basic theme, local test mail server; scratchpad `phase10en\t05`) and `render_deck.py` for Dark and Academic.

- Verified fixed: the writer's `get` on a section answered `parts` with each paragraph's address and text. The writer made 28 `get` calls (the Korean edition on 0.4.0.dev5: 58), no `query`.
- Result: 13 model calls (Harper 5, Sage 8), 215,824 tokens, about 76 s, 12 slides, `.pptx` and PNGs made, mail made. Harper was sent back 4 times (slide count, table rows, columns, height); Sage 4 times (slide count, paragraphs of another slide, a one-bullet closing slide twice).

### New findings (not platform problems)
- Some paragraphs of the paper are one character long (for example `fs://pdf/001#6.2`, `#10.2`, `#35.3`) or a few characters (`#33`: 11); probably page furniture or a stray symbol read as a paragraph (cause not investigated). The writer opens them and could cite them. A reader or splitter detail.
- Model behaviour: Harper chose Table 2 rows of the baseline models, not the Transformer's own rows, so the slide's bullets (28.4 and 41.0 BLEU) are not in the table shown; the program checks addresses and sizes, not that the rows fit the point.
- Model behaviour: after reading the sections with `get`, the writer opened single paragraphs again (`#5.1`, `#9.1`, `#43.1`, ...), calls that were not needed.

## nextop 0.4.0.dev9 (branch fs-graph, one slide per writer conversation, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `29 passed`, three real runs on the paper with gpt-5.4-mini, Basic theme
(evidence in scratchpad `phase14\realrun\t05_en_*`).

- Ported from the Korean edition: the writer writes and saves one slide per conversation (split block
  `functions/split_slides.py` per outline slide, gather keeps the order, a refused slide is redone alone); the planner's
  check asks a table or figure slide to rest on a text part that talks about it (`text_parts`, found by `classify`); a
  slide naming one piece of a section gets the whole section (`pieces`, `_deck.whole_sections`); short documents get one
  section; section pieces carry their slides' topics (`covers`); the paragraphs splitter is the new nextop example; tests
  use the run's default index. The caption label of `text_parts` matches `Table|Figure|Fig.` (the Korean `표|그림` are
  left out here).
- Runs: 1) stopped in the planner after 10 refused saves (138,037 tokens, 42.9 s): Harper put the second section just
  before the closing ("slides[10] is a section; the next slide must be a content slide") and then fell back to one
  section ("the outline has 1 section slides; brief.sections is 2"), back and forth, until the limit; 2) 30 calls,
  145,524 tokens, 43.6 s, passed; 3) 34 calls, 160,990 tokens, 42.2 s, passed. In 2 and 3 Sage's refused saves (3 on 2 slides, 5 on 4
  slides: bullet counts, one paragraph outside the slide, columns on a table slide, one bullet too long) were redone alone, and
  every slide sat in its outline place. The Korean edition had 5 of 5 passing runs on this paper.
- Tutorial notes (not platform): run 1 is a planner task problem (the check says what is wrong but not where the second
  section can go; the Korean edition did not meet it); in run 2 the cover subtitle repeated the document title (the
  mission says not to) and the second section's title did not match its slides.
- No new platform problem.
