# チュートリアル 2. 毎朝届く「明日の株価見通し」メール

> **投資の勧誘ではありません · ニュースから作った見通しです**

米国の金融ニュースサイトからエヌビディア、アップル、マイクロン、スペースXの最新記事を集め、会社ごとに次の取引日の方向（上昇・横ばい・下落）と理由を書き、理由ごとに記事の段落を一つ根拠として付けて（段落はプログラムが原文のまま写します）、一通のメールで送るフローです。仕事をするのは二人のワーカー（収集と分析）で、メールはプログラムが書きます。

これは日本語版です。対象は米国株4銘柄だけで、記事は米国のニュースサイトの英語記事、メールは日本語です。根拠の段落は記事の原文（英語）のまま載せ、理由の文は日本語で書きます。色は米国株なので米国の株価ページと同じ（上昇が緑、下落が赤）にしています。英語版（`../../en/tutorial_02_stock_news`）は同じ4銘柄を英語で、韓国語版（`../../ko/tutorial_02_stock_news`）はサムスン電子、SKハイニックス、NVIDIA、SpaceX を韓国語で扱います。

## 最後にできあがるもの

アオイ（ニュース収集担当）は会社ごとにニュースを一回だけ検索し、本当の記事だけを選んでファイルサーバー `news` に上げます（会社名のタグ付き。すでに保存されているアドレスの記事は二度と上げません）。レン（株価見通しアナリスト）は一社ずつ別々に会話し（見えるのはその会社の記事だけ）、方向と理由を書き、理由ごとに、根拠になる記事の段落のアドレス（`fs://news/003#1.2`）を付けます。レンは引用を書き写しません。段落の本文は**モデルではなくプログラム**が記事から取ってメールに入れ、レンが書いたアドレスが記事全体や日付とURLの行ではなく本文の段落1つであるかどうかも、プログラムが確かめて、違えば差し戻します。理由の文が日本語になっているか（中国語・韓国語・ロシア語の文字や、名前以外の英単語が混ざっていないか）もプログラムが確かめます。メールはプログラムが書きます。タイトル、日付、アドレスは保存された記事ファイルから読み、モデルが入力したアドレスは信用しません。

スペースXは2026年6月に Nasdaq に上場しました（SPCX）。上場していない会社を加えると、メールには株価がないことが書かれ、方向はニュースの雰囲気だけ（好材料が中心・まちまち・材料少なめ・悪材料が中心）で書かれます。

**実際の実行例（モデル: OpenAI の `gpt-5.4-mini`、nextop 0.4.0 のコンパイル済み wheel 0.4.0.dev9）。** 2026-11-27（金）に実際の検索（Tavily）と実際のモデルで作られたメールです。記事とモデルによって毎回変わります。

件名: `[株価見通し テスト] 2026-11-30 (月) エヌビディア 下落、アップル 上昇、マイクロン 下落、スペースX 上昇`（`[株価見通し テスト]` はテストモード `MAIL_TEST_MODE=1` のときだけ付きます。メールはテキストと HTML の両方で送られ、同じ内容が `outlooks/2026-11-30.txt` と `.html` に保存されます。）

