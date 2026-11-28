# チュートリアル 4. よく知られた MCP サーバーでつくる「リンク要約アシスタント」

ウェブページのアドレスを 1〜3 個渡すと、ページを読んでそれぞれ要点を 3 つずつ選び、日本語の要約報告書（Markdown）を `reports/` に保存してメールで送ります。仕事をするのは 2 人のワーカー（読み取り担当、まとめ担当）で、**ワーカーが使うツールはすべて公式の MCP リファレンスサーバーのもの**です。ツールのコードは 1 行も書いておらず、ツールのための API キーも要りません。

これは日本語版です。報告書、件名、メールは日本語で書かれます（`"language": "ja"`）。英語版（`../../en/tutorial_04_mcp_link_summary`）と韓国語版（`../../ko/tutorial_04_mcp_link_summary`）は同じプロジェクトで、言語だけが違います。

## MCP を 3 行で

- MCP（Model Context Protocol）は、AI プログラムが外部のツールやデータを使う方法を決めたオープンな標準です。
- MCP サーバーがツール（例: ウェブページの取得、ファイルの書き込み）を提供し、nextop のような MCP クライアントがそのツールを受け取ってワーカーに渡します。
- そのため、すでにあるサーバーなら `project.json` に 1 項目書くだけで、ツールのファイルなしにワーカーがそのツールを使えます。

## このチュートリアルで見せること

- 既存の MCP サーバー 3 つを、名前と起動コマンドだけでつなぐ（`project.json` の `mcp_servers`）
  - `fetch`: ウェブページを取得して Markdown のテキストにする（`mcp-server-fetch` 2026.11.4、Python、`uvx` で起動）
  - `time`: タイムゾーンの今日の日付と曜日を返す（`mcp-server-time` 2026.11.4、Python、`uvx` で起動）
  - `filesystem`: ファイルを読み書きする。このチュートリアルでは **`reports/` フォルダーにだけ** 書ける（`@modelcontextprotocol/server-filesystem` 2.2.0、Node.js、`npx` で起動）
- サーバーのツールは `<サーバー名>__<ツール名>` で登録されます: `fetch__fetch`、`time__get_current_time`、`filesystem__write_file` など。ワーカーは `worker.json` の `tools` にその名前を並べると使えます。
- サーバーのツール説明だけでは足りないときのプロジェクト側の補足（`notes`）: `filesystem` の `write_file` に「ファイル名だけを書く」と添えています（理由は韓国語版の最初の実行記録を参照）。
- 秘密の値は `{env:名前}` で: このサーバーたちはキーが要りませんが、キーが要るサーバーなら `"env": {"API_KEY": "{env:MY_KEY}"}` のように `.env` の変数名だけを書きます。値は記録、検査メッセージ、ツールの結果のどこにも出ません。
- ワーカーが書き写すものはプログラムが検査します: 保存された報告書のファイルをプログラムが読み、すべてのアドレスが一字一句そのまま入っているか、今日の日付があるか、日本語になっているか（ハングルや簡体字が混ざっていないか、かなが入っているか）を確かめます（`workers/*/checks.py`）。モデルが判定する検査はありません。

## 最後にできあがるもの

ユイ（読み取り担当）が各アドレスを `fetch__fetch` で取得し、タイトルと要点 3 つを書きます。ページはアドレスではなく **番号** で呼びます（アドレスはプログラムが運びます）。カイ（まとめ担当）が `time__get_current_time` で今日の日付を確かめ、報告書を書いて `filesystem__write_file` で `reports/` に保存します。最後にプログラム（`mail_report`）が **保存されたファイルを読み**、本文と添付ファイルにしてメールで送ります。メールに失敗してもフローは止まりません。理由が結果に残り、報告書は `reports/` に残ります。

### 実際の実行（2026-11-26）

モデル: OpenAI の `gpt-5.4-mini`、nextop 0.4.0 のコンパイル済み wheel 0.4.0.dev6（PyPI への公開前なので `setup.bat <wheel のパス>` でインストールしました）。入力: `input.json` の 2 ページ（公式ドキュメントの MCP 紹介ページと、英語版 Wikipedia の Model Context Protocol の記事）。どちらも英語のページですが、要点は日本語で書かれます。文章はモデルとページによって毎回変わります。ユイは各ページを最初の 5000 文字（`fetch__fetch` の `max_length` 5000）だけ読み、`start_index` で続きを取りには行きません。

