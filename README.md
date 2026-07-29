# がくたそのキューブ (cube draft site)

Gakuが管理するキューブドラフトの情報サイト。

- `src/<cube>/` … 原稿(Googleドキュメントから取得したMarkdown)
- `build.py` … サイトジェネレータ (`python3 build.py` で `docs/` を再生成)
- `docs/` … 公開されるHTML (GitHub Pages: main ブランチ /docs)

## 原稿の対応(Googleドライブ)

| ページ | 原稿ドキュメント | src ファイル |
|---|---|---|
| メタキューブ ルール | ID 166EgUy_Bd7IdvhoU9_p3mQAj8O3XQ7cXewzUI_aQado | src/metacube/rule.md |
| メタキューブ 用語 | ID 1J_ZNP7-hkUf9jhW6ssIsJnpW6ZJpkMqy9g_sVAvVQOI | src/metacube/glossary.md |
| メタキューブ サマリー(スライド) | ID 1vemdrn-aeI7zEZFir_HxM8Gl2CudUUmQibp8_VM6tKo | src/metacube/summary_content.html (手動整形) |
| デュエマパワドラ ルール | ID 1y8vOhy2ePa68u6z7F-MfNCEDJ2injUygMH5-Ynasqmw | src/dm-powdra/rule.md |
| デュエマパワドラ 用語集 | ID 154HAdMSDP45MRkcfRE9-u6PmwdtAHEVkRds_PX6d360 | src/dm-powdra/glossary.md |
| デュエマパワドラ ルールエイドとヒント | ID 14ct3I7KEmzHfiDnZBT_ngYwVAgYnWbqiQUdJn83lug0 | src/dm-powdra/aid.md |

用語集の書式: メタキューブは「用語␣(全角スペース)␣説明」、デュエマパワドラは「用語：説明」、セクション見出しはそれぞれ「・」「◯」始まり。

更新はClaudeがGoogleドライブの原稿を読み取り、srcに反映して再生成しプッシュする。

## 変更履歴(必須の運用ルール)

各キューブに `changelog.html`(変更履歴ページ)があり、`docs/<cube>/data/changelog.json` を表示する。

**今後、カードリストに入れ替え(カードの追加・削除)が発生したら、必ず changelog.json の配列の先頭に以下の形式でエントリを追記すること:**

```json
{
 "date": "YYYY-MM-DD",
 "note": "変更の概要(任意)",
 "added": ["入ったカード名", "..."],
 "removed": ["抜けたカード名", "..."]
}
```

- 新しい順(先頭が最新)。同名複数枚の枚数変動は「カード名 ×2→×1」のように名前に付記する
- 差分の取り方: 変更前のリスト(metacube: `src/metacube/cubecobra_latest.csv` / dm-powdra・all-in: `docs/<cube>/data/cards.json` の旧版)と新リストを突き合わせる
- カード名の表記はカードリストページと同じもの(シート/Cube Cobraの表記)を使う
- イラスト差し替えやページ機能追加など、リストの中身が変わらない変更は記録不要
