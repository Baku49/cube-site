#!/usr/bin/env python3
"""メタキューブ コンボ一覧更新スクリプト

入力: --raw   Cube Cobra /cube/api/getcombos (Commander Spellbook) をスリム化したJSON
      --tr    翻訳辞書JSON (複数可): {英文: 和文}  (手順行・前提行)
      --feat  結果(feature)名の翻訳辞書 {英名: 和名}
      --date  更新日
既存 docs/metacube/data/combos.json の翻訳済みコンボ(id一致)は手順・前提の訳を引き継ぐ。
カード名・画像・結果・人気度は最新データから再生成する。
"""
import argparse, json, re

ROOT = '/home/claude/metacube-site'
DATA = ROOT + '/docs/metacube/data'
ZONE = {'B': '戦場', 'H': '手札', 'G': '墓地', 'C': '統率領域', 'E': '追放領域', 'L': 'ライブラリー'}
SYM = {'W': '白', 'U': '青', 'B': '黒', 'R': '赤', 'G': '緑', 'C': '◇', 'T': 'T', 'X': 'X', 'S': '氷'}
REQ = {
    'Haste Enabler': '速攻を与える手段がある。',
    'Persist Creature': '頑強を持つクリーチャーをコントロールしている。',
    'Creature that earthbends on entering': '戦場に出たときに土の技を行うクリーチャーが手札にある。',
    'Card that Animates an Artifact': 'アーティファクトをクリーチャー化するカードが手札か戦場にある。',
    'Mana Dork or Mana Dork Creator': 'マナ・クリーチャー(またはそれを生成するカード)をコントロールしている。',
    'Creature with "When this creature ETBs, create 2+ creature tokens"': '「戦場に出たとき、クリーチャー・トークンを2体以上生成する」クリーチャーをコントロールしている。',
    'Artifact / Creature with "{T}: Add Mana" that can tap upon ETB (Mana Rock)': '戦場に出てすぐタップできる「(T)：マナを加える」を持つアーティファクトかクリーチャー(マナ・ロック)をコントロールしている。',
}
STATE = {
    'without summoning sickness': '{X}が召喚酔いしていない。',
    'is a creature without summoning sickness': '{X}がクリーチャーであり、召喚酔いしていない。',
    'attached to a creature you control': '{X}が自軍クリーチャーについている。',
    'attached to the mana-producing creature': '{X}がマナを生み出すクリーチャーについている。',
    'attached to [creature]': '{X}がクリーチャーについている。',
    'is paired with another creature': '{X}が他のクリーチャーと組んでいる。',
    'with two or more +1/+1 counters on it': '{X}に+1/+1カウンターが2個以上置かれている。',
    'with Walk-in Closet unlocked': '{X}の《収納室》側が開放されている。',
    'not copying anything': '{X}が何もコピーしていない。',
    'exiled by Isochron Scepter': '{X}が《等時の王笏》によって追放されている。',
    'exiled by Panoptic Mirror': '{X}が《一望の鏡》によって追放されている。',
    'is prepared': '{X}が準備済状態である。',
    'without summoning sickness and with a +1/+1 counter on it': '{X}が召喚酔いしておらず、+1/+1カウンターが置かれている。',
}


