# チュートリアル 3 を作る中で見つけたプラットフォームの問題（日本語版）

PyPI からインストールした nextop 0.3.1 で見つけたものです（新しい venv で `pip install "nextop[pdf,mcp]==0.3.1"`、パスにプラットフォームのチェックアウトなし）。プラットフォームを変えて回避したものはありません。英語版と韓国語版で見つかった問題は `../../en/tutorial_03_pdf_summary/PLATFORM_ISSUES.md` と `../../ko/tutorial_03_pdf_summary/PLATFORM_ISSUES.md` にあります。

## 1. 引用の検査（`quotes`）が日本語の行の変わり目で一致しない
- 試したこと: 日本語の PDF（`make_sample_pdf.py` の架空の報告書）を `pdf_text` で読み、行をまたぐ文を引用として `check_part("quotes")` で検査する。
- 起きたこと: `pdf_text` は段落の中の行を `\n` でつなぐ（`…満足度が最も高かっ\nた。`）。`quotes` は空白と改行の並びを一つの空白にしてから比べる（`alike`）ので、原文は `高かっ た。` になり、正しく写した引用 `高かった。` が「引用が見つかりません」で差し戻される。英語や韓国語は単語の間で改行されるので起きないが、空白なしで続く日本語（と中国語）では文の途中のどこでも起きる。
- 期待: 日本語の文字（仮名、漢字、全角の記号）の隣の改行は、比べる前に取り除く（またはプロジェクトの言語が ja のとき、`pdf_text` が段落の中の行を空白なしでつなぐ）。
- 再現: `python make_sample_pdf.py` のあと
  `python -c "from nextop.parts import check_part; from nextop.parts.reader import pdf_text; t=pdf_text.read('samples/sample_report.pdf')['parts'][1]['text']; S=type('S',(),{'text':lambda self,a:t}); print(check_part('quotes')({'k':{'source':'fs://pdf/003','quote':'本報告書では、四半期ごとの利用状況、月ごとの来館者数'}}, S()))"`
  → `quote not found: "本報告書では、四半期ごとの利用状況、…" (k) is not in the text at fs://pdf/003. …`（原文は `四\n半期`）
- チュートリアルへの影響: チュートリアルの中で回避しました。`workers/summarizer/checks.py` が引用と原文の両方に `functions/_pdf.py` の `joined`（日本語の文字の隣の空白と改行を取り除く）をかけてから `quotes` に渡します。実際の実行（2026-11-25、架空の報告書）で、そらの引用「参加者アンケートでは、読み聞かせの会の満足度が最も高かった。」は原文で `高かっ\nた。` と改行されていて、この回避で通りました。テスト: `test_a_quote_across_a_line_break_of_the_page_passes`。

## 2. メモ: 言語の検査は各チュートリアルが書く
- 英語版と韓国語版と同じく、「書いた文がその言語か」はチュートリアルの `checks.py` が検査します。日本語版では、仮名のない文、韓国語の文字、日本語の文字集合（cp932）にない漢字を差し戻します（`language_errors`）。実際の実行ではモデルが中国語を混ぜることが多く（論文で 5 回中 4 回）、`头`、`络` は差し戻せましたが、`網絡`、`首个` のように cp932 にもある字は文字だけでは見分けられませんでした。プラットフォームの問題ではありませんが、日本語の言語パックや公式の検査パーツに「文の言語」の検査があれば、各チュートリアルが書かずに済みます。

## 問題なし
- 日本語の言語パック（`"language": "ja"`）: 検査の差し戻し（`必須項目「title」がありません`、`引用が見つかりません: …`）が日本語で出ました。
- `pdf_text` は日本語の PDF を英語版と同じ順番の部分（本文 7、表 2、図 1）に読み、`表1.`、`図1.` のキャプションを表と図に付け、日本語の見出し（`1. 概要`）を本文の部分のタイトルにしました。論文は英語版と同じく本文 43、表 4、図 2 です。
- doc ファイルサーバー、`FILES_IN` / `FILES_OUT`、`record_address`、フローの検査は、実際の実行（2026-11-25、ローカルモデル。論文 5 回、架空の報告書 1 回、すべてメール送信まで）とテストで説明どおりに動きました。
- 日本語の件名（`[PDF要約・テスト] … の A4 要約（本文 7、表 2、図 1）`）と日本語の添付ファイル名（`要約_sample_report.pdf`）は、テストのメールサーバーで送ったとおりに読めました。

## nextop 0.4.0 (branch fs-graph, wheel 0.4.0.dev5, 2026-11-26)