```
※ 投資の勧誘ではありません · ニュースから作った見通しです

2026-11-30 (月) の株価見通し（ニュース収集日 2026-11-27 (金)）

▼ エヌビディア: 下落
▲ アップル: 上昇
▼ マイクロン: 下落
▲ スペースX: 上昇

## エヌビディア（Nasdaq: NVDA） · 下落
ニュースの流れ: AI関連の不安やCEOをめぐる見方の変化で、株価が続落する流れです。
1. AI関連の売りが続いており、直近でも株価が大きく下げているため、次の取引日も弱含みになりやすいです。
   記事: Nvidia, AMD, and Micron stocks sink as investors flee AI trade - Yahoo Finance（2026-11-25）
   https://finance.yahoo.com/markets/article/nvidia-amd-micron-stocks-sink-as-investors-flee-ai-trade-134518921.html
   根拠の段落: "# Nvidia, AMD, and Micron stocks sink as investors flee AI trade. Nvidia (NVDA) stock retreated another 5% on Wednesday, following a 6% decline in the prior session as ch ..."
2. CEO復帰は一時材料になったものの、ガバナンスへの疑念が残っているため、投資家心理の改善につながりにくいです。
   記事: Nvidia Stock Falls Again as AI Fears and CEO Questions Weigh on Shares - Yahoo Finance（2026-11-25）
   https://finance.yahoo.com/markets/stocks/articles/nvidia-stock-falls-again-ai-151733005.html
   根拠の段落: "The board reversed course after reviewing concerns about his conduct and leadership, leaving investors to assess whether his return settles questions or creates new conce ..."

## アップル（Nasdaq: AAPL） · 上昇
ニュースの流れ: AI売りの中でもiPhoneメーカーとして相対的な強さが目立つ流れです。
1. AI関連の売りが広がる中でもApple株は上昇しており、相対的な強さが続きやすいです。
   記事: Apple Stocks Rise as AI Selloff Spares the iPhone Maker（2026-11-26）
   https://finance.yahoo.com/markets/stocks/articles/apple-stocks-rise-ai-selloff-190038273.html
   根拠の段落: "Apple (NASDAQ:AAPL) shares rose 0.43% to $355.58 at the 4:00 p.m. ET close on November 25, gaining on a day when the Nasdaq Composite fell as much as 4.6% before recoveri ..."
2. AIを大規模なデータセンター投資ではなく既存端末への組み込みに寄せる戦略が、防御的な評価につながっています。
   記事: Apple Stocks Rise as AI Selloff Spares the iPhone Maker（2026-11-26）
   https://finance.yahoo.com/markets/stocks/articles/apple-stocks-rise-ai-selloff-190038273.html
   根拠の段落: "Apple (NASDAQ:AAPL) shares rose 0.43% to $355.58 at the 4:00 p.m. ET close on November 25, gaining on a day when the Nasdaq Composite fell as much as 4.6% before recoveri ..."

## マイクロン（Nasdaq: MU） · 下落
ニュースの流れ: 供給過剰懸念やメモリ需給悪化への警戒で、株価が弱含む流れです。
1. アナリストがメモリ半導体の供給過剰リスクが高まっていると警告し、マイクロンの価格決定力を損なう可能性があるため、弱材料です。
   記事: Micron’s stock falls as an analyst warns about a future supply glut - MarketWatch（2026-11-24）
   https://www.marketwatch.com/story/microns-stock-falls-as-an-analyst-warns-about-a-future-supply-glut-f7fbeefb
   根拠の段落: "# Micron’s stock falls as an analyst warns about a future supply glut. ## A BNP Paribas analyst says the risk of an ‘oversupply scenario is mounting’ for memory chips, an ..."
2. 同じ記事でマイクロン株は火曜日に11%下落したと伝えられており、ニュースの反応がすでに悪化しています。
   記事: Micron’s stock falls as an analyst warns about a future supply glut - MarketWatch（2026-11-24）
   https://www.marketwatch.com/story/microns-stock-falls-as-an-analyst-warns-about-a-future-supply-glut-f7fbeefb
   根拠の段落: "# Micron’s stock falls as an analyst warns about a future supply glut. ## A BNP Paribas analyst says the risk of an ‘oversupply scenario is mounting’ for memory chips, an ..."

## スペースX（Nasdaq: SPCX） · 上昇
ニュースの流れ: FCCの承認や株式配布の話題など、事業拡大と制度面のニュースが中心です。
1. FCCがSpaceXの宇宙データセンター計画に道を開いたため、事業拡大への期待が高まりやすいです。
   記事: FCC Authorizes SpaceX to Build 1 Million Data Centers in Space - WSJ（2026-11-25）
   https://www.wsj.com/business/fcc-authorizes-spacex-to-build-1-million-data-centers-in-space-0eb20ee7
   根拠の段落: "The Federal Communications Commission has approved SpaceX’s SPCX 1.74%increase; green up pointing triangle request for one million satellites to create data centers in sp ..."
2. SpaceXがアクティブなTrump Accountに自社株を配ると発表しており、注目度の上昇が材料になりやすいです。
   記事: SpaceX, Elon Musk to give one share each to active Trump accounts - Yahoo Finance（2026-11-25）
   https://finance.yahoo.com/markets/article/spacex-elon-musk-to-give-one-share-each-to-active-trump-accounts-205719872.html
   根拠の段落: "2. Best 0% APR Cards. # SpaceX, Elon Musk to give one share each to active Trump Accounts. SpaceX (SPCX) said Wednesday it will give one share of its Class A stock to eve ..."
3. ただし、2本とも将来計画や贈与の話題で、業績への直接的な裏づけは本文からは強く読み取りにくいです。
   記事: FCC Authorizes SpaceX to Build 1 Million Data Centers in Space - WSJ（2026-11-25）
   https://www.wsj.com/business/fcc-authorizes-spacex-to-build-1-million-data-centers-in-space-0eb20ee7
   根拠の段落: "The Federal Communications Commission has approved SpaceX’s SPCX 1.74%increase; green up pointing triangle request for one million satellites to create data centers in sp ..."

※ 投資の勧誘ではありません · ニュースから作った見通しです。根拠の段落は、ワーカーが選んだ記事の段落を、プログラムが原文（英語）のまま写したものです。
```