def conv_mana(m):
    if not m:
        return ''
    def rep(mm):
        inner = mm.group(1)
        parts = inner.split('/')
        out = []
        for p in parts:
            out.append(p if p.isdigit() else SYM.get(p, p))
        return '(' + '/'.join(out) + ')'
    s = re.sub(r'\{([^}]+)\}', rep, m)
    s = s.replace(' plus commander tax if applicable', '(必要なら統率者税を追加)')
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--raw', required=True)
    ap.add_argument('--tr', nargs='*', default=[])
    ap.add_argument('--feat', required=True)
    ap.add_argument('--date', required=True)
    a = ap.parse_args()

    raw = json.load(open(a.raw))
    feat = json.load(open(a.feat))
    tr = {}
    for p in a.tr:
        tr.update(json.load(open(p)))
    old = {c['id']: c for c in json.load(open(DATA + '/combos.json'))['combos']}
    cards = json.load(open(DATA + '/cards.json'))['cards']
    ov = json.load(open(DATA + '/overrides.json'))
    byname, byfront = {}, {}
    for x in cards:
        byname.setdefault(x['name'], x)
        byfront.setdefault(x['name'].split(' // ')[0], x)

    def rec(n):
        return byname.get(n) or byfront.get(n.split(' // ')[0])

    def ja(x):
        o = ov.get(f"{x['set']}:{x['cn']}", {})
        if o.get('name'):
            return o['name']
        if x.get('printed_name'):
            return x['printed_name']
        if x.get('faces'):
            return ' // '.join(f.get('printed_name') or f['name'] for f in x['faces'])
        return x['name']

    def img(x):
        o = ov.get(f"{x['set']}:{x['cn']}", {})
        return o.get('img') or x.get('img') or (x.get('faces') and x['faces'][0].get('img')) or ''

    untranslated = []
    combos = []
    for c in raw:
        cs = []
        extra_pre = []
        for u in c['uses']:
            x = rec(u['name'])
            jn = ja(x) if x else u['name']
            zones = [ZONE.get(z, z) for z in (u.get('zones') or ['B'])]
            if u.get('cmd'):
                init = f'《{jn}》が統率者である'
            else:
                init = f'《{jn}》が' + 'または'.join(zones) + 'にある'
            cs.append({'en': u['name'], 'ja': jn, 'img': img(x) if x else '', 'init': init})
            for k in ('bf', 'gy', 'lib', 'ex'):
                st = u.get(k)
                if st:
                    if st in STATE:
                        extra_pre.append(STATE[st].replace('{X}', f'《{jn}》'))
                    elif st.startswith('attached to '):
                        t = rec(st[len('attached to '):])
                        tn = ja(t) if t else st[len('attached to '):]
                        extra_pre.append(f'《{jn}》が《{tn}》についている。')
                    elif st.startswith('is paired with '):
                        t = rec(st[len('is paired with '):])
                        tn = ja(t) if t else st[len('is paired with '):]
                        extra_pre.append(f'《{jn}》が《{tn}》と組んでいる。')
                    else:
                        extra_pre.append(f'《{jn}》: {st}')
                        untranslated.append(st)
        for r in c.get('requires') or []:
            extra_pre.append(REQ.get(r['name']) or (r['name'] + '（未翻訳）'))
            if r['name'] not in REQ:
                untranslated.append(r['name'])
        results = []
        for p in c['produces']:
            results.append(feat.get(p['name']) or p['name'])
            if p['name'] not in feat:
                untranslated.append(p['name'])
        o = old.get(c['id'])
        if o:
            pre, steps, mana = o['pre'], o['steps'], o['mana']
        else:
            pre = []
            for f in ('notable', 'easy'):
                for l in (c.get(f) or '').split('\n'):
                    l = l.strip()
                    if not l:
                        continue
                    if l in tr:
                        pre.append({'t': tr[l]})
                    else:
                        pre.append({'t': l, 'en': True}); untranslated.append(l)
            for l in extra_pre:
                pre.append({'t': l})
            steps = []
            for l in (c.get('desc') or '').split('\n'):
                l = l.strip()
                if not l:
                    continue
                if l in tr:
                    steps.append({'t': tr[l]})
                else:
                    steps.append({'t': l, 'en': True}); untranslated.append(l)
            mana = conv_mana(c.get('mana'))
        combos.append({'id': c['id'], 'cards': cs, 'identity': c.get('identity') or '', 'mv': c.get('mv') or 0,
                       'mana': mana, 'results': results, 'pre': pre, 'steps': steps, 'pop': c.get('pop') or 0})
    out = {'updated': a.date, 'source': 'Commander Spellbook (via Cube Cobra)',
           'note': 'Commander Spellbook のコンボデータを日本語化したもの。カード名は日本語版名称、前提・手順も日本語訳。',
           'combos': combos}
    json.dump(out, open(DATA + '/combos.json', 'w'), ensure_ascii=False, indent=1)
    print('combos', len(combos), 'kept', sum(1 for c in raw if c['id'] in old), 'new', sum(1 for c in raw if c['id'] not in old))
    print('untranslated', len(untranslated), untranslated[:20])


if __name__ == '__main__':
    main()