The tutorial now uses a file server with type folders: `types/pages/type.json` (pdf, reader `pdf_text`, the example
`paragraphs` splitter copied to `parts/splitter/paragraphs.py`, `route` of figure parts to `types/figures`, an image
type). `classify` reads the PDF's part tree from the FILES_IN row (`parts`: sections, paragraphs, tables with
`columns`/`rows`, figures with `image`/`width`/`height`, `caption`, `pages`); the report lists each section's paragraph
addresses, and a key point cites one paragraph (`fs://pdf/001#3.1`) with a quote that the `quotes` check finds in that
paragraph. The splitter cuts at blank lines only, so it works on Japanese paragraphs as it is. Checked with the compiled
wheel 0.4.0.dev5 (no source on the path): `nextop check` OK and the offline tests pass. No real run was made for this
Japanese edition.

- Issue 1 above (the `quotes` check does not match across a Japanese line break) is fixed in 0.4.0.dev5: with the
  tutorial's `joined` workaround removed, the test `test_a_quote_across_a_line_break_of_the_page_passes` still passes at
  the first save (the paragraph text still holds `四\n半期`). The workaround (`joined`, `JoinedSources`) and its unit test
  are removed from `functions/_pdf.py`, `workers/summarizer/checks.py` and `tests/`.
- Issue 2 (FILES_IN gets doc parts only as files): now the part tree comes as data (`parts`).

### 3. Paragraph text and paragraph addresses do not come together from `get` (medium)
Found in the Korean edition (its issue 8). `get` on a section with more than 3 paragraphs gives paragraph cards without
text, and on a smaller one the joined text without the paragraph addresses. This tutorial puts the paragraph addresses
into the report (`sections[].paragraphs`, by the program), so the worker opens a paragraph by address. A long paper means
many `get` calls. Cause and suggested fix: `nextop/file_server/typed.py` `_open_typed` (`LONG_TEXT_PARTS`): decide by the
length of the text, and give the text as its leaves `[{"address", "text"}]`.

### 4. A test that hands its own adapters gets no default index (low)
Found in the Korean edition (its issue 9). `nextop/runtime/flow.py` uses the given adapters as they are; the default
`bm25` index part is added only when the adapters are built from project.json. The tests name the bm25 index part in
`tests/conftest.py`.

## Phase 10: real run with the compiled wheel 0.4.0.dev6 and gpt-5.4-mini (2026-11-26)

Fresh venv with only the wheel (`site-packages`, `.pyd`, 0.4.0.dev6). Paper run: `C:\Users\SHK\AppData\Local\Temp\claude\61d2a55c1c8ed559\7801ea38-cfcd-4c6c-a551-04091160998b\scratchpad\phase10ja\t03\runs\20261126-234910-91ca` (4 model calls, 53,642 tokens, 21.0 s). No new platform problem found; the findings above are updated:

- Issue 3 (`get` gives text or addresses, not both): fixed. The summarizer opened 10 nodes with `get`; a section of up to 8000 characters comes back as `{"card", "parts": [{"address": "fs://pdf/001#3.1", "text": ...}, ...]}` and the key points cite `fs://pdf/001#3.1`, `#23.4`, `#34.1`; the quote check passed (the first save was refused only because the page overflowed). Quotes keep the PDF's line breaks (`\n`) and still match.
- Issue 4 (given adapters get no default index): fixed in the platform (tests pass: 21).
- The mission text for `get` was updated for the new shape (parts with `address` and `text` for short sections, the cards below for long ones).

## nextop 0.4.0.dev9 (branch fs-graph, the new paragraphs splitter, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `21 passed`, real runs on the paper with gpt-5.4-mini (evidence in scratchpad
`phase14\realrun\t03_ja` and `t03_ja_hung`).

- Ported from the Korean edition: `parts/splitter/paragraphs.py` is the new nextop example; the tests no longer name the
  index part (the run adds the default bm25 index by itself).
- Run: 4 model calls, 53,458 tokens, 18.2 s; 9 `get` calls; first save past one page by about 358 characters, second
  passed; 3 key points citing paragraphs, every quote passed; no table or figure chosen; mail sent; Japanese only.
- Platform finding (medium): the first run of the day (`runs/20261127-111749-9dbb` of the copy `t03_ja_hung`) hung in
  the summarizer: three model calls came back in about 1 s each, the fourth request never answered, and after more than
  12 minutes the run still showed `running` (no event, no retry, no error) until it was killed. The OpenAI adapter has no
  time limit unless the project sets one (`nextop/adapters/openai_compat.py`: `timeout` None, "no time limit unless the
  project sets one"; `urllib.request.urlopen(req, timeout=self.timeout)`), so one stalled HTTP request stops a flow
  forever. Suggested: a default request timeout (a few minutes) with the existing retry, or `nextop check` / the run
  saying that no timeout is set. Not worked around in the tutorial (the rerun passed).
