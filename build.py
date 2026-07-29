# -*- coding: utf-8 -*-
"""キューブドラフト情報サイト ジェネレータ
src/<cube>/ 配下の原稿から docs/ 配下のHTMLを生成する。
使い方: python3 build.py

構造:
  docs/index.html            … サイトトップ(キューブ一覧)
  docs/<slug>/index.html     … 各キューブのトップ
  docs/<slug>/rules.html     … ルール (src/<slug>/rule.md から生成)
  docs/<slug>/glossary.html  … 用語集 (src/<slug>/glossary.md から生成)
  docs/<slug>/cards.html     … カードリスト置き場(現在は準備中表示)
"""
import re, html, datetime, pathlib
import markdown

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
OUT = ROOT / "docs"
OUT.mkdir(exist_ok=True)

UPDATED = datetime.date.today().strftime("%Y年%m月%d日")

SITE_NAME = "がくたそのキューブ"
SITE_SUB = "GAKUTASO'S CUBE DRAFTS"

# ---------------- キューブ定義 ----------------
CUBES = [
    {
        "slug": "metacube",
        "name": "メタキューブ",
        "tags": ["MTG", "コマンダー", "パワード", "2〜6人(推奨4人)"],
        "desc": "コマンダーとその変種ルールで遊ぶ、カードパワー上限をほぼ設けないマジック：ザ・ギャザリングのキューブドラフト。",
        "cardlist_url": "https://cubecobra.com/cube/list/MetaCube",
        "cardlist_label": "Cube Cobra",
        "has_content": True,
        "src_dir": "metacube",
        "art": "art_crop.webp",
        "has_summary": True,
        "has_aid": False,
        "glossary_style": "metacube",
        "cards_app": True,
    },
    {
        "slug": "dm-powdra",
        "name": "デュエマパワドラ",
        "tags": ["デュエル・マスターズ", "殿堂ゼロ", "3〜6人"],
        "desc": "殿堂ゼロルールで遊ぶ、デュエル・マスターズのパワードキューブドラフト。",
        "cardlist_url": None,
        "cardlist_label": None,
        "has_content": True,
        "src_dir": "dm-powdra",
        "art": "dm_theme.webp",
        "art_overlay": (".25", ".85"),
        "art_in_header": True,
        "has_summary": False,
        "has_aid": True,
        "glossary_style": "dm",
    },
    {
        "slug": "all-in",
        "name": "オールイン",
        "tags": ["遊戯王OCG", "パワード", "2～8人"],
        "desc": "「強すぎる」という理由でカードを不採用にしない理念のもと、ハイパワーカードを詰め込んだ遊戯王OCGのキューブドラフト。グッドスタッフ要素が強く、カテゴリ中心の近年の遊戯王とは異なる体験を提供する。",
        "cardlist_url": None,
        "cardlist_label": None,
        "has_content": True,
        "src_dir": "all-in",
        "art": "allin_theme.webp",
        "art_overlay": (".3", ".88"),
        "art_in_header": True,
        "has_summary": False,
        "has_aid": False,
        "has_glossary": False,
        "has_hint": True,
        "cards_app": True,
    },
]