メールの件名: `[リンク要約・テスト] MCPの概要と導入背景をまとめたリンク要約（リンク2件）`（`[リンク要約・テスト]` はテストモード `MAIL_TEST_MODE=1` のときだけ付きます）。本文と添付ファイルは、このファイル `reports/links_20261126-235604.md` そのものです。

```
# リンク要約 · 2026-11-26 (木)

## 1. What is the Model Context Protocol (MCP)?
アドレス: https://modelcontextprotocol.io/docs/getting-started/intro
- MCPはAIアプリケーションを外部システムにつなぐためのオープンソース標準である。
- MCPにより、AIアプリケーションはデータソース、ツール、ワークフローに接続できる。
- このページはMCPの概要、利点、対応するエコシステム、学習項目を案内している。

## 2. Model Context Protocol - Wikipedia
アドレス: https://en.wikipedia.org/wiki/Model_Context_Protocol
- MCPはAnthropicが導入したオープン標準で、外部のツールやデータソースとの統合を標準化する枠組みである。
- 表には開発元、導入時期、業界、対応する接続用言語、公式サイトが示されている。
- 本文では、MCPの目的、情報のサイロや古い仕組みへの対応、採用状況が説明されている。

## ひとことで
MCPはAIアプリケーションと外部システムをつなぐための標準であり、概要と導入背景、対応状況が整理されている。
```

読んで気づいた点: 公式ページの要点は正しく、日本語だけで書かれています。Wikipedia の記事は最初の 5000 文字の大半が右側の情報欄（開発元、導入時期、対応言語、公式サイト）で、本文の説明が少ないため、2 ページ目の要点は「表には開発元、導入時期…が示されている」のように、ページが何を載せているかの説明にとどまり、事実の要点が薄くなりました。これは「最初の 5000 文字だけ」という取り決めの代償です。もっと深く読みたいときは、ミッションの手順 2 を変えて `start_index` で続きを読ませます（呼び出しと時間が増えます）。

同じ日の前の 2 回の実行の記録: 手順 2 の文を「結果の最後に案内があっても、最初の部分で要点がわかるなら、もう呼びません」（0.3.1 のときの文）のままにした実行では、ユイがウィキペディアのページで `start_index` 5000 の続きを 1 回取りました（モデル呼び出し 6 回、17,716 トークン）。「`start_index` は使いません」と書いた次の実行では取らず（5 回、12,331 トークン）、そのときの書き方は「# 」を付けたタイトル（`## 2. # Model Context Protocol - Wikipedia`）でした。いまのミッションは「先頭の `# ` を付けずに」と書いてあり、上の実行はそのあとのものです。

**かかった時間**（`gpt-5.4-mini`、OpenAI の API。MCP サーバーの `fetch` はインターネットを使います。環境によって大きく変わります。数字は `runs/<run>/cost.json` と `events.jsonl` から）:

| 仕事 | モデル呼び出し | 時間 |
|---|---|---|
| ユイ: 2 ページの取得（`fetch__fetch` 2 回）+ 要点の作成 | 2（5,794 トークン） | 7.4 秒 |
| カイ: 日付 + 報告書の作成と保存 + 結果の保存 | 3（6,557 トークン） | 5.2 秒 |
| メール | 0 | 0.3 秒 |
| フロー全体 | 5（合計 12,351 トークン） | 13.1 秒 |

nextop 0.4.0.dev9 でもう一度確かめました（2026-11-27、`gpt-5.4-mini`、新しい仮想環境に wheel だけ）。同じ 2 ページで、ユイ 3 回（11,058 トークン、`fetch__fetch` 3 回。Wikipedia の記事を `start_index` 5000 でもう一度読みました。ミッションは読まないように言っていますが、モデルがそうしました）、カイ 3 回（6,667 トークン）、合計モデル呼び出し 6 回、17,725 トークン、21.0 秒で、報告書とメールができました。要点は日本語だけで書かれ、韓国語は混ざっていません。この版のためにチュートリアルのファイルは変えていません。

