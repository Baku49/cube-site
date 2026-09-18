#!/usr/bin/env python3
"""メタキューブ カードリスト更新スクリプト

入力:
  --csv      Cube Cobra 書き出しCSV (mainboard)
  --scry     ブラウザで取得した Scryfall データ {"set:cn": {en, ja, jaOther}}  (slim 形式)
  --wg       ブラウザで取得した Wisdom Guild データ {name: {found, rows{...}}}
  --elo      ブラウザで取得した Cube Cobra Elo {cardID: {name,set,cn,elo}}
  --date     更新日 (YYYY-MM-DD)
出力: docs/metacube/data/{cards,changelog,overrides,elo}.json を更新、
      src/metacube/{cards_index.json,cubecobra_latest.csv,missing_ja.json,elo_missing.json} を更新
"""
import argparse, csv, json, re, collections, shutil, datetime

ROOT = '/home/claude/metacube-site'
DATA = ROOT + '/docs/metacube/data'
SRC = ROOT + '/src/metacube'

COLOR_NAME = {'W': 'White', 'U': 'Blue', 'B': 'Black', 'R': 'Red', 'G': 'Green'}
FACE_FIELDS = ['name', 'printed_name', 'mana_cost', 'type_line', 'printed_type_line', 'oracle_text',
               'printed_text', 'flavor_text', 'power', 'toughness', 'loyalty', 'defense']
TOP_FIELDS = ['name', 'printed_name', 'mana_cost', 'cmc', 'type_line', 'printed_type_line', 'oracle_text',
              'printed_text', 'flavor_text', 'power', 'toughness', 'loyalty', 'defense', 'rarity', 'set_name',
              'artist', 'layout', 'scryfall_uri']


def cat_of(ci):
    if not ci:
        return 'Colorless'
    if len(ci) == 1:
        return COLOR_NAME[ci[0]]
    return 'Multicolored'


def build_record(en, ja, ja_other, count):
    """既存 cards.json と同じスキーマのレコードを作る"""
    p = ja or en
    rec = {'set': en['set'], 'cn': en['collector_number'], 'count': count, 'cat': cat_of(en['color_identity']),
           'lang': 'ja' if ja else 'en'}
    for f in TOP_FIELDS:
        rec[f] = p.get(f)
    rec['img'] = p.get('img')
    faces = None
    if p.get('card_faces'):
        faces = []
        other_faces = (ja_other or {}).get('card_faces') if (not ja and ja_other) else None
        for i, f in enumerate(p['card_faces']):
            fo = {k: f.get(k) for k in FACE_FIELDS}
            if other_faces and i < len(other_faces):
                for k in ('printed_name', 'printed_type_line', 'printed_text'):
                    if not fo.get(k):
                        fo[k] = other_faces[i].get(k)
            fo['img'] = f.get('img')
            faces.append(fo)
        if not rec['img'] and faces[0].get('img'):
            rec['img'] = faces[0]['img']
    else:
        if not ja and ja_other and not ja_other.get('card_faces'):
            for k in ('printed_name', 'printed_type_line', 'printed_text'):
                if not rec.get(k):
                    rec[k] = ja_other.get(k)
    rec['faces'] = faces
    rec['ci'] = ''.join(en['color_identity'] or [])
    return rec


# ---- Wisdom Guild ----
SYM = {'白': 'W', '青': 'U', '黒': 'B', '赤': 'R', '緑': 'G', 'Ｔ': 'T', 'Ｑ': 'Q', '◇': 'C', 'Ｘ': 'X', '氷': 'S',
       'Φ': 'P', 'Ｅ': 'E'}
ZEN = str.maketrans('０１２３４５６７８９', '0123456789')


def conv_symbols(text):
    def rep(m):
        inner = m.group(1)
        parts = inner.split('/')
        out = []
        for part in parts:
            part = part.translate(ZEN)
            if part.isdigit():
                out.append(part)
            elif all(ch in SYM for ch in part) and part:
                out.append(''.join(SYM[ch] for ch in part))
            else:
                return m.group(0)
        return '{' + '/'.join(out) + '}'
    return re.sub(r'[（(]([^（）()]{1,4})[）)]', rep, text)