CSS = r"""
:root{
  --bg:#0c0e13; --bg2:#12151d; --panel:#171b25; --panel2:#1d222e;
  --line:#2a3040; --text:#e8e4d8; --muted:#9a94a8; --gold:#c9a86a; --gold2:#e3c98f;
  --w:#f5f0d8; --u:#4f9edb; --b:#a48ac2; --r:#e05b4b; --g:#57a05e;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);
  font-family:"Noto Sans JP","Hiragino Kaku Gothic ProN",sans-serif;
  font-size:16px;line-height:1.9;}
a{color:var(--gold2);text-decoration:none}
a:hover{text-decoration:underline}
.mana-strip{height:4px;background:linear-gradient(90deg,var(--w),var(--u),var(--b),var(--r),var(--g));}
header.site{position:sticky;top:0;z-index:50;background:rgba(12,14,19,.92);
  backdrop-filter:blur(8px);border-bottom:1px solid var(--line);}
.site-inner{max-width:1040px;margin:0 auto;padding:.6rem 1.2rem;
  display:flex;align-items:center;gap:1rem;flex-wrap:wrap;}
.brand{font-family:"Shippori Mincho",serif;font-weight:700;font-size:1.05rem;
  letter-spacing:.1em;color:var(--gold2);white-space:nowrap;line-height:1.3}
.brand .sub{font-size:.62rem;color:var(--muted);letter-spacing:.22em;display:block}
.cube-switch{display:flex;align-items:center;gap:.5rem}
.cube-switch select{background:var(--panel);color:var(--gold2);border:1px solid var(--line);
  border-radius:8px;padding:.35rem .6rem;font-size:.92rem;font-family:inherit;cursor:pointer}
.cube-switch select:focus{outline:none;border-color:var(--gold)}
nav.main{display:flex;gap:.2rem;flex-wrap:wrap;margin-left:auto;align-items:center}
nav.main a{padding:.35rem .8rem;border-radius:6px;color:var(--text);font-size:.92rem}
nav.main a:hover{background:var(--panel2);text-decoration:none}
nav.main a.active{background:var(--panel2);color:var(--gold2);border:1px solid var(--line)}
nav.main span.disabled{padding:.35rem .8rem;color:var(--muted);font-size:.92rem;cursor:default}
.badge{font-size:.65rem;border:1px solid var(--line);border-radius:999px;
  padding:.05rem .45rem;color:var(--muted);margin-left:.3rem;vertical-align:middle}
main{max-width:1040px;margin:0 auto;padding:1.6rem 1.2rem 4rem;}
.hero{padding:3.2rem 1.2rem 2.6rem;text-align:center;position:relative;
  background:radial-gradient(ellipse at 50% -20%, #232a3d 0%, transparent 60%);}
.hero.art{background-size:cover;background-position:center 30%;
  padding:4.6rem 1.2rem 3.4rem;border-bottom:1px solid var(--line);}
.hero.art h1,.hero.art p{text-shadow:0 2px 14px rgba(0,0,0,.95),0 0 4px rgba(0,0,0,.9)}
.hero.art p{color:#d9d3c2}
.hero h1{font-family:"Shippori Mincho",serif;font-size:2.3rem;letter-spacing:.15em;
  margin:.2rem 0 .6rem;color:var(--gold2);}
.hero p{color:var(--muted);max-width:620px;margin:.4rem auto}
h1.page{font-family:"Shippori Mincho",serif;font-size:1.9rem;letter-spacing:.1em;
  color:var(--gold2);border-bottom:1px solid var(--line);padding-bottom:.5rem;margin:.5rem 0 1.2rem}
.updated{color:var(--muted);font-size:.82rem;margin-bottom:1.6rem}
/* ---- article (rules) ---- */
article.doc h1{font-family:"Shippori Mincho",serif;font-size:1.45rem;color:var(--gold2);
  letter-spacing:.06em;margin:2.6rem 0 1rem;padding:.5rem .9rem;
  background:linear-gradient(90deg,var(--panel) 0%,transparent 100%);
  border-left:4px solid var(--gold);border-radius:3px;}
article.doc h2{font-family:"Shippori Mincho",serif;font-size:1.2rem;color:var(--gold2);
  margin:2rem 0 .8rem;padding-left:.7rem;border-left:3px solid var(--u);}
article.doc h3{font-size:1.05rem;color:var(--text);margin:1.6rem 0 .6rem;
  padding-left:.7rem;border-left:3px solid var(--r);}
article.doc h4{font-size:1rem;color:var(--gold2);margin:1.4rem 0 .4rem;}
article.doc p{margin:.55rem 0}
article.doc strong{color:var(--gold2)}
article.doc a{border-bottom:1px dotted var(--gold)}
.toc{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:1rem 1.4rem;margin:0 0 1.5rem;}
.toc .toc-title{font-size:.8rem;letter-spacing:.25em;color:var(--muted);margin-bottom:.5rem}
.toc ol{margin:0;padding-left:1.2rem}
.toc li{margin:.15rem 0;font-size:.95rem}
.toc ol ol{padding-left:1.1rem;font-size:.9rem}
/* ---- cards (top page) ---- */
.cube-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:1.2rem;margin-top:1.4rem}
.cube-card{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:14px;padding:1.4rem 1.5rem;position:relative;overflow:hidden;}
.cube-card::before{content:"";position:absolute;inset:0 0 auto 0;height:3px;z-index:2;
  background:linear-gradient(90deg,var(--w),var(--u),var(--b),var(--r),var(--g));}
.card-art{height:130px;margin:-1.4rem -1.5rem 1rem;background-size:cover;background-position:center 30%;
  border-bottom:1px solid var(--line);}
.cube-card h2{font-family:"Shippori Mincho",serif;margin:.2rem 0 .5rem;font-size:1.35rem;
  letter-spacing:.08em;color:var(--gold2)}
.cube-card p{color:var(--muted);font-size:.92rem;margin:.3rem 0 .9rem}
.tags{display:flex;gap:.4rem;flex-wrap:wrap;margin-bottom:1rem}
.tag{font-size:.72rem;padding:.15rem .55rem;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.btns{display:flex;gap:.6rem;flex-wrap:wrap}
.btn{display:inline-block;padding:.45rem 1rem;border-radius:8px;font-size:.9rem;
  border:1px solid var(--gold);color:var(--gold2)}
.btn:hover{background:var(--gold);color:#14100a;text-decoration:none}
.btn.ghost{border-color:var(--line);color:var(--text)}
.btn.ghost:hover{background:var(--panel2);color:var(--text)}
.btn.disabled{border-color:var(--line);color:var(--muted);pointer-events:none}
.cube-card.coming{opacity:.6}
/* ---- card list ---- */
.cl-main{max-width:1200px}
.cl-controls{position:sticky;top:56px;z-index:40;background:rgba(12,14,19,.96);
  backdrop-filter:blur(8px);padding:.8rem 0;border-bottom:1px solid var(--line);margin-bottom:1rem}
.cl-btnrow{display:flex;gap:.6rem;align-items:center;margin-top:.6rem;flex-wrap:wrap}
.cl-toggle{display:flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.cl-tbtn{background:var(--panel);color:var(--muted);border:none;padding:.4rem .9rem;
  font-size:.9rem;cursor:pointer;font-family:inherit}
.cl-tbtn.active{background:var(--panel2);color:var(--gold2)}
button.cl-tbtn#cl-history{border:1px solid var(--line);border-radius:8px}
.cl-count{color:var(--muted);font-size:.85rem;margin-left:auto}
.cl-seccount{font-size:.8rem;color:var(--muted);font-family:"Noto Sans JP",sans-serif;margin-left:.4rem}
.cl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:.7rem;margin:.8rem 0 1.6rem}
.cl-card{position:relative;cursor:pointer;border-radius:8px;transition:transform .12s}
.cl-card:hover{transform:translateY(-3px)}
.cl-card img{width:100%;border-radius:8px;display:block;background:var(--panel);min-height:120px}
.cl-badge{position:absolute;top:6px;right:6px;background:rgba(0,0,0,.85);color:var(--gold2);
  border:1px solid var(--gold);border-radius:999px;padding:.05rem .5rem;font-size:.8rem;font-weight:700}
.cl-errata{position:absolute;top:6px;left:6px;background:#7a2a1e;color:#ffd9cc;border-radius:4px;
  padding:.02rem .35rem;font-size:.72rem;font-weight:700}
.cl-errata-inline{font-size:.68rem;background:#7a2a1e;color:#ffd9cc;border-radius:4px;padding:.05rem .3rem}
.cl-names{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:.3rem;margin:.8rem 0 1.6rem}
.cl-nameitem{text-align:left;background:var(--panel);border:1px solid var(--line);color:var(--text);
  border-radius:7px;padding:.35rem .7rem;font-size:.9rem;cursor:pointer;font-family:inherit}
.cl-nameitem:hover{border-color:var(--gold);color:var(--gold2)}
.cl-nbadge{color:var(--gold2);font-weight:700}
.cl-modal{position:fixed;inset:0;z-index:100;display:flex;align-items:center;justify-content:center}
.cl-modal-back{position:absolute;inset:0;background:rgba(0,0,0,.75)}
.cl-modal-box{position:relative;background:var(--bg2);border:1px solid var(--gold);border-radius:14px;
  max-width:880px;width:calc(100% - 2rem);max-height:88vh;overflow-y:auto;padding:1.4rem 1.6rem;
  box-shadow:0 20px 60px rgba(0,0,0,.8)}
.cl-close{position:absolute;top:.6rem;right:.8rem;background:none;border:none;color:var(--muted);
  font-size:1.6rem;cursor:pointer;line-height:1}
.cl-close:hover{color:var(--gold2)}
.cl-h2{font-family:"Shippori Mincho",serif;color:var(--gold2);margin:.2rem 0 1rem}
.cl-detail{display:flex;gap:1.4rem;flex-wrap:wrap}
.cl-detail-imgs{flex:0 0 260px;display:flex;flex-direction:column;gap:.7rem}
.cl-detail-imgs img{width:260px;border-radius:12px}
.cl-detail-info{flex:1;min-width:260px}
.cl-cardname{font-family:"Shippori Mincho",serif;font-size:1.3rem;color:var(--gold2);font-weight:700}
.cl-en{color:var(--muted);font-size:.85rem;margin-bottom:.3rem}
.cl-line{margin:.3rem 0}
.cl-type{color:var(--text);font-weight:600;margin:.4rem 0;border-bottom:1px solid var(--line);padding-bottom:.4rem}
.cl-text{margin:.6rem 0;line-height:1.8;font-size:.95rem}
.cl-flavor{margin:.6rem 0;color:var(--muted);font-style:italic;font-size:.88rem;
  border-left:2px solid var(--line);padding-left:.7rem}
.cl-pt{text-align:right;font-weight:700;color:var(--gold2);font-size:1.05rem}
.cl-metainfo{color:var(--muted);font-size:.8rem;margin-top:.7rem;border-top:1px solid var(--line);padding-top:.5rem}
.cl-noja{color:#c9a06a}
.cl-ovnote{background:#3a2018;border:1px solid #7a2a1e;color:#ffd9cc;border-radius:8px;
  padding:.5rem .8rem;margin-bottom:.8rem;font-size:.88rem}
.cl-orig{margin:.8rem 0;color:var(--muted)}
.cl-orig summary{cursor:pointer;font-size:.85rem}
.cl-hr{border:none;border-top:1px solid var(--line);margin:.8rem 0}
.cl-logentry{border:1px solid var(--line);border-radius:10px;padding:.8rem 1rem;margin:.6rem 0;background:var(--panel)}
.cl-logdate{color:var(--gold2);font-weight:700}
.cl-lognote{margin:.2rem 0;color:var(--text)}
.cl-logadd{color:#9fd3a8;font-size:.85rem;margin-top:.3rem;line-height:1.7}
.cl-logrem{color:#e8a89a;font-size:.85rem;margin-top:.3rem;line-height:1.7}
/* ---- wild card sets (all-in) ---- */
.cl-set-stack{position:relative;width:100%;padding-top:150%}
.cl-set-img{position:absolute;width:76%;border-radius:7px;background:var(--panel);
  box-shadow:2px 3px 10px rgba(0,0,0,.65);display:block}
.cl-si0{left:0;top:0;z-index:3}
.cl-si1{left:12%;top:5%;z-index:2}
.cl-si2{left:24%;top:10%;z-index:1}
.cl-sn2.cl-si0{left:0;top:0}.cl-sn2.cl-si1{left:16%;top:7%}
.cl-set:hover .cl-set-img{box-shadow:2px 3px 14px rgba(0,0,0,.85)}
.cl-wtag{position:absolute;bottom:6px;left:6px;background:rgba(20,16,10,.9);color:var(--gold2);
  border:1px solid var(--gold);border-radius:4px;padding:.02rem .4rem;font-size:.72rem;font-weight:700}
.cl-wtag-in{font-size:.7rem;background:rgba(20,16,10,.9);color:var(--gold2);
  border:1px solid var(--gold);border-radius:4px;padding:.05rem .3rem}
.cl-set-no{color:var(--muted);font-size:.8rem;letter-spacing:.15em;margin:.2rem 0 .4rem}
.ms{display:inline-flex;align-items:center;justify-content:center;width:1.25rem;height:1.25rem;
  border-radius:50%;font-size:.72rem;font-weight:700;margin:0 1px;vertical-align:-3px;color:#1a1a1a}
.ms.mw{background:#f8f4d8}.ms.mu{background:#9ec6e8}.ms.mb{background:#b8a8c8}
.ms.mr{background:#e8a898}.ms.mg{background:#a8cbaa}.ms.mc{background:#c8c4bc}
/* ---- 準備中 ---- */
.wip{background:var(--panel);border:1px dashed var(--line);border-radius:14px;
  text-align:center;padding:3.5rem 1.5rem;margin-top:1.5rem;color:var(--muted)}
.wip .wip-mark{font-family:"Shippori Mincho",serif;font-size:1.4rem;color:var(--gold2);
  letter-spacing:.3em;margin-bottom:.8rem}
/* ---- summary ---- */
.sum-grid{display:grid;grid-template-columns:1fr 1fr;gap:1.2rem}
.sum-span2{grid-column:1/-1}
.sum-panel{background:linear-gradient(160deg,var(--panel2),var(--panel));border:1px solid var(--line);
  border-radius:14px;padding:1.3rem 1.5rem;position:relative;overflow:hidden}
.sum-panel::before{content:"";position:absolute;inset:0 0 auto 0;height:3px;
  background:linear-gradient(90deg,var(--w),var(--u),var(--b),var(--r),var(--g));}
.sum-title{font-family:"Shippori Mincho",serif;color:var(--gold2);font-size:1.2rem;
  letter-spacing:.08em;margin:.3rem 0 .9rem;display:flex;align-items:center;gap:.5rem}
.sum-num{color:var(--gold)}
.sum-note{font-size:.8rem;color:var(--muted);font-family:"Noto Sans JP",sans-serif;margin-left:.4rem}
.sum-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:.8rem}
.sum-stat{background:var(--bg2);border:1px solid var(--line);border-radius:10px;
  text-align:center;padding:1rem .6rem}
.sum-stat .v{font-family:"Shippori Mincho",serif;font-size:1.7rem;color:var(--gold2);line-height:1.2}
.sum-stat .l{color:var(--muted);font-size:.82rem;margin-top:.3rem;line-height:1.5}
.sum-list{margin:.4rem 0;padding-left:1.3rem}
.sum-list li{margin:.25rem 0}
.sum-em{color:var(--gold2);font-weight:700}
.sum-formula{background:var(--bg2);border:1px solid var(--gold);border-radius:10px;
  padding:.7rem 1rem;text-align:center;color:var(--gold2);font-weight:700;letter-spacing:.02em}
.sum-sub{color:var(--muted);margin:.8rem 0 .2rem}
.sum-banner{margin-top:1rem;background:linear-gradient(90deg,#2a1e1e,#1d1622);
  border:1px solid var(--r);border-radius:10px;padding:.8rem 1rem;text-align:center;line-height:1.7}
.sum-banner strong{color:#f0b8a8}
.sum-cards{display:flex;gap:.7rem;flex-wrap:wrap;margin-top:.9rem}
.sum-cards img{width:130px;border-radius:7px;border:1px solid var(--line);
  box-shadow:0 4px 14px rgba(0,0,0,.5)}
.sum-cards-cap{align-items:flex-start}
.sum-cards-cap figure{margin:0;width:170px}
.sum-cards-cap img{width:150px}
.sum-cards-cap figcaption{font-size:.74rem;color:var(--muted);line-height:1.6;margin-top:.4rem}
.sum-steps{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:1rem}
.sum-step{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem}
.sum-step p{font-size:.92rem;margin:.45rem 0;line-height:1.75}
.sum-step strong{color:var(--gold2)}
.sum-step-head{font-family:"Shippori Mincho",serif;color:var(--gold2);font-size:1.05rem;
  margin-bottom:.4rem;display:flex;align-items:center;gap:.5rem}
.step-badge{display:inline-flex;align-items:center;justify-content:center;width:1.7rem;height:1.7rem;
  border-radius:50%;border:1px solid var(--gold);color:var(--gold2);font-size:.95rem;flex:none}
@media(max-width:760px){.sum-grid{grid-template-columns:1fr}}
/* ---- glossary ---- */
.g-controls{position:sticky;top:56px;z-index:40;background:rgba(12,14,19,.95);
  backdrop-filter:blur(8px);padding:.8rem 0;border-bottom:1px solid var(--line);margin-bottom:1.2rem}
.g-search{width:100%;padding:.65rem 1rem;font-size:1rem;border-radius:10px;
  border:1px solid var(--line);background:var(--panel);color:var(--text);outline:none}
.g-search:focus{border-color:var(--gold)}
.g-cats{display:flex;gap:.45rem;flex-wrap:wrap;margin-top:.6rem}
.g-cat{padding:.28rem .8rem;border-radius:999px;font-size:.85rem;cursor:pointer;
  border:1px solid var(--line);background:var(--panel);color:var(--muted)}
.g-cat.active{border-color:var(--gold);color:var(--gold2);background:var(--panel2)}
.g-count{color:var(--muted);font-size:.82rem;margin:.5rem 0 1rem}
.g-section-title{font-family:"Shippori Mincho",serif;color:var(--gold2);font-size:1.25rem;
  letter-spacing:.08em;margin:2rem 0 .4rem;padding-left:.7rem;border-left:4px solid var(--gold)}
.g-section-note{color:var(--muted);font-size:.88rem;margin:0 0 1rem;padding-left:.9rem}
.entry{background:var(--panel);border:1px solid var(--line);border-radius:10px;
  padding:.9rem 1.2rem;margin:.6rem 0;}
.entry dt{font-weight:700;color:var(--gold2);font-size:1.02rem;margin-bottom:.25rem}
.entry dd{margin:0;color:var(--text);font-size:.95rem;line-height:1.85}
.hidden{display:none}
footer.site{border-top:1px solid var(--line);color:var(--muted);font-size:.82rem;
  text-align:center;padding:1.6rem 1rem 2.2rem;}
@media(max-width:640px){
  body{font-size:15px}
  .hero h1{font-size:1.7rem}
  .site-inner{padding:.6rem .8rem;gap:.6rem}
  nav.main{margin-left:0}
}
"""

