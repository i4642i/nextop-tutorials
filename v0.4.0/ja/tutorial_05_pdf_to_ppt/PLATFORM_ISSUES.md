# チュートリアル 5 を作る中で見つけたプラットフォームの問題（日本語版）

PyPI からインストールした nextop 0.3.1 で見つけたものです（新しい venv で `pip install "nextop[pdf,mcp]==0.3.1"`、パスにプラットフォームのチェックアウトなし）。プラットフォームを変えて回避したものはありません。英語版と韓国語版で見つかった問題は `../../en/tutorial_05_pdf_to_ppt/PLATFORM_ISSUES.md` と `../../ko/tutorial_05_pdf_to_ppt/PLATFORM_ISSUES.md` にあります。

## 1. 引用の検査（`quotes`）が日本語の行の変わり目で一致しない
- チュートリアル 3 の日本語版の [`PLATFORM_ISSUES.md`](../tutorial_03_pdf_summary/PLATFORM_ISSUES.md) の 1 と同じ問題です。`pdf_text` は段落の中の行を `\n` でつなぎ、`quotes` は改行を空白一つにしてから比べるので、空白なしで続く日本語の文を行をまたいで正しく写した引用（`高かった。`）が、原文（`高かっ\nた。` → `高かっ た。`）と一致しません。
- チュートリアルへの影響: チュートリアルの中で回避しました。`workers/writer/checks.py` が、引用（`columns[].bullets[]` の中も）と原文の両方に `functions/_common.py` の `joined`（日本語の文字の隣の空白と改行を取り除く）をかけてから `quotes` に渡します。実際の実行（2026-11-25、架空の報告書、run 20261125-214614-a9c5）で、しおりの引用「参加者アンケートでは、読み聞かせの会の満足度が最も高かった。」はこの回避で通りました。テスト: `test_flow.py` の `writing()` の 2 つの引用（`貸出冊数\nは`、`延ば\nし`）と `test_quotes_are_compared_without_the_line_breaks_of_japanese`。

## 2. 行末のハイフンで切れた英単語は、一字一句写しても一致しない（言語に関係なし）
- 試したこと: 論文 "Attention Is All You Need" の 3.1 節の文を引用する。
- 起きたこと: PDF では `position-` で行が終わり次の行が `wise` で始まるので、`pdf_text` の本文は `position-\nwise`、`quotes` の比べる形は `position- wise` になる。論文の文どおりの `a simple, position-wise fully connected feed-forward network` は「引用が見つかりません」で差し戻される（実際の実行 run 20261125-213840-4cdd と 20261125-214147-c4eb で、しおりの引用がこれで差し戻され、別の文を引用し直しました）。
- 期待: 行末のハイフンの後の改行は、比べる前に取り除く（`-\n` → `-`）。または `pdf_text` が行末のハイフンでつながった語を一つにしてテキストに入れる。
- 再現: `python get_paper.py` のあと
  `python -c "from nextop.parts.reader import pdf_text; t=[p['text'] for p in pdf_text.read('input/attention_is_all_you_need.pdf')['parts'] if 'Each layer has two' in p.get('text','')][0]; i=t.find('position-'); print(repr(t[i:i+20]))"` → `'position-\nwise fully'`
- チュートリアルへの影響: 小さい。差し戻されたワーカーは別の文を引用して通ります。英語版と韓国語版でも同じことが起きるはずです（同じ論文、同じ読み取りパーツ）。チュートリアルでは回避していません。

## 3. メモ: 言語の検査は各チュートリアルが書く
- チュートリアル 3 の日本語版と同じく、「書いた文が日本語か」はチュートリアルの `checks.py` が検査します（`language_errors`: 仮名のない文、韓国語の文字、cp932 にない漢字）。実際の実行では、しおりの最初の保存の「多头」（4 か所）を差し戻せました。一方、載せなかったもう一回の実行の「巻込み」（畳み込み）や「係り受け解析」（構成素解析）のように、日本語の字で書いた誤訳は文字では見分けられません。

