# Platform problems found while building tutorial 3

Found with the platform checkout on branch naw-steps (nextop 0.3.0, commit 9a63576, not published yet). Nothing was worked around by changing the platform. Where the tutorial text or code adapts to a problem, it says so below.

## 1. A doc table part: `pdf_get` shows one text, the quote check compares with another (medium)
- Tried: a worker opens a table part of a PDF with `pdf_get` and quotes one row of it, as the guides say ("quote word for word").
- Happened (real run 2026-11-25, local model, `nextop` 0.3.0 checkout): `pdf_get` returns the table as Markdown (`| 3분기 | 3,300 | 5,900 | +27% |`, with the `| --- |` line). The worker quoted that row exactly. The `quotes` check refused it:
  `인용을 원문에서 찾을 수 없습니다: "| 3분기 | 3,300 | 5,900 | +27% |" (summary.tables[0])가 fs://pdf/005의 글에 없습니다. 원문을 글자 그대로 인용하거나 그 주장을 빼 주세요.`
  The check compares with `_part_search_text` (the cells as `3분기 | 3,300 | ...` lines, no outer bars), see `source_text` in `nextop/file_server/__init__.py`.
- Expected: what a worker can read of a part and what the quote check accepts are the same text, or the refusal says which form is meant.
- Reproduce: sync or upload a PDF with a ruled table into a `"media": "doc"` file server, let a worker open the table part and quote a whole row with its bars.
- Tutorial impact (before 3f80f38): medium. The mission and the field description told the worker to quote the text of one cell, without `|`. A model that copies a row still gets a refusal that reads wrong ("not in the text") and loses a round trip.

## 2. A function with FILES_IN gets doc parts only as Markdown files (low)
- Tried: `functions/classify.py` counts rows and columns of each table part.
- Happened: the record rows a function receives (`inputs["files/pdf"]`) have `path`, `region` and `regions`, but not `table.rows`, and the document row has no `doc.meta.pages`. The function parsed the Markdown file of the table part (`table_rows()`) and `intake` counted the pages itself with pypdfium2.
- Expected: a supported way to get the cells and the page count (for example `table` and `doc` on the row, or a helper in `nextop.file_server`). The store's `items/*.json` hold both, but the guides tell nobody to read them.
- Tutorial impact: none since 3f80f38 (parser and page count removed; `classify` uses `table.rows`, `doc.pages`, `figure.width`).

## 3. `pdf_text` names tables and figures `Table 1` / `Figure 1` and does not connect their captions (low)
- Happened: the caption ("표 1. 분기별 방문자와 대출 권수") is a line of the neighbouring text part. The tutorial found it with a small rule in `build_report` (a table's caption is the last line of the text part before it, a figure's the first line of the text part after it, when it starts with 표/그림/Table/Figure).
- Expected: nothing required; a caption link in the reader result would remove the rule. The first text part of a document (the title) has an empty text and only a heading.
- Tutorial impact: none since 3f80f38 (`classify` reads `region.caption`).

## 4. Figures cannot be read, only located (low, known)
- A figure part has an empty `description` until an `image_describe` reader exists. The summarizer therefore describes a figure only from its caption and the text near it, and the tutorial says so.
- Tutorial impact: low.

## 5. The published "nextop 0.2.0" wheel has no `doc` media, no `pdf_text` and no `pdf` extra (blocker for readers until 0.3.0 is released)
- Tried: `pip install "nextop[pdf]"` and `from nextop.parts.reader import pdf_text` with the PyPI wheel.
- Happened: no such extra, no such module (the `quotes` check part and the doc reader exist only on the branch).
- Expected: a release that has them before the tutorial goes on the homepage (README says "nextop 0.3.0 이상"). The tests fall back to the platform checkout (`NEXTOP_SRC`) for our own development, same as tutorials 1 and 2.
- Tutorial impact: high until release.