FOOT_NOTE = "本サイトはファンコンテンツです。各カードゲームの名称・カード情報はそれぞれの権利者に帰属します。"


def cube_switcher(current_slug, depth):
    """ヘッダーのキューブ切り替えプルダウン"""
    prefix = "../" if depth == 1 else ""
    opts = f'<option value="{prefix}index.html">キューブを選択…</option>' if current_slug is None else ""
    for c in CUBES:
        sel = " selected" if c["slug"] == current_slug else ""
        opts += f'<option value="{prefix}{c["slug"]}/index.html"{sel}>{c["name"]}</option>'
    return (
        '<div class="cube-switch"><select aria-label="キューブ切り替え" '
        'onchange="if(this.value)location.href=this.value">' + opts + "</select></div>"
    )


def page(title, body, *, cube=None, active="", depth=0):
    root = "../" if depth == 1 else ""
    if cube is None:
        nav = f'<a href="{root}index.html" class="active">キューブ一覧</a>'
    else:
        items = []
        items.append(("index", f'{cube["slug"]}トップ' if False else "キューブトップ", "index.html", True))
        items.append(("rules", "ルール", "rules.html", cube["has_content"]))
        if cube.get("has_summary"):
            items.append(("summary", "ルールサマリー", "summary.html", True))
        if cube.get("has_glossary", True):
            items.append(("glossary", "用語集", "glossary.html", cube["has_content"]))
        if cube.get("has_aid"):
            items.append(("aid", "ルールエイドとヒント", "aid.html", True))
        if cube.get("has_hint"):
            items.append(("hint", "ヒント", "hint.html", True))
        elif cube.get("hint_pending"):
            items.append(("hint", "ヒント", "hint.html", False))
        items.append(("cards", "カードリスト", "cards.html", True))
        nav = f'<a href="{root}index.html">キューブ一覧</a>'
        for key, label, href, enabled in items:
            if not enabled:
                nav += f'<span class="disabled">{label}<span class="badge">準備中</span></span>'
            else:
                cls = ' class="active"' if key == active else ""
                nav += f'<a href="{href}"{cls}>{label}</a>'
    switcher = cube_switcher(cube["slug"] if cube else None, depth)
    header_style = ""
    if cube and cube.get("art_in_header") and cube.get("art"):
        art_url = root + "assets/" + cube["art"]
        header_style = (' style="background-image:linear-gradient(rgba(12,14,19,.82),rgba(12,14,19,.9)),'
                        + "url('" + art_url + "');background-size:cover;background-position:center 30%" + '"')
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&family=Shippori+Mincho:wght@600;700&display=swap" rel="stylesheet">
<style>{CSS}</style>
</head>
<body>
<div class="mana-strip"></div>
<header class="site"{header_style}>
  <div class="site-inner">
    <a href="{root}index.html" style="text-decoration:none"><div class="brand">{SITE_NAME}<span class="sub">{SITE_SUB}</span></div></a>
    {switcher}
    <nav class="main">{nav}</nav>
  </div>