## 時間と必要なもの

約 30 分。できあがったプロジェクトを読み、設定を入れて実行します。

- Python 3.11〜3.13 と nextop 0.4.0（MCP 付き）: 下の 0 の `setup.bat` がすべてインストールします（手動なら `pip install -r requirements.txt`）。 `requirements.txt` は nextop 0.4.0 に固定し、`project.json` の `"nextop": ">=0.4,<0.5"` がこのプロジェクトに必要なバージョンを示します（別のバージョンだと `nextop check` が直し方を知らせます）。すでに別の nextop が入っている場合は `setup.bat` が 0.4.0 に入れ替え、最後にインストールされたバージョンを表示します。
- [uv](https://docs.astral.sh/uv/)（`requirements.txt` に入っているので `setup.bat` がインストールします）: `uvx` が Python の MCP サーバー（fetch、time）をダウンロードし、それぞれ専用の環境で起動します
- Node.js 24 以上: `npx` が filesystem サーバーをダウンロードして起動します
- OpenAI API のキー（既定。ツール呼び出しに対応したほかの OpenAI 互換 API でも動きます。下の設定を参照）
- メールアカウントの SMTP 設定（なくてもかまいません。メールが送られず、報告書が `reports/` に残るだけです）
- 初回だけインターネット（`uvx` と `npx` がサーバーをダウンロードします）。2 回目からはローカルのキャッシュを使います。

`pip install mcp-server-fetch` でサーバーをインストールすることもできますが、`mcp` 2.3 以上が必要なため、nextop 自身が使う `mcp` が更新されてしまいます。`uvx` ならサーバーごとに専用の環境と正確なバージョンが使えます。

## ここで学ぶ nextop の機能

- `project.json` の `mcp_servers`: 3 つの stdio サーバー（コマンド、引数、時間制限）
- MCP ツールの名前の規則 `<サーバー>__<ツール>` とワーカーの `tools` リスト
- プロジェクトの補足（`notes`）: サーバー自身の説明に、このプロジェクトでの使い方を書き足す
- サーバーの権限を絞る: filesystem サーバーは引数で渡したフォルダー（`reports`）にしか書けない
- フロー検査（`nextop check`）がサーバーを起動してツール一覧を受け取り、ワーカーが名前を挙げたツールがすべてあるか確かめる
- MCP サーバーが書いたファイルを読むプログラム検査（`checks.py`）と、日本語の文に混ざった別の言語の文字を差し戻す検査
- メールに失敗してもフローを止めない最後のブロック（`mail_report`）
- モデルなしのテスト: 偽のモデル + 本物の 3 つの MCP サーバー + このパソコン上のテスト用ウェブページとテスト用メールサーバー

## 手順

このフォルダー（`ja/tutorial_04_mcp_link_summary`）で PowerShell を開きます。

### 0. インストール: setup.bat を実行する

このフォルダーの `setup.bat` をダブルクリックするか、PowerShell で `.\setup.bat` を実行します。最初の 1 回で、このチュートリアルに必要なものをすべて自動でインストールします。

- Python 3.11〜3.13 を探します。なければ winget で Python 3.12 をインストールします（そのあと新しいターミナルを開いて `setup.bat` をもう一度実行）
- このフォルダーに仮想環境 `.venv` を作り、`requirements.txt`（nextop[mcp] 0.4.0、uv、pytest など）をインストールします。まだ PyPI にない nextop を試すときは、`setup.bat C:\ダウンロード
extop-....whl` のように wheel ファイルのパスを渡すと（または環境変数 `NEXTOP_WHEEL`）、nextop だけをそのファイルでインストールします。wheel は Python のバージョンに合っている必要があります（`cp311` なら Python 3.11）
- `.env` がなければ `.env.example` をコピーして作り、記入する名前だけを表示します。キーの値は自分で `.env` に書きます
- モデルなしのテストを実行し、すべて通ると最後に `Setup OK` と表示します

このチュートリアルには Node.js も必要です（filesystem サーバーを `npx` で起動します）。`setup.bat` は Node.js をインストールしません。`npx` がないときは `winget install -e --id OpenJS.NodeJS.LTS` でインストールするよう表示して止まります。インストール後、新しいターミナルを開いて `setup.bat` をもう一度実行します。最初のテストでは `uvx` と `npx` がサーバーをダウンロードするので、インターネットが必要です。

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
project.json             プロジェクトの設定（LLM の接続、3 つの MCP サーバー）
input.json               実行の入力: {"links": "アドレス1\nアドレス2"}（1 行に 1 アドレス、1〜3 個）
workers/reader           ユイ: ページの取得（fetch__fetch）、要点 3 つ
workers/writer           カイ: 日付（time__get_current_time）、報告書の保存（filesystem__write_file）
functions/intake.py      最初のブロック: アドレスを読んで番号を振り、報告書のファイル名を決める
functions/mail_report.py 最後のブロック: 保存された報告書を読んでメールで送る（失敗してもフローは続く）
functions/_links.py      設定、アドレスの読み取り、タイムゾーンの日付、日本語の検査、メール（補助）
flows/link_summary.json  intake -> ユイ -> カイ -> mail_report
reports/                 報告書の保存先（filesystem サーバーが書ける唯一のフォルダー）
tests/                   モデルなしのテスト
```

`tools/` フォルダーはありません。ツールはすべて MCP サーバーから来ます。

### 2. モデルなしでテストする

```powershell
python -m pytest -q tests
```

`15 passed` と出れば成功です（初回はサーバーのダウンロードで少し時間がかかります）。テストが確かめること:
- 3 つの MCP サーバーが起動し、ツールが `fetch__fetch`、`time__get_current_time`、`filesystem__write_file` などの名前で登録され、フロー検査にエラーも警告もない
- fetch がページを読み、time がタイムゾーンの日付を返し、filesystem が `reports/` にだけ書ける（`project.json` への書き込みは拒否される）
- アドレスの読み取り（1〜3 個、http/https、重複なし）、日本語の検査（ハングル、簡体字、かなのない文）、ユイの検査（各ページ 1 回、要点 3 つ）とカイの検査（保存されたファイルにアドレスと日付がある。ページ自身のタイトルの文字は検査しない）
- 偽のモデルでフロー全体が動く: 本物の fetch サーバーがこのパソコンのテスト用ページ（日本語のコーヒーのページを含む）を読み、本物の filesystem サーバーが報告書を保存し、メールがテスト用メールサーバーに届く。アドレスが抜けた報告書は 1 回差し戻される。メールの設定がなくてもフローは正常に終わる

### 3. 設定を入れる

```powershell
copy .env.example .env
```

（メモ帳で `.env` を作るときは「UTF-8」で保存してください。）下の「設定」を見て値を入れます。

### 4. フローを検査する

```powershell
nextop check
```

`OK: mcp link summary (workers 2, tools 20, flows 1, file servers 0)` と出れば成功です。LLM のキーを入れる前は `[error] adapter llm.default: API key missing: set LLM_API_KEY in the environment or .env` と出ます。20 個のツールは fetch の 1 個、time の 3 個、filesystem の 16 個です（ワーカーが受け取るのはそのうち 3 個だけ）。サーバーが起動できないときは理由が表示され、サーバーが標準エラーに書いた内容は `runs/mcp/<サーバー名>.log` にあります。

### 5. 実行する

```powershell
nextop run --flow link_summary --input input.json
```

20 秒ほど（モデルによります）で `run <id>: done` と出ます。最初は `MAIL_TEST_MODE=1` なので、メールは `OFFICE_EMAIL` にだけ届きます。ほかのページを要約するには `input.json` の `links` を変えます（1 行に 1 アドレス、`\n` で区切って最大 3 個）。

### 6. 結果を見る

- `OFFICE_EMAIL` の受信箱: 件名が `[リンク要約・テスト]` で始まるメール。本文と添付ファイル（.md）が報告書です
- `reports/links_<日時>.md`: 報告書
- `runs/<実行 id>/blocks/<ブロック>/attempt-1/`: `inputs.md`（モデルが受け取ったもの）、`calls.jsonl`（モデルの呼び出し）、`tools.jsonl`（MCP ツールの呼び出しと結果、検査が差し戻した文）
- `runs/<実行 id>/blocks/mail_report/attempt-1/output.json`: メールが送られたか（`sent`）とその理由（`note`）

### 7. スタジオで見る

```powershell
nextop studio
```

ブラウザーでフロー `link_summary` を選ぶと、intake → ユイ → カイ → mail_report が見えます。TOOLS タブには MCP ツールがサーバー名（`MCP server fetch` など）とともに並び、各サーバーの状態（ツールの数、または使えない理由）が表示されます。ツールの試し実行はサーバーに 1 回呼び出しを送ります（例: `time__get_current_time` に `{"timezone": "Asia/Seoul"}`）。サーバーの設定を変えたら、スタジオを再起動してください（スタジオは動いている間、接続を保ちます）。

## しくみ

```
intake（プログラム）   アドレスに番号（1, 2, 3）を振り、報告書のファイル名を決める
   |
   +--> ユイ（reader）   <-- MCP: fetch__fetch（ページごとに 1 回）
   |        ページ番号ごとに: タイトルと要点 3 つ（アドレスは書かない）
   |        checks.py: 各ページ 1 回、要点 3 つ、日本語（ハングル・簡体字なし、かなあり）
   |        v   notes
   +--> カイ（writer）   <-- MCP: time__get_current_time（今日の日付）、filesystem__write_file（reports/ に保存）
   |        報告書: 日付、ページごとのタイトル・アドレス・要点、全体のひとこと
   |        checks.py: 保存されたファイルを読む: すべてのアドレス、今日の日付、日本語
   |        v   report（ファイル名、1 文の見出し）
   +--> mail_report（プログラム）  reports/ のファイルを読んでメールで送る。失敗したら理由だけを残す
```

- ユイはページを番号だけで呼びます。アドレスは intake が作ったリストにあり、カイがそのリストから書き写します。書き写したアドレスが一字一句正しいかは、保存されたファイルでプログラムが確かめます。
- 報告書のファイル名はプログラム（intake）が決めます。カイはその名前で保存し、メールのブロックはその名前のファイルを読みます。メールに入るのは、モデルが出力に書いた文ではなく、ディスクに保存されたファイルです。
- filesystem サーバーは、引数で渡した `reports` フォルダーの外を読むことも書くこともできません。ワーカーが受け取ったのは、そのうち書き込みのツール 1 つだけです。
- **日本語の検査**（`functions/_links.py` の `japanese_errors`）: ハングル、日本語では使わない簡体字（这、们、说、时、发、为 など）、かなが 1 文字もない文（英語や中国語の文）を差し戻します。ページ自身のタイトル（英語のことが多い）は検査しません。簡体字の一覧はよく出る字だけなので、すべての中国語を見つけるわけではありません。
- **タイムゾーンは Asia/Seoul** です。英語版・韓国語版と同じです（この版は言語だけを変えています）。Asia/Tokyo も同じ UTC+9 なので日付は変わりません。自分のタイムゾーンにするには、そろえる必要がある 3 か所を変えます: `project.json` の time サーバーの `--local-timezone`、`workers/writer/mission.md` の `timezone`、`functions/_links.py` の `SEOUL`（検査が期待する日付）。

## 設定

### LLM（`project.json`、`workers/*/worker.json`、`.env`）

既定は OpenAI API です。`project.json` の `base_url` は `https://api.openai.com/v1`、各 `workers/*/worker.json` の `"model"` は `gpt-5.4-mini` です。`.env` の `LLM_API_KEY=` のあとに OpenAI API のキーを入れてください。ほかの OpenAI 互換 API でも動きます。`base_url` とモデル名を変えてください。

### MCP サーバー（`project.json` の `mcp_servers`）

```json
"mcp_servers": {
  "fetch": {"transport": "stdio", "command": "uvx",
            "args": ["--from", "mcp-server-fetch==2026.11.4", "mcp-server-fetch"], "timeout": 120},
  "time": {"transport": "stdio", "command": "uvx",
           "args": ["--from", "mcp-server-time==2026.11.4", "mcp-server-time", "--local-timezone", "Asia/Seoul"],
           "timeout": 120},
  "filesystem": {"transport": "stdio", "command": "npx",
                 "args": ["-y", "@modelcontextprotocol/server-filesystem@2.2.0", "reports"], "timeout": 120,
                 "notes": {"write_file": "..."}}
}
```

- バージョンは正確に固定しています（`==2026.11.4`、`@2.2.0`）。固定しないと、ある日新しいバージョンがダウンロードされて動きが変わることがあります。
- `timeout` 120 秒: 初回のサーバーのダウンロードのための余裕です。
- コマンドはこのフォルダーで実行されます（既定の `cwd`）。そのため `reports` はこのフォルダーの `reports/` です。
- fetch サーバーは既定で各サイトの robots.txt に従い、このパソコンやプライベートネットワークのアドレス（127.0.0.1、192.168.x.x）は読みません。テストだけが、このパソコンのテスト用ページを読むために `--allow-private-ips` を付けます。
- `write_file` の `notes` は英語のままです（英語版・韓国語版と同じ文）。ワーカーへの説明で、日本語の言語パックでもそのまま伝わります。

### メール（SMTP）

`.env` に `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASS`、`OFFICE_EMAIL` を入れます。ポート 587 は STARTTLS、465 は SSL を使います（それ以外のポートは暗号化なしで送るので、自分のパソコンのテスト用サーバーにだけ使ってください）。

- `MAIL_TEST_MODE=1`（既定）: メールは `OFFICE_EMAIL` にだけ届き、件名が `[リンク要約・テスト]` で始まります。
- 本番では: `MAIL_TEST_MODE=0` にして `MAIL_TO=a@example.com,b@example.com`（複数ならカンマ区切り）を入れます。

パスワードとキーは `.env` にだけ書きます。`.env` はコミットも共有もしないでください（`.gitignore` に入っています）。

## ほかの MCP サーバーを足す

よく知られた MCP サーバーの多くは「起動コマンド + 引数」の 1 行でつながります。手順はいつも同じです。

1. `project.json` の `mcp_servers` に名前（小文字の英字、数字、`_`）と起動方法を書きます。バージョンは正確に固定します。
2. `nextop check` を実行してツールの名前（`<サーバー名>__<ツール名>`）を確かめます（スタジオの TOOLS タブにも出ます）。
3. それを使うワーカーの `worker.json` の `tools` に名前を書き、そのワーカーの `mission.md` にいつ使うかを書きます。サーバーの説明だけでは使い方が足りないときは `notes` を足します。

例 1. キーが要る stdio サーバー（値は `.env` に、`project.json` には変数名だけ）:

```json
"github": {"transport": "stdio", "command": "npx",
           "args": ["-y", "@modelcontextprotocol/server-github@<version>"],
           "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "{env:GITHUB_TOKEN}"}}
```

例 2. すでにどこかで動いているサーバーに http（Streamable HTTP）でつなぐ。同じ fetch ツールを http で提供している場所があるなら（例: fetch サーバーを包んだ社内の MCP ゲートウェイ）:

```json
"fetch": {"transport": "http", "url": "https://<server host>/mcp",
          "headers": {"Authorization": "Bearer {env:FETCH_TOKEN}"}}
```

サーバー名が同じならツール名（`fetch__fetch`）も同じなので、ワーカーは変える必要がありません。nextop は http のサーバーを起動せず、つなぐだけです（サーバーはすでに動いている必要があります）。

## 次に試すこと

- アドレスの代わりに検索語を受け取る: 検索の MCP サーバー（例: Brave Search）を足し、見つかったアドレスをユイに読ませる
- 同じページの要約を毎日受け取る: `nextop run --flow link_summary --input input.json` を Windows のタスク スケジューラ（または cron）に登録する
- 以前の報告書と比べる: カイに `filesystem__read_text_file` を渡し、昨日の報告書から変わったことを `reports/` に書かせる