## 6. `pdf_text` on "Attention Is All You Need" (arXiv 1706.03762v7, 15 pages): several wrong readings (high for this paper)
Found 2026-11-25 with the platform checkout on branch naw-steps (commit 4fa4538). Nothing was worked around in the tutorial; its run just shows the result.
Reproduce (after `python get_paper.py`):
```
import sys; sys.path.insert(0, r"<platform checkout>")
from nextop.parts.reader import pdf_text
g = pdf_text.read("input/attention_is_all_you_need.pdf")
for p in g["parts"]: print(p["kind"], p["pages"], p["title"], p.get("rows") and len(p["rows"]))
```
It gives (with `meta.pages` 15) 32 parts: 24 text, 5 table, 3 figure. What is right and what is not:
- **The real tables are not found (6a).** Tables 1-4 of the paper (pages 6, 8, 9, 10) have no ruled lines (typeset with horizontal rules only), so no table part exists for them. Their rows stay in the text part as lines, and the caption stays in the text (for example the text part of page 8, index 15 counted from 0: `Table2: TheTransformerachievesbetterBLEUscores...` followed by the model rows). The tutorial therefore cannot put Table 1-4 on the A4 page.
- **Five false tables (6b).** Pages 13-15 (attention visualisations, words drawn rotated or reversed) give table parts `Table 1` .. `Table 5` of 3-6 rows and 27-59 columns, made of fragments (`ehT | waL | lliw | reven ...`, `tI | si | ni ...`). They are counted in the classification (표 5개) and are not tables.
- **The vertical arXiv stamp becomes headings (6c).** The sideways text `arXiv:1706.03762v7 [cs.CL] 2 Aug 2023` is read as reversed lines (`3202 guA 2`, `]LC.sc[`, `7v26730.6071:viXra`), is bigger than 1.2 times the body, and so becomes a heading: three text parts on page 1 get these as titles, and every later text part up to page 12 keeps `7v26730.6071:viXra` as its section title. The real headings (`1 Introduction`, `3.5 Positional Encoding`) are bold but the same size as the body, so no heading is found. The summary page shows `쪽 8 · 7v26730.6071:viXra` as the place of a quote.
- **Missing spaces (6d).** In most lines the text has no spaces: `Thedominantsequencetransductionmodelsarebasedoncomplexrecurrent...`, while other lines are fine (`In this work we employ h = 8 parallel attention layers, or heads.`). A worker copies what it sees, so the quotes on the page are unreadable (`basedsolelyonattentionmechanisms,...`). The quote check passes because the same text is on both sides. Probably the word-gap tolerance of the line extraction against this PDF's tight spacing.
- **Figures: partly right (6e).** Figure 1 (page 3, 334x492 px) is cut correctly and its caption is attached (`Figure1: TheTransformer-modelarchitecture.`, again without spaces). Figure 2 (page 4) is two pictures (scaled dot-product, multi-head): the first has the caption, the second is `Figure 3` (a number by position; the paper's Figure 3 is on page 13). Figures 3-5 (page 13-15, attention maps) are not figures but the false tables of 6b. The pictures are cut at 110 dpi, so Figure 1 looks soft on the A4 page.
- **Equations (6f).** The positional-encoding equations of page 6 come out as `PE =sin(pos/100002i/dmodel)` / `(pos,2i)`: subscripts and superscripts are separate lines or glued. Not usable as a quote; no worker should quote an equation.
- **Layout (6g).** The paper is a single column, so column order was not tested; a two-column paper still has to be tried.
- **Page 1 (6h).** The first part is the arXiv permission note without spaces (`Providedproperattributionisprovided,Googleherebygrantspermissionto...`) with an empty title; the title (`Attention Is All You Need`) is the second part, the authors and the abstract follow with the stamp titles.
- Expected: tables without vertical rules found as tables (or not claimed as tables), no table parts from rotated text, a vertical margin stamp not used as a heading, words with their spaces, bold headings of body size, the second picture of a figure not numbered as a new figure.
- Tutorial impact: high for this paper. The summarizer worker is told to skip tables with broken cells or more than 10 columns, and the program check refuses them, so the A4 page of the Attention run shows figures only. The offline sample PDF (`python make_sample_pdf.py`) has ruled tables and shows the table drawing.

## Not a platform problem, for the record
- `reportlab` is not in the `pdf` extra. The tutorial needs it for the A4 page and the sample PDF, so the README says `pip install reportlab`.

## Fixed in 3f80f38 (platform, branch naw-steps, 2026-11-25)
- 1: a table part now has one text for reading (_get), the quote check and grep (the Markdown table); a row quoted as shown passes.
- 2: FILES_IN functions get doc.pages, table.rows/n_rows/n_cols and figure.image/width/height.
- 3 and 4: pdf_text sets the nearest Table/Figure caption as the part title (region.caption); figure descriptions stay empty without an image_describe reader.
- Reportlab: stays out of the pdf extra (reading needs nextop[pdf] only; documented).

## Tutorial refreshed on 3f80f38 (2026-11-25)
- The workarounds for 1, 2 and 3 are removed; a real run with the local model quoted whole table rows and the quote check accepted them. No new platform problem found in this run.

## Fixed in 3ad8486 (platform, branch naw-steps, 2026-11-25)
- 6a: tables without ruled lines are found from the text alignment under their "Table N:" caption (header row and cells kept); the paper's Tables 1-4 are now table parts with their captions.
- 6b, 6c: only upright characters are read, so the rotated attention-map labels give no false tables and the vertical arXiv stamp is gone (no stamp headings).
- 6d: word gaps of 0.15 of the font size or more get a space (`Provided proper attribution is provided, Google hereby ...`).
- 6e: pictures with one caption (or touching) are one figure part: Figure 1 and Figure 2 are one part each. Figures 3-5 are drawings made of lines (vector graphics), not pictures; they are still not figure parts.
- 6f: lines made mostly of math fonts or symbols read as "(equation)" ("(수식)" in a Korean document). Equations themselves are still not read.
- 6h: the permission note and title still come out as the first two parts; headings now include the real section headings (bold of body size, e.g. "1 Introduction", "3.2 Attention"). Author lines at 12 pt still become a heading (not changed).
- Still open: 6g (two-column papers not tried); a bold figure label inside a drawing ("Input-Input Layer5") on pages 13-15 still becomes a heading.

## Found in the real run on 3ad8486 (2026-11-25)
- 7a: superscripts are flattened into the line: "2.3 x 10^19" in Table 2 is read as `2.3 · 1019`, so the table on the A4 page shows 1019 (checked: the cells equal the parsed table, so the loss is in the reader). Suggest: mark a smaller, raised run as a superscript (for example `^19`) or keep the font-size change visible. Reproduce: read pages 8 of the paper and look at Table 2, columns "Training Cost (FLOPs)". Fixed in 7be49ed (nextop pdf_text: raised and lowered runs are read as `10^19` and `x_i`; Table 2 now shows `2.3 · 10^19`). Rerun for real on 7be49ed (2026-11-25): the A4 page shows `2.3 · 10^19`, `1.4 · 10^20`, `9.6 · 10^18`, `3.3 · 10^18`, equal to the parsed cells.
- Nothing else in this run was a platform problem: the 4 tables, 2 figures, section headings and word spaces came out as listed above.

## Found in the real run on 7be49ed (2026-11-25)
- 7b (low): on page 13 (the attention visualisation, rotated words), the new raised/lowered marking turns the figure's word fragments into a heading `In_ttpenutito-nInVipsuuatli zLataioynes r5` (before: `Input-Input Layer5`). It is a text part of 45 characters, not used by the summary. Suggest: no `^`/`_` marking (and no heading) for lines whose characters are rotated or come from inside a figure area. Reproduce: read the paper, list the text parts of page 13. Fixed in 4350f1d (nextop pdf_text: text inside or next to a vector drawing is no longer body text or a heading; page 13 gives no garbled heading).
- 7c (note, not a fault): the author lines now join the title part (`Attention Is All You Need`, 431 characters); text parts went from 45 to 44.

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5 at c9a3cf3, 2026-11-26)

