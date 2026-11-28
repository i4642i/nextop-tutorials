# nextop チュートリアル

[nextop](https://pypi.org/project/nextop/)（エージェント型ワーカーのフレームワーク）を使って、一歩ずつ作っていくサンプルプロジェクトです。バージョンフォルダーごとに、その nextop のバージョンに合わせたチュートリアルが英語・韓国語・日本語で入っています。どのチュートリアルも、試した nextop のバージョンに固定されています。

[English](README.md) | [한국어](README.ko.md) | 日本語

- ホームページ: https://nextop.nextopologix.com
- YouTube（チュートリアル動画）: https://www.youtube.com/@nextopologix

| バージョン | nextop | チュートリアル |
|---|---|---|
| [`v0.4.0/`](v0.4.0/) | 0.4.0 (`pip install nextop==0.4.0`) | [日本語](v0.4.0/ja/)、[英語](v0.4.0/en/)、[韓国語](v0.4.0/ko/): ヘアサロンの予約チャット、株価見通しメール、PDF を A4 一枚に要約、MCP サーバーでリンク要約、PDF を PowerPoint に |

[`v0.4.0/ja/README.md`](v0.4.0/ja/README.md) から始めてください。Windows ではチュートリアルフォルダーの `setup.bat` を実行すると、そのチュートリアルに必要なライブラリ（固定された nextop を含む）を `.venv` に入れ、`.env.example` から `.env` を作ります。API キーは `.env` に自分で入れます。

## ライセンス

このリポジトリのチュートリアルのファイルは [MIT ライセンス](LICENSE) です。チュートリアルが動く nextop プラットフォームは別のパッケージで、独自のライセンスに従います（[PyPI の nextop](https://pypi.org/project/nextop/)）。