## 問題なし
- 日本語の言語パック（`"language": "ja"`）: `quotes` の差し戻し（`引用が見つかりません: …`）が日本語で出ました。
- doc ファイルサーバーと `pdf_text`（論文: 図 1 と図 2 は元の解像度 911×1343 と 1216×769、キャプション全文。架空の報告書: 本文 7、表 2、図 1、`表1.`・`図1.` のキャプション）、`FILES_IN` / `FILES_OUT`、`columns[].bullets[]` の中の引用の検査、フローの検査は、実際の実行（2026-11-25、ローカルモデル。論文 2 回、架空の報告書 1 回、すべてメール送信まで）と 23 のテストで説明どおりに動きました。

## Phase 10: real run with the compiled wheel 0.4.0.dev6 and gpt-5.4-mini (2026-11-26)

Fresh venv with only the wheel (`site-packages`, `.pyd`, 0.4.0.dev6). Paper run, basic theme: `C:\Users\SHK\AppData\Local\Temp\claude\61d2a55c1c8ed559\7801ea38-cfcd-4c6c-a551-04091160998b\scratchpad\phase10ja\t05\runs\20261126-234911-6ba7` (11 model calls, 201,444 tokens, 72.3 s; planner 4 calls, writer 7 calls; 12 slides, `.pptx`, mail). No new platform problem found.

- The earlier finding that the writer called `get` 58 times (Korean dev5 run) is fixed: the writer opened 26 nodes. A section up to 8000 characters comes back with its paragraphs and their addresses (`parts`), so the writer cites paragraphs without a second call. Slide sources are paragraph addresses (`fs://pdf/001#6.1`); the first save was refused for sources that were not paragraphs of the slide's parts, and the refusal lists the allowed paragraph addresses, which the writer used.
- The planner needed four saves (13 slides instead of 12, tables too tall or too wide, a figure used twice); every refusal said what to change.
- `Transformer 構成` as a slide title was refused by the tutorial's language check (no kana) and became `トランスフォーマー構成`.
- Bullets came out short (3 per slide) and one bullet of the figure 2 slide is off the figure's content; the program does not check this.

## nextop 0.4.0.dev9 (branch fs-graph, one slide per writer conversation, 2026-11-27)

Checked with the compiled wheel 0.4.0.dev9 in a fresh venv (nextop from the installed `.pyd`, no source on the path):
`nextop check` OK on all 15 tutorials, `30 passed`, two real runs on the paper with gpt-5.4-mini, Basic theme
(evidence in scratchpad `phase14\realrun\t05_ja_*`).

- Ported from the Korean edition: the writer writes and saves one slide per conversation (split block
  `functions/split_slides.py`, gather keeps the order, a refused slide is redone alone); the planner's check asks a table
  or figure slide to rest on a text part that talks about it (`text_parts`); a slide naming one piece of a section gets
  the whole section; short documents get one section; section pieces carry their slides' topics (`covers`); the
  paragraphs splitter is the new nextop example; tests use the run's default index. The caption label of `text_parts`
  matches `Table|Figure|Fig.|表|図` (Japanese captions are "表1." and "図1."), and since Japanese has no spaces between
  words, a kana or kanji right before "表1" does not stop a match (only a Latin letter or digit does).
- Runs: 1) 29 calls (planner 4, writer 25), 156,438 tokens, 51.1 s; 2) 26 calls (planner 3, writer 23), 123,526 tokens,
  36.5 s. Both made the 12-slide .pptx, the previews and the mail. The writer's refused saves (1 and 2) were redone alone:
  bullet count on a table slide, a cover title in English with no kana (the language check), bullets outside the columns
  of a comparison. Every slide sat in its outline place; slide text in Japanese, no Korean letters (paper terms such as
  "key size" and "dropout" stay in English).
- No new platform problem.