</header>
{body}
<footer class="site">
  最終更新日: {UPDATED}<br>
  {FOOT_NOTE}
</footer>
</body>
</html>"""


# ---------------- ルール/記事ページ共通 ----------------
def article_html(md_text):
    """markdown -> (toc_html, body_html)"""
    body_html = markdown.markdown(md_text, extensions=["extra"])
    toc_items = []
    counter = [0]

    def clean(t):
        return t.lstrip("・◯○ ")

    def add_id(m):
        level, text = m.group(1), m.group(2)
        counter[0] += 1
        hid = f"sec{counter[0]}"
        toc_items.append((int(level), hid, clean(re.sub(r"<[^>]+>", "", text))))
        return f'<h{level} id="{hid}">{clean(text)}</h{level}>'

    body_html = re.sub(r"<h([12])>(.*?)</h\1>", add_id, body_html)
    body_html = re.sub(r"<h([34])>([・◯○]?)(.*?)</h\1>", lambda m: f"<h{m.group(1)}>{m.group(3)}</h{m.group(1)}>", body_html)

    toc_html = '<div class="toc"><div class="toc-title">目次</div><ol>'
    open_sub = False
    for level, hid, text in toc_items:
        if level == 1:
            if open_sub:
                toc_html += "</ol></li>"
                open_sub = False
            toc_html += f'<li><a href="#{hid}">{text}</a>'
        else:
            if not open_sub:
                toc_html += "<ol>"
                open_sub = True
            toc_html += f'<li><a href="#{hid}">{text}</a></li>'
    if open_sub:
        toc_html += "</ol></li>"
    toc_html += "</li></ol></div>"
    return toc_html, body_html


def build_article(cube, src_name, out_name, title, active):
    md_text = (SRC / cube["src_dir"] / src_name).read_text(encoding="utf-8")
    toc_html, body_html = article_html(md_text)
    body = f"""