The tutorial now uses a file server with type folders: `types/pages/type.json` (pdf, reader `pdf_text`, the example
`paragraphs` splitter copied to `parts/splitter/paragraphs.py`, `route` of figure parts to `types/figures`, an image
type). `classify` reads the PDF's part tree from the FILES_IN row (`parts`: sections, paragraphs, tables with
`columns`/`rows`, figures with `image`/`width`/`height`, `caption`, `pages`); the report lists each section's paragraph
addresses, and a key point cites one paragraph (`fs://pdf/001#3.1`) with a quote that the `quotes` check finds in that
paragraph. Checked with the compiled wheel in a fresh venv: `nextop check` OK, tests pass, one real run on
`samples/sample_report.pdf` with gpt-5.4-mini (run `20261126-224905-4c43`: 2 model calls, 9,469 tokens, 8.5 s; the
0.3.0 run had 2 calls, 12,090 tokens, 16.6 s). The worker opened the paragraphs by the report's addresses, every quote
passed on the first save, the page is one A4 page with both tables and the figure.

- Issue 2 (FILES_IN gets doc parts only as files): now the part tree comes as data (fs-graph `ba54649`, early finding
  P1). The early 0.4 workaround that read the store's `items/*.json` is not used.
- Issue 4 (figures cannot be read): 0.4.0 has a place for it (a figure type can name a reader that describes the
  picture; the example part is `examples/parts/reader/image_describe.py`). This tutorial keeps the caption rule.