（読みやすさのため、根拠の段落は約 170 文字で `...` と縮めています。メールには段落の全文があります。全文は自分で実行したあと `outlooks/` にあります。）

**「根拠の段落:」の行は、レンが書いたのではなく、プログラムが記事から段落を原文（英語）のまま入れたものです。** レンが書いたのは理由の文（`point`）と段落のアドレス（`fs://news/002#1.2` のような `source`）だけで、プログラムがそのアドレスの段落を保存された記事から取って、メールに入れます。書き写しミスはありません。この実行では、アオイが 4 回の検索の結果から本当にその会社についての 6 本を選んで `news` に上げました（Yahoo Finance、MarketWatch、WSJ の記事。どれも `stocks.json` の米国のニュースサイトです）。

このメールで読んで気づいた点（検査では見つけられないものです）:
- 日本語は読みやすく、文は「です・ます」でそろっていて、中国語・韓国語は混ざっていません（英語は会社名、製品名、「Trump Account」のような固有の名前だけです）。
- 根拠の段落には、記事の取り込み時に混ざった表示用の文字（「2. Best 0% APR Cards.」や「increase; green up pointing triangle」など）が残っています。これは検索結果（Tavily）の本文にあったものを、段落としてそのまま写した結果で、レンの間違いではありません。
- アップルとマイクロンは、2 つの理由がそれぞれ同じ段落を指しています（どちらも記事が 1 本だけでした）。ミッションは「同じ記事を二度使うときは別々の段落を選ぶ」と言っていますが、プログラムは同じ段落の二度使いを差し戻さないので、そのまま通りました。

この実行の `get` と `query` の使い方（`tools.jsonl`）: レンは `get` を 15 回、`query` を 8 回使いました（`query` には記事のアドレスと記事の言語の質問）。記事を `get` で開くと、段落がアドレスと本文の組で返ります（`fs://news/003#1.2` など）。

エヌビディア、マイクロン、スペースXの会話では、モデルが 4 社分の見通しを一度に保存しようとし、プログラムが「この会話は スペースX だけを扱います。その分だけを保存してください」のように差し戻しました（そのあと正しく保存しました）。アップルの会話では、ニュースの状態が「thin」なのに理由を 3 つ書いて差し戻されました。

**プログラムが根拠の段落をどう確かめるか。** 理由の `source` が記事全体（`fs://news/001`）だったり、日付とURLの行だったりすると、チェック（`checks.py` の `paragraph_errors`）は差し戻します。たとえば記事全体のアドレスなら、次のようになります:

```
エヌビディア: source「fs://news/001」は記事全体です。記事の段落を1つ選んでください（query や get の結果にある fs://news/001#1.2 のようなアドレスです）
```

