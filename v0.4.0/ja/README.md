# nextop チュートリアル（日本語版）

[nextop](https://pypi.org/project/nextop/) で働くワーカー（agentic worker）を作る、段階的なチュートリアルです。チュートリアルごとに完成したプロジェクトのフォルダーが1つあります。読んで、`.env` とモデルの設定を埋め、モデルなしでテストを動かしてから、実際に実行します。

日本語版は nextop 0.3.1 から使える日本語の言語パック（`project.json` の `"language": "ja"`）を使います。ワーカーへの指示、ツールのメッセージ、出力が日本語になります。

English: [../README.md](../README.md) · 한국어: [../README.ko.md](../README.ko.md)

## チュートリアル

国によって変わるチュートリアルは日本に合わせてあります。ほかは言語だけを日本語にしています。

| 番号 | チュートリアル | 日本語版の内容 |
|---|---|---|
| 1 | [ヘアサロンの予約チャット](tutorial_01_hair_salon/) | 日本のサロン（ヘアサロン こもれび）: 税込の円、日本の携帯電話番号、24 時間表記、火曜定休、国内SMSサービス用のスロット |
| 2 | [毎朝の株価見通しメール](tutorial_02_stock_news/) | 米国株: エヌビディア、アップル、マイクロン、スペースX |
| 3 | [PDF を A4 1枚に要約](tutorial_03_pdf_summary/) | 日本語の要約 |
| 4 | [よく知られた MCP サーバーで作るリンク要約](tutorial_04_mcp_link_summary/) | 日本語のレポート |
| 5 | [PDF からテーマ付きの PowerPoint を作る](tutorial_05_pdf_to_ppt/) | 日本語のスライド |

## 必要なもの

- Windows: まずチュートリアルのフォルダーで `setup.bat` を実行します。Python 3.11〜3.13 を探し（なければ winget でインストール）、`.venv` を作ってそのフォルダーの `requirements.txt`（nextop 0.3.1 とそのチュートリアルが使う道具）をインストールし、`.env.example` から `.env` を作り、モデルなしのテストを実行します
- 手動（どの OS でも）: Python 3.11〜3.13 と、チュートリアルのフォルダーで `pip install -r requirements.txt`
- チュートリアル 4 には Node.js（`npx`）も必要です。`setup.bat` はインストールしません: `winget install -e --id OpenJS.NodeJS.LTS`
- LLM API のキー。既定は OpenAI（`https://api.openai.com/v1`、モデル `gpt-5.4-mini`）で、キーは `.env` の `LLM_API_KEY` に入れます。OpenAI 互換 API ならどれでも動きます。`project.json` の `base_url` と `workers/*/worker.json` のモデル名を変えてください。日本語が得意なモデルをおすすめします
- 任意: メールを送る SMTP アカウント

チュートリアル 1 から始めてください。フォルダーごとに `README.md`（手順）と `PLATFORM_ISSUES.md`（作りながら見つけた nextop の問題と再現方法）があります。

## 日本語について

各 README の実行例は、2026-11-26 に nextop 0.4.0（コンパイル済みの wheel 0.4.0.dev6）と OpenAI の `gpt-5.4-mini` で実際に実行した結果です（チュートリアル 3 と 5 の架空の報告書の例だけは、2026-11-25 の nextop 0.3.1 とローカルモデルのままです）。以前のローカルモデルは日本語に中国語の簡体字や英単語を混ぜることがあったため、各チュートリアルにはそれをワーカーに差し戻すプログラムのチェック（モデルを使わないもの）があります。`gpt-5.4-mini` の今回の実行には混ざりはありませんでしたが、実行は 1 回ずつなので、日本語は実際に使う前に目で確かめてください。モデルの質の問題（言い回し、指示の取りこぼし）は、各 README に書いてあります。

## ライセンス

このリポジトリのチュートリアルファイルは [MIT ライセンス](../LICENSE) です。商用利用も含めて、自由にコピー・変更して使えます。チュートリアルが動く nextop プラットフォームは別のパッケージで、独自のライセンスに従います（[PyPI の nextop](https://pypi.org/project/nextop/) を参照）。