def strip_en_types(t):
    return re.sub(r'\([A-Za-z\' \-]+\)', '', t)


def apply_wg(rec, wg):
    rows = wg['rows']
    name_row = rows.get('カード名', '')
    ja_name = None
    if '/' in name_row:
        ja_name = name_row.split('/')[0].strip()
    text = rows.get('テキスト', '').strip()
    typ = rows.get('タイプ', '').strip()
    flav = rows.get('フレーバ', '').strip()
    pt = rows.get('Ｐ／Ｔ', '').strip()
    ov = {}
    if ja_name and ja_name != rec['name']:
        rec['printed_name'] = ja_name
        if rec['lang'] != 'ja':
            ov['name'] = ja_name
    if typ:
        rec['printed_type_line'] = strip_en_types(typ)
        ov['type'] = typ
    if text:
        rec['printed_text'] = text
        ov['text'] = conv_symbols(text)
    if flav and rec['lang'] != 'ja':
        ov['flavor'] = flav
    if pt and text:
        ov['pt'] = pt
    if text or typ:
        rec['wg'] = True
    ov['src'] = 'wisdom-guild'
    return ov if (text or typ) else None


def ja_name_of(rec):
    if rec.get('printed_name'):
        return rec['printed_name']
    if rec.get('faces'):
        return ' // '.join(f.get('printed_name') or f['name'] for f in rec['faces'])
    return rec['name']