段落は、`parts/splitter/paragraphs.py`（nextop の例の分割パーツをこのプロジェクトに置いたもの）が、見出しごとのセクションと、空行で区切った段落に分けたものです。検索（Tavily）の本文には空行がないことが多いので、800 文字を超えるかたまりは文の終わりで約 400 文字ずつに分けます（文は切りません）。文を終えない 15 文字未満のかけらは隣の段落に付け、200 文字を超える「#」の行は見出しではなく本文として扱います。文の終わりは「. ! ?」のほかに「。！？」も見るので、日本語の記事にもそのまま使えます（この例の記事は英語です）。この実行の 6 本の記事は 19 段落になり、いちばん長い段落は 659 文字でした（800 文字を超える段落も 15 文字未満の段落もありません）。分け方は記事の書き方で決まるので、プラットフォームには入れず、プロジェクトに置いてあります。

収集の状態に合わない理由の数や、日本語になっていない文も差し戻します。上の実行で実際に差し戻された文の一つ: `アップル: 理由が3個です。この会社のニュースの状態は「thin」なので、1〜2個にしてください`

**かかった時間**（`gpt-5.4-mini`、OpenAI の API と Tavily の検索。環境によって大きく変わります。数字は `runs/<run>/cost.json` と `events.jsonl` から）:

| 仕事 | 回数・時間 |
|---|---|
| アオイ: 検索4回 + 記事の選択 + 6本のアップロード（アップロード 4 回） | モデル呼び出し 4回（18,653 トークン） |
| レン: 下見 + 会社ごとの見通し（`get` 15 回、`query` 8 回、保存 9 回: 差し戻し 4 回） | モデル呼び出し 23回（102,060 トークン） |
| 実行全体 | モデル呼び出し 27回、プロンプト 117,330 + 出力 3,383 = 120,713 トークン、56.5秒（0.4.0.dev6: 18回、87,346 トークン、60.6秒） |

## 時間と必要なもの

およそ1時間です。できあがったプロジェクトを読み、設定を入れて実行します。