- Issue 1 (table quote text): the quote check still compares a table part with its cells; key points here cite
  paragraphs, and tables are chosen by address only.

### 8. Paragraph text and paragraph addresses do not come together from `get` (medium)
Same as tutorial 2, issue 7: `get` on a section with more than 3 paragraphs gives paragraph cards without text, and on
a smaller one the joined text without the paragraph addresses. This tutorial puts the paragraph addresses into the
report (`sections[].paragraphs`, by the program), so the worker opens a paragraph by address; in the real run it opened
9 nodes for a 2-page report. A long paper means many `get` calls. Cause and suggested fix: tutorial 2, issue 7
(`nextop/file_server/typed.py` `_open_typed`, `LONG_TEXT_PARTS`).

### 9. A test that hands its own adapters gets no default index (low)
Same as tutorial 2, issue 9 (`nextop/runtime/flow.py:139`, `:771`). The tests name the bm25 index part in
`tests/conftest.py`.

## nextop 0.4.0.dev6 (branch fs-graph `044087f`, R1-R8 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev6 in a fresh venv (nextop imported from the installed `.pyd`, no source on the path): `nextop check` OK, tests pass, one real run with gpt-5.4-mini (evidence in scratchpad `phase10ko`).

- 8 (`get` text and addresses not together): fixed in `ccf42ab` (R3), confirmed: `get fs://pdf/001#3` answers `parts`
  `#3.1`, `#3.2` with address and text; a one-paragraph part answers its text. The mission and README now say so.
- 9 (given adapters without index): fixed in `9f2c9c3` (R6); `tests/conftest.py` no longer names the index.
- Run (sample report): 2 model calls, 9,434 tokens, 7.6 s; 7 `get` calls (dev5: 9); 5 key points, every quote passed on
  the first save; A4 page with 2 tables and 1 figure; mail sent (run `20261126-235318-310b`).
- No new platform problem.

## nextop 0.4.0.dev7 (branch fs-graph, F1-F6 fixed, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev7 in a fresh venv (nextop imported from the installed `.pyd`, version
0.4.0.dev7, no source on the path): `nextop check` OK, `19 passed`, one real run with gpt-5.4-mini on the sample report
(evidence in scratchpad `phase11ko\realrun\t03`).

- `parts/splitter/paragraphs.py` is the new example (F2). The sample report's parts and paragraph addresses did not
  move (`#3.1`, `#3.2`, `#7.1`, `#7.2`; the other sections one paragraph each), so the tests and mission are unchanged.
- F4 (table parts give `columns` + `rows`): `build_report` already put `columns` first; the report's tables are
  5 x 4 and 4 x 3 with the header row `분기 | 방문자(명) | 대출(권) | 전년 대비` (tests pass unchanged). No tutorial code reads
  a header from `get(...)["rows"][0]`.
- F3 (page numbers, first-words title): on the paper (read the same way in tutorial 5) no text part is a page number
  and the first part is titled with its first words; the README paper example (0.3.0) already showed a first-words
  title, so it was not changed.
- Run: 3 model calls, 14,507 tokens, 9.7 s (dev6: 2 calls, 9,434 tokens, 7.6 s); 8 `get` calls, 5 key points cite
  paragraphs, every quote passed on the first save; A4 page with 2 tables and 1 figure; mail sent.
- No new platform problem.