<main>
<h1 class="page">{cube["name"]} {title}</h1>
<div class="updated">最終更新日: {UPDATED}</div>
{toc_html}
<article class="doc">
{body_html}
</article>
</main>"""
    out = OUT / cube["slug"]
    out.mkdir(exist_ok=True)
    (out / out_name).write_text(
        page(f'{title} | {cube["name"]}', body, cube=cube, active=active, depth=1), encoding="utf-8")


def build_rules(cube):
    build_article(cube, "rule.md", "rules.html", "ルール", "rules")


def build_aid(cube):
    build_article(cube, "aid.md", "aid.html", "ルールエイドとヒント", "aid")


# ---------------- メタキューブ: ルールサマリー ----------------
def build_summary(cube):
    frag = (SRC / cube["src_dir"] / "summary_content.html").read_text(encoding="utf-8")
    body = f"""
<main>
<h1 class="page">{cube["name"]} ルールサマリー</h1>
<div class="updated">最終更新日: {UPDATED} ｜ 統率者指定・固有色・対戦ルールの早見表</div>
{frag}
</main>"""
    out = OUT / cube["slug"]
    out.mkdir(exist_ok=True)
    (out / "summary.html").write_text(
        page(f'ルールサマリー | {cube["name"]}', body, cube=cube, active="summary", depth=1), encoding="utf-8")


# ---------------- メタキューブ: 用語集 ----------------
SECTION_DEFS = [
    ("キーワード能力", "keyword"),
    ("キーワード処理", "action"),
    ("定義済みトークン", "token"),
    ("その他のルール用語", "other"),
]


def build_glossary(cube):
    src = SRC / cube["src_dir"] / "glossary.md"
    text = src.read_text(encoding="utf-8")
    style = cube.get("glossary_style", "metacube")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    sections = []
    current = None
    for i, para in enumerate(paragraphs):
        matched = False
        if style == "metacube":
            for name, key in SECTION_DEFS:
                if para.startswith("・" + name):
                    note = para[len("・" + name):].lstrip("：: ").strip()
                    current = {"name": name, "key": key, "note": note, "entries": []}
                    sections.append(current)
                    matched = True
                    break
        else:  # dm: ◯で始まる1行段落がセクション見出し
            if para.startswith("◯") and "\n" not in para:
                name = para.lstrip("◯").strip()
                current = {"name": name, "key": f"sec{len(sections)}", "note": "", "entries": []}
                sections.append(current)
                matched = True
        if matched:
            continue
        lines = para.split("\n")
        first = lines[0]
        if style == "dm":
            if "：" in first:
                term, rest = first.split("：", 1)
            else:
                term, rest = first, ""
        elif "　" in first:
            term, rest = first.split("　", 1)
        else:
            sp = first.find(" ")
            term, rest = (first[:sp], first[sp+1:]) if sp > 0 else (first, "")
        desc_lines = [rest.strip()] + [l.strip() for l in lines[1:]]
        desc = "<br>".join(html.escape(l) for l in desc_lines if l)
        if current is None:
            current = {"name": "用語", "key": "other", "note": "", "entries": []}
            sections.append(current)
        current["entries"].append((term.strip(), desc))

    total = sum(len(s["entries"]) for s in sections)
    if len(sections) > 1:
        cats_html = '<button class="g-cat active" data-cat="all">すべて</button>' + "".join(
            f'<button class="g-cat" data-cat="{s["key"]}">{s["name"]}</button>' for s in sections
        )
        cats_html = f'<div class="g-cats">{cats_html}</div>'
    else:
        cats_html = ""
    sections_html = ""
    for s in sections:
        note = f'<p class="g-section-note">{html.escape(s["note"])}</p>' if s["note"] else ""
        entries = "".join(
            f'<dl class="entry" data-cat="{s["key"]}" data-term="{html.escape(t)}">'
            f'<dt>{html.escape(t)}</dt><dd>{d}</dd></dl>'
            for t, d in s["entries"]
        )
        sections_html += (
            f'<section class="g-section" data-cat="{s["key"]}">'
            f'<h2 class="g-section-title">{s["name"]}</h2>{note}{entries}</section>'
        )

    js = r"""