def front(name):
    return name.split(' // ')[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--csv', required=True)
    ap.add_argument('--scry', required=True)
    ap.add_argument('--wg')
    ap.add_argument('--elo')
    ap.add_argument('--date', required=True)
    ap.add_argument('--note', default='')
    a = ap.parse_args()

    rows = list(csv.DictReader(open(a.csv, encoding='utf-8')))
    rows = [r for r in rows if r['board'] == 'mainboard' and r['maybeboard'] == 'false']
    counts = collections.Counter((r['Set'], r['Collector Number']) for r in rows)
    order = []
    for r in rows:
        k = (r['Set'], r['Collector Number'])
        if k not in order:
            order.append(k)

    old = json.load(open(DATA + '/cards.json'))
    old_map = {(x['set'], x['cn']): x for x in old['cards']}
    scry = json.load(open(a.scry))
    wg = json.load(open(a.wg)) if a.wg else {}
    overrides = json.load(open(DATA + '/overrides.json'))

    new_cards = []
    added_recs, missing_ja = [], []
    for k in order:
        if k in old_map:
            rec = dict(old_map[k]); rec['count'] = counts[k]
        else:
            d = scry[f'{k[0]}:{k[1]}']
            en, ja, jo = d['en'], d['ja'], d['jaOther']
            if not ja and jo and jo['set'] == en['set']:
                ja = jo
            rec = build_record(en, ja, jo, counts[k])
            key = f'{k[0]}:{k[1]}'
            has_ja = rec.get('printed_text') or (rec.get('faces') and any(f.get('printed_text') for f in rec['faces']))
            if not has_ja:
                w = wg.get(front(rec['name']))
                ov = apply_wg(rec, w) if (w and w.get('found')) else None
                if ov:
                    overrides[key] = ov
                else:
                    # 同名カードの旧printingに override があれば引き継ぐ
                    for ok, ox in old_map.items():
                        okey = f'{ok[0]}:{ok[1]}'
                        if ox['name'] == rec['name'] and okey in overrides and ok not in counts:
                            overrides[key] = overrides[okey]
                            if ox.get('wg'):
                                rec['wg'] = True
                                if ox.get('wgSrc'):
                                    rec['wgSrc'] = ox['wgSrc']
                                for f in ('printed_name', 'printed_type_line', 'printed_text'):
                                    if not rec.get(f):
                                        rec[f] = ox.get(f)
                            break
            if rec['lang'] != 'ja':
                missing_ja.append({'set': k[0], 'cn': k[1], 'name': rec['name']})
            added_recs.append(rec)
        new_cards.append(rec)

    # 変更履歴 (カード名ベース)
    old_names = collections.Counter()
    for x in old['cards']:
        old_names[x['name']] += x['count']
    new_names = collections.Counter()
    for x in new_cards:
        new_names[x['name']] += x['count']
    added_names, removed_names = [], []
    for x in new_cards:
        if new_names[x['name']] > old_names.get(x['name'], 0):
            n = new_names[x['name']] - old_names.get(x['name'], 0)
            if x['name'] not in [y for y, _ in added_names]:
                added_names.append((x['name'], (ja_name_of(x), n)))
    for x in old['cards']:
        if old_names[x['name']] > new_names.get(x['name'], 0):
            n = old_names[x['name']] - new_names.get(x['name'], 0)
            if x['name'] not in [y for y, _ in removed_names]:
                removed_names.append((x['name'], (ja_name_of(x), n)))

    def fmt(lst):
        return [nm if n == 1 else f'{nm}×{n}' for _, (nm, n) in lst]

    changelog = json.load(open(DATA + '/changelog.json'))
    entry = {'date': a.date, 'note': a.note or f'リスト更新(Cube Cobra書き出し {a.date})。',
             'added': fmt(added_names), 'removed': fmt(removed_names)}
    changelog.insert(0, entry)

    # Elo
    elo_missing = []
    if a.elo:
        elo_raw = json.load(open(a.elo))
        by_sc = {(v['set'], v['cn']): v for v in elo_raw.values()}
        elo = json.load(open(DATA + '/elo.json'))
        by_name, by_id = {}, {}
        for x in new_cards:
            v = by_sc.get((x['set'], x['cn']))
            if v and v.get('elo') is not None:
                by_name[x['name']] = round(v['elo'], 1)
                cid = [i for i, vv in elo_raw.items() if vv is v][0]
                by_id[cid] = round(v['elo'], 1)
            else:
                elo_missing.append(x['name'])
        elo['byName'], elo['byId'] = by_name, by_id
        d = datetime.date.fromisoformat(a.date)
        elo['updated'] = f'{d.year}年{d.month:02d}月{d.day:02d}日'
        json.dump(elo, open(DATA + '/elo.json', 'w'), ensure_ascii=False, indent=1)
        json.dump(elo_missing, open(SRC + '/elo_missing.json', 'w'), ensure_ascii=False, indent=1)

    out = {'generated': a.date, 'source': f'Cube Cobra CSV {a.date} + Scryfall', 'cards': new_cards}
    json.dump(out, open(DATA + '/cards.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(changelog, open(DATA + '/changelog.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(overrides, open(DATA + '/overrides.json', 'w'), ensure_ascii=False, indent=1)
    idx = [{'set': x['set'], 'cn': x['cn'], 'name': x['name'], 'count': x['count'], 'cat': x['cat']} for x in new_cards]
    json.dump(idx, open(SRC + '/cards_index.json', 'w'), ensure_ascii=False, indent=1)
    shutil.copy(a.csv, SRC + '/cubecobra_latest.csv')
    mj = json.load(open(SRC + '/missing_ja.json'))
    keep = [e for e in mj['no_japanese_printing'] if (e['set'], e['cn']) in counts]
    mj['no_japanese_printing'] = keep + missing_ja
    json.dump(mj, open(SRC + '/missing_ja.json', 'w'), ensure_ascii=False, indent=1)

    print('cards', len(new_cards), sum(x['count'] for x in new_cards))
    print('new records', len(added_recs), 'no-ja', len(missing_ja), 'elo missing', len(elo_missing))
    print('changelog +', len(entry['added']), '-', len(entry['removed']))
    print('added:', entry['added'])
    print('removed:', entry['removed'])


if __name__ == '__main__':
    main()