- Python 3.11〜3.13 と nextop 0.4.0: 下の 0 の `setup.bat` がすべてインストールします（手動なら `pip install -r requirements.txt`）。このチュートリアルは nextop 0.4.0 のファイルサーバー（タイプフォルダー、共通ツール）で書かれています。0.4.0 が PyPI に公開されるまでは、受け取った wheel ファイルでインストールします: `setup.bat <wheel ファイルのパス>` `requirements.txt` は nextop 0.4.0 に固定し、`project.json` の `"nextop": ">=0.4,<0.5"` がこのプロジェクトに必要なバージョンを示します（別のバージョンだと `nextop check` が直し方を知らせます）。すでに別の nextop が入っている場合は `setup.bat` が 0.4.0 に入れ替え、最後にインストールされたバージョンを表示します。
- OpenAI API のキー（既定。ほかの OpenAI 互換 API でも動きます。下の設定を参照）
- Web 検索のキー: [Tavily](https://tavily.com) の `TAVILY_API_KEY`（1回の実行で4回検索します）
- メールアカウントの SMTP 設定（なくてもかまいません。ないとメールの段階だけ失敗し、見通しは `outlooks/` に残ります）

手順 1〜3 はモデルも検索キーもなしですぐにできます。テストは偽のモデルと偽の検索サービスを使います。

## ここで学べる nextop の機能

- 二人のワーカー（アオイ、レン）とプログラムのブロック（`plan`、`mail_outlook`）を組み合わせたフロー
- ツールで外から取ってくる: Web 検索はファイルサーバーではなくプロジェクトのツール（`news_search`）で、ワーカーは選んだ記事だけを上げます
- 残るファイルサーバー（`lifetime: project`）とタグ・有効期限（`expire_after`）: 記事は7日間保存され、会社名がタグになります
- タイプフォルダーと分割パーツ: `types/articles/type.json`（md の記事、段落で分ける、最初の一文を地図にする）と、プロジェクトの `parts/splitter/paragraphs.py`
- 共通ツール `upload`、`query`、`get`: アオイは `upload` で記事を上げ、レンは `query` で記事の段落を探し、段落のアドレスを理由に付けます
- ステップと `for_each`: レンはまず全社のニュースを下見し（scan）、そのあと会社ごとに別々に会話します（judge）。一つの会話に見えるのはその会社の記事だけです
- プログラムのチェック（`checks.py`）: 理由の `source` が本文の段落1つのアドレスかを、モデルなしで確かめます
- 日本語の言語パック（`"language": "ja"`）: nextop がワーカーに渡す文やチェックの差し戻し文が日本語になります
- ファイルを受け取る関数（`FILES_IN`）: メールの関数が記事ファイルと段落（`parts`）を自分で読み、タイトル、アドレス、根拠の段落を取ります
- 同じ記事を二度保存しない（ページのアドレスで重複を除く）
- モデルも検索も使わないテスト: 偽のモデルと偽の検索サーバーでフロー全体を動かします

## 手順

このフォルダー（`ja/tutorial_02_stock_news`）で PowerShell を開きます。

### 0. インストール: setup.bat を実行する

このフォルダーの `setup.bat` をダブルクリックするか、PowerShell で `.\setup.bat` を実行します。最初の 1 回で、このチュートリアルに必要なものをすべて自動でインストールします。

- Python 3.11〜3.13 を探します。なければ winget で Python 3.12 をインストールします（そのあと新しいターミナルを開いて `setup.bat` をもう一度実行）
- このフォルダーに仮想環境 `.venv` を作り、`requirements.txt`（nextop、pytest など）をインストールします。`setup.bat C:\ダウンロード\nextop-0.4.0...whl` のように wheel ファイルのパスを渡すと（または環境変数 `NEXTOP_WHEEL`）、nextop だけをそのファイルでインストールします。wheel は Python のバージョンに合っている必要があります（`cp311` なら Python 3.11）
- `.env` がなければ `.env.example` をコピーして作り、記入する名前だけを表示します。キーの値は自分で `.env` に書きます
- モデルなしのテストを実行し、すべて通ると最後に `Setup OK` と表示します

何度実行しても大丈夫です（すでにある `.venv` と `.env` はそのまま残します）。以下のコマンドは仮想環境を有効にしてから実行します。

```powershell
.venv\Scripts\activate
```

手動でインストールする場合:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 1. フォルダーを見る

```
project.json          プロジェクトの設定（LLM の接続、言語 ja）
stocks.json           4社（名前、ティッカー、上場かどうか、検索語）と検索の設定
workers/collector     アオイ: ニュース検索、記事の選択、アップロード
workers/analyst       レン: 会社ごとの方向と理由（段落チェックと日本語チェック付き）
tools/news_search.py  Web 検索ツール（Tavily）。新しい記事だけをファイルに保存して一覧を返します
functions/plan.py     最初のブロック: 見通しの対象日（週末のあとは月曜）と会社
functions/mail_outlook.py   最後のブロック: メール（テキスト + HTML）を作って送ります
functions/_news.py    設定、検索、メール（補助）
file_servers/news     記事の保管場所（7日間保存）: file_server.json + types/articles/type.json
parts/splitter/paragraphs.py   記事を見出しと段落に分ける分割パーツ（例のコピー）
flows/daily_outlook.json    plan -> アオイ -> レン -> メール
tests/                モデルも検索も使わないテスト
```

### 2. モデルなしでプログラムの部分をテストする

```powershell
python -m pytest -q tests
```

`20 passed` と出れば成功です。テストで確かめていること:
- 次の取引日が正しい（金曜と土曜は月曜になる）、曜日が日本語（`2026-11-26 (木)`）、アドレスが整理される（`?utm_...` や末尾の `/` は無視）、日付の形が一つ
- 検索ツールが同じアドレスを二度保存しない、保存済みの記事・SNS・米国ニュースサイト以外を外す、検索サービスにはそのサイトだけを頼む、検索が失敗したらモデルが読めるエラーを返す
- 理由の `source` が段落1つのアドレスなら通り、記事全体・セクション・日付とURLの行・読めない記事は差し戻される。理由の数が合わないものと、日本語でない文（中国語の簡体字、韓国語、ロシア語、名前以外の英単語、かなのない文）も差し戻す
- 偽のモデルでフロー全体が動く: アップロードに会社名のタグが付く、会社ごとに別の会話になる（他社の記事は見えない）、記事全体を根拠にした理由が一度差し戻されて直る、メールがテスト用メールサーバーに届き、根拠の段落はプログラムが記事から写している
- メールに注意書き、整理された記事アドレス、日本語の件名と見出しがある

### 3. 設定を入れる

```powershell
copy .env.example .env
```

（メモ帳で `.env` を作るときは「UTF-8」で保存してください。）そのあと下の「設定」のとおりに入れます。

### 4. フローを確かめる

```powershell
nextop check
```

LLM のキーを入れる前は次のように出ます:

```
[error] adapter llm.default: API key missing: set LLM_API_KEY in the environment or .env
```

モデルのアドレス、キー、名前を入れると `OK: stock news outlook (workers 2, tools 1, flows 1, file servers 1)` と出ます（nextop のコマンドの表示は英語です）。

### 5. 実行する

```powershell
nextop run --flow daily_outlook
```

1〜2分後に `run <id>: done` と出ます。最初は `MAIL_TEST_MODE=1` なので、メールは `OFFICE_EMAIL` にだけ届きます。

### 6. 結果を見る

- `OFFICE_EMAIL` の受信箱: 上のようなメール（件名は `[株価見通し テスト]` で始まります）
- `outlooks/<日付>.txt` と `.html`: 同じ内容
- `file_servers/news/store/`: 保存された記事（`items/` が記録、`files/` が記事の本文）。会社名のタグ付き
- `runs/<run id>/`: フローの記録。どのブロックにも `inputs.md`（モデルが受け取ったもの）、`calls.jsonl`（モデルの呼び出し）、`tools.jsonl`（ツールの呼び出しとチェックが差し戻した文）があります。チェックが差し戻したものは、`tools.jsonl` の `save_output` の行に `refused_by: program` として残ります

もう一度実行してみてください。アドレスがすでに保存されている記事はツールが外し（`skipped_known`）、新しい記事だけが上がります。1回の実行で検索は4回（会社ごとに1回）です。

### 7. 自分で変えてみる

- `stocks.json` の会社を変えたり加えたりする（名前、ティッカー、上場かどうか、検索語）と、アオイとレンはそれを扱います。ツールとワーカーはそのままです
- `stocks.json` の `search.include_domains` でニュースサイトを変える（検索はそのサイトだけを対象にし、ツールはほかのサイトのページを外します）
- `workers/analyst/mission.md` でレンの基準（上昇と横ばいの分かれ目など）を変える

## しくみ

```
plan（プログラム）  今日、次の取引日（週末のあとは月曜）、会社
   |
   +--> アオイ（collector）  <-- ツール: news_search（Tavily、会社ごとに1回、米国ニュースサイトだけ、新しい記事をファイルに保存）
   |        本当の記事だけをニュースファイルサーバーに上げる（upload、タグ: 会社名）
   |        v   coverage: 会社ごとに ok / thin / none
   +--> レン（analyst）     <-- アオイが上げた記事（news）
   |        ステップ 1 scan: 会社ごとのニュースの大きな流れ
   |        ステップ 2 judge（for_each）: 会社ごとに一つの会話、その会社の記事だけ
   |             記事ごとに query で段落を探す -> 方向 + 理由（根拠の段落のアドレス）
   |             checks.py: source が本文の段落1つ（paragraph_errors）、理由の数、日本語の文
   |        v   outlook
   +--> mail_outlook（プログラム）  記事ファイルからタイトル、日付、アドレス、根拠の段落を読んでメールを書く --> 送る
```

- アオイがツールに渡すのは会社名だけです。検索語（英語）とニュースサイトは `stocks.json` にあり、アオイは結果を読んで選ぶだけです。
- 記事ファイル（タイトル、日付、アドレス、本文）はツールが書きます。アオイはそれを変えずに上げます。
- すでに保存されているアドレスはツールが外します。ツールは保管フォルダーを開かず、ファイルサーバーのビュー（`ctx["file_servers"]["news"].sources()`）に尋ねます。アドレスの書き方が違うだけの同じ記事（`?utm_...`、末尾の `/`）は一つのアドレスです。
- レンは理由ごとに、根拠になる段落のアドレスを付けます（`query` や `get` の結果にあるアドレスをそのまま写します）。プログラムがそのアドレスを確かめ、記事全体や日付とURLの行なら差し戻します。モデルが判断するチェックはありません。質問（`query` の `question`）は記事の言語（ここでは英語）で書きます。検索は言葉が合う段落を探すからです。
- 日本語チェックもプログラムです。理由の文と「ニュースの流れ」にかながあるか、漢字が日本語の漢字（JIS X 0208）か、ハングルやキリル文字がないか、名前以外の小文字の英単語がないかを見ます。英語の根拠の段落は見ません。
- メールの記事タイトル、日付、アドレス、根拠の段落は、プログラムが記事ファイルとそのファイルの段落（`parts`）から読みます。モデルが入力したアドレスや文は使いません。
- 一回の実行で、モデルは一度に一社の記事だけを受け取ります（`for_each`）。入力が小さく保たれ、他社の記事が紛れ込みません。

## 設定

### LLM（`project.json`、`workers/*/worker.json`、`.env`）

既定は OpenAI API です。`project.json` の `base_url` は `https://api.openai.com/v1`、各 `workers/*/worker.json` の `"model"` は `gpt-5.4-mini` です。`.env` の `LLM_API_KEY=` のあとに OpenAI API のキーを入れてください。ほかの OpenAI 互換 API でも動きます。`base_url` とモデル名を変えてください。

`nextop check` が `OK` と言えば完了です。

### Web 検索（Tavily）

`.env` の `TAVILY_API_KEY=` のあとにキーを入れます。1回の実行で4回検索するので、キーの残りクレジットをときどき確かめてください。検索の設定（何日前までか、会社ごとの結果数、対象にするニュースサイトと外すサイト）は `stocks.json` の `search` にあります。

### メール（SMTP）

`.env` に `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS` を入れます。ポート 587 は STARTTLS、465 は SSL を使います（それ以外のポートは暗号化なしで送るので、自分のコンピューターのテスト用サーバーだけに使ってください）。

- `MAIL_TEST_MODE=1`（既定）: メールは `OFFICE_EMAIL` にだけ届き、件名は `[株価見通し テスト]` で始まります。最初はこのままにしてください。
- 本番: `MAIL_TEST_MODE=0` にして `MAIL_TO=a@example.com,b@example.com`（複数はカンマ区切り）を入れます。件名は `[株価見通し]` で始まります。

パスワードとキーは `.env` にだけ入れます。`.env` はコミットも共有もしないでください（`.gitignore` に入っています）。

### 会社（`stocks.json`）

- `name`: メールに出る名前で、タグと照合のキーにもなります（エヌビディア、アップル、マイクロン、スペースX）。`query` は検索語で、英語の米国ニュースを探すため英語のままです。
- `listed`: `false` にすると、メールに株価がないことが書かれ、方向は「好材料が中心 / まちまち・材料少なめ / 悪材料が中心」で書かれます。スペースXは2026年6月に上場したので `listed: true`、`Nasdaq: SPCX` です。上場していない会社には `listed: false` を使ってください。
- 次の取引日は週末だけを飛ばします。米国市場の祝日（感謝祭など）は知りません。たとえば上の例の 2026-11-26 (木) は感謝祭で、米国市場は休みです。
- 米国市場の取引時間は日本時間の夜（23:30〜翌6:00、夏時間は 22:30〜翌5:00）です。

## 次に試すこと

- 毎日同じ時刻に受け取る: Windows のタスク スケジューラ（または cron）に `nextop run --flow daily_outlook` を登録します。米国市場が閉まったあと（日本時間の朝）がおすすめです
- 会社を加える（`stocks.json`）: 同じフローがそのまま動きます
- 昨日の見通しと今日の値動きを比べる: `outlooks/` と実際の値動きを読む別のフロー
- 記事の全文を読む: 記事の全文を取ってくるツールがあれば、根拠にできる段落が増えます（各サイトの利用規約を確かめてください）
- 読者ごとに自分の会社だけを送る: メールの関数で `MAIL_TO` ごとに分けます