<script>
document.addEventListener('DOMContentLoaded', function(){
  const search = document.getElementById('gsearch');
  const count = document.getElementById('gcount');
  const cats = document.querySelectorAll('.g-cat');
  const entries = document.querySelectorAll('.entry');
  const sections = document.querySelectorAll('.g-section');
  let cat = 'all';
  function norm(s){
    return (s||'').toLowerCase()
      .replace(/[ァ-ン]/g, ch => String.fromCharCode(ch.charCodeAt(0) - 0x60));
  }
  function apply(){
    const q = norm(search.value.trim());
    let visible = 0;
    entries.forEach(e => {
      const okCat = (cat === 'all' || e.dataset.cat === cat);
      const hay = norm(e.dataset.term + ' ' + e.textContent);
      const okQ = !q || hay.includes(q);
      e.classList.toggle('hidden', !(okCat && okQ));
      if (okCat && okQ) visible++;
    });
    sections.forEach(sec => {
      const any = sec.querySelectorAll('.entry:not(.hidden)').length > 0;
      sec.classList.toggle('hidden', !any);
    });
    count.textContent = visible + ' / ' + entries.length + ' 件を表示中';
  }
  search.addEventListener('input', apply);
  cats.forEach(b => b.addEventListener('click', () => {
    cats.forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    cat = b.dataset.cat;
    apply();
  }));
  apply();
});
</script>"""

    body = f"""
