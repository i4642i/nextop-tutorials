# Platform problems found while building tutorial 5

Found with the platform checkout on branch naw-steps (nextop 0.3.0, commit 7be49ed, not published yet). Nothing was worked around by changing the platform. Where the tutorial adapts to a problem, it says so below.

## 1. Figure pictures are cut at a fixed 110 dpi: blurry on a slide (medium for this tutorial) Fixed in 4350f1d (nextop pdf_text: a figure that is one raster picture is cut at its own resolution, 150 to 300 dpi, longest side at most 3000 px; Figure 2 is now 1216 x 769, Figure 1 911 x 1343). The example decks were drawn again from the saved plan with the new pictures.
- Tried: the program puts a figure part's picture (`figure.image`) on a 16:9 slide, in a 500 x 330 point card.
- Happened (real run 2026-11-25, Attention paper): Figure 2 is 446 x 282 pixels (`RESOLUTION = 110` in `nextop/parts/reader/pdf_text.py`). On the slide it is drawn about 476 points wide, so a full-screen show (about 2 pixels per point) stretches it about 2x: the small labels of the drawing ("Scaled Dot-Product Attention", "MatMul") look soft. Figure 1 (334 x 492) is drawn near its own size and looks fine.
- Expected: a way to get a sharper picture of a figure part, for example a reader setting for the resolution, or the figure's page and box in the record so a function can cut it again at the size it needs.
- Reproduce: read the paper with `pdf_text`, open the figure part of Figure 2 (page 4) and look at its size.
- Tutorial impact: medium. The figure is readable but not crisp; nothing was changed in the tutorial.

## 2. A caption is cut at the end of its first line (low) Fixed in 4350f1d (the whole caption paragraph is read; the Figure 2 slide now shows the full caption).
- Happened: Figure 2's caption is `Figure 2: (left) Scaled Dot-Product Attention. (right) Multi-Head Attention consists of several` (the paper goes on: "attention layers running in parallel."). The slide shows the caption as the reader gives it, so it ends in the middle of a sentence. Tutorial 3 shows the same caption.
- Expected: the whole caption (all its lines), or the caption line marked as cut.
- Reproduce: read the paper with `pdf_text` and look at `region.caption` of the figure part on page 4.
- Tutorial impact: low (one caption reads unfinished).

## 3. Nothing else
- The doc file server, `pdf_get`, the quote check (`check_part("quotes")`, also on quotes nested in `slides[].columns[].bullets[]`), `FILES_IN`/`FILES_OUT` and the flow check worked as documented. Table cells with powers (`2.3 · 10^19`) came through as the reader writes them and are shown that way.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)

The tutorial now uses the same file server as tutorial 3 (type folders `pages` and `figures`, the example `paragraphs`
splitter in `parts/splitter/`); `classify` reads the part tree from the FILES_IN row, the report lists each section's
paragraphs, a bullet cites one paragraph of its slide's parts and its quote is checked in that paragraph; the speaker
notes name the paragraph's section and page (`_deck.compose`). Checked with the compiled wheel in a fresh venv:
`nextop check` OK, `21 passed`, one real run on the paper, basic theme (run `20261126-225146-eaaf`: 9 model calls,
168,541 tokens, 55.9 s; the 0.3.0 runs had 6 to 11 calls, 111,309 to 223,970 tokens). Issues 1 and 2 above stay fixed
(Figure 1 and 2 on their slides are sharp, the Figure 2 caption is whole).

### 3. Paragraph text and paragraph addresses do not come together from `get` (medium)
Same as tutorial 2, issue 7. In the real run the writer made 58 `get` calls (sections, then their paragraphs one by one), cited a
whole section `fs://pdf/001#9` once (its text came joined, without the paragraph addresses) and was sent back with the
list of its paragraphs. Cause and suggested fix: tutorial 2, issue 7 (`nextop/file_server/typed.py` `_open_typed`).

### 4. A test that hands its own adapters gets no default index (low)
Same as tutorial 2, issue 9. The tests name the bm25 index part in `tests/conftest.py`.

### Notes (not platform problems)
- The 2-page sample report gives `slides 7, sections 2`: only one outline fits (cover, agenda, section, content, section,
  content, closing). gpt-5.4-mini missed it 10 times and the planner stopped (run in scratchpad
  `phase9\realrun\t05_sample_failed`, 53,989 tokens). The paper (12 slides) works. A change for later: let intake give
  one section for a short document, or say the one fitting order in the brief.
