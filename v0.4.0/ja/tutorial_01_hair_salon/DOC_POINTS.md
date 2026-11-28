# あとで README に入れること（まだ書いていないこと）

- サロン案内やメニュー（営業時間、定休日、スタイリスト、料金、所要時間）を変えたら、受付ワーカーの reply_checks（workers/reception/worker.json）に貼ってあるお店の事実も直します。回答の LLM 検査はサロン案内の文書を見ません。
- 電話番号は nextop 自身の phone フィールド型を使い、電話番号のフィールドに `"country": "JP"` を付けています（file_servers/bookings と customers の type.json）。表のキーは E.164（+819012345678）です。functions/_salon.py の `mobile()` も同じ部品で読むので、記録した番号と予約の番号がそのまま比べられます。プラットフォームから部品をコピー（eject）していません。
- 回答の検査（workers/reception/reply_check.py）は、ひらがな・カタカナ・漢字（々 〆 ヶ 〇 を含む）以外の文字（ラテン文字、全角英字、ハングルなど）を断ります。メニューのスタイル名はそのまま通ります。漢字だけで書かれた中国語は漢字と区別できないので通ります。

## スタイルメニュー（salon.json）の出典（2026-11-28 に確認）

スタイル名は 2026 年の日本の美容院・トレンド記事で使われている名前です。料金は税込の円で、相場（女性の1回の平均利用額 約7,700円、男性 約4,900円）に合わせた街のサロンの値です。所要時間は 30 分の枠の倍数で、スタイリストの勤務時間に収まるようにしました。

- ウルフカット、ハッシュカット、韓国風レイヤー: MAQUIA ヘアカタログ https://maquia.hpplus.jp/catalog/hair/120902/ 、美的 https://www.biteki.com/442213/ 、Oggi https://oggi.jp/6905344
- メンズ（マッシュ、センターパート、フェード、ツイストスパイラルパーマ、ニュアンスパーマ）: FASHIONSNAP 2026 メンズショート https://www.fashionsnap.com/article/2026-mens-short/ 、楽天ビューティ https://beauty.rakuten.co.jp/style/men/style72/ 、Smartlog https://smartlog.jp/46507
- 料金の相場（美容センサス 2025 を引いた記事）: pricey.jp https://pricey.jp/web/articles/4804 、DIME https://dime.jp/genre/1812808/ 、ファイナンシャルフィールド https://financial-field.com/living/entry-356078