<main>
<h1 class="page">{cube["name"]} 用語集</h1>
<div class="updated">最終更新日: {UPDATED} ｜ 全{total}項目</div>
<div class="g-controls">
  <input id="gsearch" class="g-search" type="search" placeholder="用語を検索" autocomplete="off">
  {cats_html}
</div>
<div id="gcount" class="g-count"></div>
{sections_html}
</main>
{js}"""
    out = OUT / cube["slug"]
    out.mkdir(exist_ok=True)
    (out / "glossary.html").write_text(
        page(f'用語集 | {cube["name"]}', body, cube=cube, active="glossary", depth=1), encoding="utf-8")


# ---------------- 各キューブ: カードリスト ----------------
def build_cards(cube):
    if cube.get("cards_app"):
        frag = (SRC / cube["src_dir"] / "cards_app_body.html").read_text(encoding="utf-8")
        out = OUT / cube["slug"]
        out.mkdir(exist_ok=True)
        (out / "cards.html").write_text(
            page(f'カードリスト | {cube["name"]}', frag, cube=cube, active="cards", depth=1), encoding="utf-8")
        return
    ext = ""
    if cube["cardlist_url"]:
        ext = (f'<p style="margin-top:1.2rem"><a class="btn ghost" href="{cube["cardlist_url"]}" '
               f'target="_blank" rel="noopener">それまでは {cube["cardlist_label"]} を参照 ↗</a></p>')
    body = f"""
<main>
<h1 class="page">{cube["name"]} カードリスト</h1>
<div class="wip">
  <div class="wip-mark">─ 準備中 ─</div>
  <p>カードリストのページは現在準備中です。<br>公開までしばらくお待ちください。</p>
  {ext}
