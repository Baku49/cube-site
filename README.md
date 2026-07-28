# キューブドラフト保管庫 (cube draft site)

Gakuが管理するキューブドラフトの情報サイト。

- `src/<cube>/` … 原稿(Googleドキュメントから取得したMarkdown)
- `build.py` … サイトジェネレータ (`python3 build.py` で `docs/` を再生成)
- `docs/` … 公開されるHTML (GitHub Pages: main ブランチ /docs)

更新はClaudeがGoogleドライブの原稿を読み取り、再生成してプッシュする。
