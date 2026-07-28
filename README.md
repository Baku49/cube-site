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