</div>
</main>"""
    out = OUT / cube["slug"]
    out.mkdir(exist_ok=True)
    (out / "cards.html").write_text(
        page(f'カードリスト | {cube["name"]}', body, cube=cube, active="cards", depth=1), encoding="utf-8")


# ---------------- 各キューブ: キューブトップ ----------------
def build_cube_index(cube):
    tags = "".join(f'<span class="tag">{t}</span>' for t in cube["tags"])
    if cube["has_content"]:
        btns = '<a class="btn" href="rules.html">ルール</a>'
        if cube.get("has_summary"):
            btns += '<a class="btn" href="summary.html">ルールサマリー</a>'
        if cube.get("has_glossary", True):
            btns += '<a class="btn" href="glossary.html">用語集</a>'
        if cube.get("has_aid"):
            btns += '<a class="btn" href="aid.html">ルールエイドとヒント</a>'
        if cube.get("has_hint"):
            btns += '<a class="btn" href="hint.html">ヒント</a>'
        elif cube.get("hint_pending"):
            btns += '<span class="btn disabled">ヒント(準備中)</span>'
        btns += '<a class="btn" href="cards.html">カードリスト</a>'
        if cube["cardlist_url"]:
            btns += (f'<a class="btn ghost" href="{cube["cardlist_url"]}" target="_blank" '
                     f'rel="noopener">カードリスト ({cube["cardlist_label"]}) ↗</a>')
        content = ""
    else:
        btns = '<span class="btn disabled">ルール(準備中)</span><span class="btn disabled">用語集(準備中)</span><a class="btn" href="cards.html">カードリスト</a>'
        content = """
<div class="wip">
  <div class="wip-mark">─ 準備中 ─</div>
  <p>このキューブの情報は現在準備中です。<br>公開までしばらくお待ちください。</p>
</div>"""
    if cube.get("art"):
        ov1, ov2 = cube.get("art_overlay", (".45", ".94"))
        hero_open = (f'<div class="hero art" style="background-image:linear-gradient(rgba(12,14,19,{ov1}),'
                     f'rgba(12,14,19,{ov2})),url(\'../assets/{cube["art"]}\')">')
    else:
        hero_open = '<div class="hero">'
    body = f"""
{hero_open}
  <h1>{cube["name"]}</h1>
  <p>{cube["desc"]}</p>
</div>
<main>
<div class="tags" style="justify-content:center">{tags}</div>
<div class="btns" style="justify-content:center">{btns}</div>
{content}
</main>"""
    out = OUT / cube["slug"]
    out.mkdir(exist_ok=True)
    (out / "index.html").write_text(
        page(f'{cube["name"]} | {SITE_NAME}', body, cube=cube, active="index", depth=1), encoding="utf-8")


# ---------------- サイトトップ ----------------
def build_site_index():
    cards = ""
    for c in CUBES:
        tags = "".join(f'<span class="tag">{t}</span>' for t in c["tags"])
        if c["has_content"]:
            btns = (f'<a class="btn" href="{c["slug"]}/index.html">キューブトップ</a>'
                    f'<a class="btn ghost" href="{c["slug"]}/rules.html">ルール</a>')
            if c.get("has_glossary", True):
                btns += f'<a class="btn ghost" href="{c["slug"]}/glossary.html">用語集</a>'
            cls = "cube-card"
        else:
            btns = f'<a class="btn ghost" href="{c["slug"]}/index.html">キューブトップ(準備中)</a>'
            cls = "cube-card coming"
        art = f'<div class="card-art" style="background-image:url(assets/{c["art"]})"></div>' if c.get("art") else ""
        cards += f"""
  <div class="{cls}">
    {art}
    <h2>{c["name"]}</h2>
    <div class="tags">{tags}</div>
    <p>{c["desc"]}</p>
    <div class="btns">{btns}</div>
  </div>"""
    body = f"""
<div class="hero art" style="background-image:linear-gradient(rgba(12,14,19,.5),rgba(12,14,19,.94)),url('assets/art_crop2.webp')">
  <h1>{SITE_NAME}</h1>
  <p>管理中のキューブドラフトの情報を公開しています。<br>各キューブのルール・用語集・カードリストは随時更新されます。</p>
</div>
<main>
<div class="cube-grid">{cards}
</div>
</main>"""
    (OUT / "index.html").write_text(page(SITE_NAME, body, cube=None, depth=0), encoding="utf-8")


def copy_assets():
    import shutil
    a = SRC / "assets"
    if a.is_dir():
        dest = OUT / "assets"
        dest.mkdir(exist_ok=True)
        for f in a.rglob("*"):
            if f.is_file():
                target = dest / f.relative_to(a)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)


if __name__ == "__main__":
    copy_assets()
    build_site_index()
    for c in CUBES:
        build_cube_index(c)
        build_cards(c)
        if c["has_content"]:
            build_rules(c)
            if c.get("has_summary"):
                build_summary(c)
            if c.get("has_aid"):
                build_aid(c)
            if c.get("has_hint"):
                build_article(c, "hint.md", "hint.html", "ヒント", "hint")
            if c.get("has_glossary", True):
                build_glossary(c)
    gen = sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*.html"))
    print("generated:")
    for g in gen:
        print(" ", g)