- After a refusal ("not a paragraph of this slide's parts") the writer once kept its point and moved the citation to a
  paragraph of the slide that does not say it (slide 7, bullet 3 "포지셔널 인코딩은 순서 정보를 넣습니다" cites "Motivating our use
  of self-attention we consider three desiderata."). The program checks that the quote is in the paragraph, not that
  it supports the point.

## nextop 0.4.0.dev6 (branch fs-graph `044087f`, R1-R8 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev6 in a fresh venv (nextop imported from the installed `.pyd`, no source on the path): `nextop check` OK, tests pass, one real run with gpt-5.4-mini (evidence in scratchpad `phase10ko`).

- 3 (`get` text and addresses not together): fixed in `ccf42ab` (R3), confirmed: a part's `get` answers its paragraphs
  with address and text. In the passing run the writer opened 69 paragraph addresses in one turn and saved once: writer
  2 model calls, 36,335 tokens (dev5: 6 calls, 135,534 tokens, 58 `get`).
- 4 (given adapters without index): fixed in `9f2c9c3` (R6); `tests/conftest.py` no longer names the index.
- Run (paper, basic theme): 5 model calls (planner 3, writer 2), 68,984 tokens, 41.3 s; 12-slide .pptx, previews and
  mail OK (run `20261127-000306-42e1`).
- Three runs before it stopped in the writer (tutorial task problems, fixed in the tutorial): a skipped slide shifted
  the rest by one (`t05_failed_shift`); 9 of 12 slides written again and again (`t05_failed_nine`); the planner gave the
  pieces of one section (6.2, cut at a page break into `#35`, `#36`, `#38`) to two slides, so the writer could not cite
  the paragraphs it needed (`t05_failed_parts`). Now each written slide carries its outline number `no` (a missing number
  is named with its layout and topic), and a bullet may cite any piece of the same section as its slide's parts.

### New: a run that ends on nudges names only the nudges, not the refused saves (low)
- Happened (writer): 9 saves were refused by the program checks; between them the model answered 4 times with text
  only ("저장에 실패했습니다 ..."). The 4th text-only answer ended the work with "the LLM did not call any tool"; the reason
  does not say that 9 saves were refused or what was still wrong.
- Evidence: scratchpad `phase10ko\realrun\t05_failed_nine\runs\20261126-235649-4147\blocks\writer\attempt-1\status.json`
  and `calls.jsonl` (calls 11, 15, 17, 19 have no tool call; each came after a refused save).
- Cause: `nextop/runtime/react.py:271` (`nudges = 0` once per run, never reset after a tool call) and `:333-335` (the
  failure reason).
- Suggested fix: count text-only answers in a row (reset after any tool call), and when the work stops on nudges after
  refused saves, add the refusal count and the last problems to the reason (as the check_limits failure at `:388` does).

### New: a save that is the same as the refused one gets the same answer, with no word that nothing changed (low)
- Happened (writer): saves 6 and 7, 10 and 12, 13 and 14 were the same as the save just refused; each got the same
  problem list, and the 10 refusals ran out.
- Evidence: scratchpad `phase10ko\realrun\t05_failed_shift\runs\20261126-235350-f583\blocks\writer\attempt-1\tools.jsonl`
  (`save_output` arguments of those calls are equal).
- Cause: `nextop/runtime/react.py:385-397` (the refusal path sends `not_saved` + problems only).
- Suggested fix: when a save equals the previous refused save, say so in the answer ("this save is the same as the one
  refused before: change the fields named below"), so the model does not spend its refusals on repeats.

## nextop 0.4.0.dev7 (branch fs-graph, F1-F6 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev7 in a fresh venv (nextop imported from the installed `.pyd`, version
0.4.0.dev7, no source on the path): `nextop check` OK, `22 passed`, three real runs with gpt-5.4-mini on the paper,
basic theme (evidence in scratchpad `phase11ko\realrun`).

- `parts/splitter/paragraphs.py` is the new example (F2) and `pdf_text` drops page numbers and running heads (F3): in
  the classification report no text part is a page number any more; the only part under 15 characters is `#33`
  "6 Results" (a heading-only section, 11 characters); the first part's title is its first words ("Provided proper
  attribution is provided, Google hereby") instead of "(no title)". Table parts give `columns` + `rows` (F4); the
  report's tables keep their header row and row counts (tests pass unchanged).
- Run 3 (`t05`): passed. 9 model calls (planner 2, writer 7), 164,852 tokens, 56.1 s; 12 slides, previews and mail
  OK; 4 writer saves (3 refused: bullets citing paragraphs outside the slide's parts, one quote not in the paragraph),
  every quote in the final deck found in its paragraph (dev6 passing run: 5 calls, 68,984 tokens, 41.3 s).
- Run 1 (`t05_failed_parts`, writer stopped after 10 refused saves, 424,011 tokens): the planner gave the Table 1
  slide (layer complexity) the part `#14` (3.2.1 Scaled Dot-Product Attention) instead of `#23`/`#24` (4 Why
  Self-Attention, the section that discusses Table 1), so the writer could not cite the paragraphs it needed; it also
  put bullets on a section slide. Tutorial task problem (planner part choice), not platform.
- Run 2 (`t05_failed_shift`, stopped after 10 refused saves, 515,465 tokens): the writer's content was shifted by one
  slide from slide 6 on (each `no` present 1-12, but slide 6 had the section slide's empty bullets and slide 7 the
  table slide's bullets). The `no` field from phase 10 catches a missing number, not shifted content. Tutorial task
  problem (one save for 12 slides), not platform.
- F5 (nudges in a row) and F6 (unchanged save) were not met: no run ended on text-only answers, and no save repeated
  the refused one.
- No new platform problem.

## Writer reliability: one slide per conversation (2026-11-27, nextop 0.4.0.dev7) - handled in the tutorial

The writer stops of phases 10 and 11 (`t05_failed_shift`, `t05_failed_nine`, `t05_failed_parts`, and the two dev7
failures above) are **handled**. They were tutorial task problems, not platform problems: one save held all 12 slides,
so one wrong slide refused all of them and the model rewrote everything; and a planner mistake (the Table 1 slide on
`#14`) reached the writer, who cannot change the outline.

- Why it showed up in 0.4.0 and not (visibly) in 0.3.x: 0.4.0 made bullets cite paragraph addresses inside the
  slide's own sections (0.3.x accepted a section address), and the new paragraph splitter plus page-break handling cut
  one section into several pieces (for example `#35`, `#36`, `#38`). Both are intended changes, but together they made
  the one-save-for-12-slides design fail much more often (dev5: sample failed; dev6: 3 failures before a pass; dev7: 2
  failures before a pass). How many 0.3.x runs failed is not recorded; the README only kept successful runs.
- The flow is now `intake -> classify -> planner -> split -> writer (one copy per slide) -> gather -> deliver`. The
  split function `functions/split_slides.py` (`KIND = "split"`, terminal `slide`) cuts the outline into one piece per
  slide; each writer copy writes and saves one slide with its own checks; a refused slide is redone alone; `gather`
  gives the slides back in outline order. Platform features used as documented (manual, "Parallel sections: split and
  gather"); nothing was worked around.
- The planner's check refuses a table or figure slide whose parts do not include one of the text parts that talk about
  it (`report.tables[].text_parts`, found by `classify`). A slide that names one piece of a section cut at a page break,
  table or figure gets the whole section (`report.sections[].pieces`, `_deck.whole_sections`). A first version refused
  the planner until it named every piece; in run 2 the planner failed to fix that one point 7 saves in a row, so the
  program now adds the pieces.
- Short documents get one section (`_deck.amounts`): the 2-page sample now passes (the earlier "Notes" item).
- Runs (gpt-5.4-mini, scratchpad `t05split`): paper, basic theme, 5 of 5 passed (the last 3 on the final code: 31,
  31, 36 calls; 162,155 / 133,814 / 163,833 tokens; 45.4 / 34.2 / 36.1 s); sample report, dark theme, passed (13
  calls, 39,946 tokens, 12.2 s). Before the one-section change the sample stopped in the planner after 10 refused
  saves (`t05_sample_failed`).
- No new platform problem was found. Each copy's records are in `runs/<id>/blocks/writer@<n>/`, and `cost.json` lists
  the copies one by one as documented.
- Checks: `nextop check` OK (`OK: pdf to ppt (workers 2, tools 0, flows 1, file servers 1)`), tests `29 passed`
  (compiled wheel 0.4.0.dev7 in a venv).
