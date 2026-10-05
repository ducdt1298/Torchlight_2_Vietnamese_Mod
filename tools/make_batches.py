# -*- coding: utf-8 -*-
"""Create translation batches (translation/batches/*.json) from work/classified.json.

Each item: {"id": int, "mode": "translate"|"decide", "ctx": str, "en": str}
Also writes translation/names_keep_english.txt (strings that stay English) and work/id_map.json.
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config


def words(s):
    return len(re.findall(r"[A-Za-z']+", s))


def batch_key(s, v):
    g, hint = v['group'], v['hint']
    kind, _, sub = g.partition(':')
    if g == 'unit:ITEMS':
        return 'items'
    if g == 'quest:TL2MAINQUEST':
        return 'mainquest'
    if g == 'quest:A1-SIDEQUESTS':
        return 'sidequest_a1'
    if g in ('quest:A2-SIDEQUESTS', 'quest:A3-SIDEQUESTS'):
        return 'sidequest_a2a3'
    if kind == 'quest':
        return 'passives_misc_quests'
    if g in ('skill:RAILMAN', 'skill:BERSERKER'):
        return 'skills_engineer_berserker'
    if kind == 'skill':
        return 'skills_other'
    if g == 'effects' or kind == 'unit':
        return 'effects_monsters'
    if g == 'ui:table':
        return 'ui_table'
    return 'ui_globals'


SPLIT = {'items': 3, 'ui_table': 2, 'mainquest': 2}      # large groups split into N word-balanced parts
ORDER = ['items', 'mainquest', 'sidequest_a1', 'sidequest_a2a3', 'passives_misc_quests',
         'skills_engineer_berserker', 'skills_other', 'effects_monsters', 'ui_globals', 'ui_table']


def main():
    C = json.load(open(os.path.join(config.WORK, 'classified.json'), encoding='utf-8'))
    groups = defaultdict(list)
    for s, v in C.items():
        if v['class'] in ('translate', 'decide'):
            groups[batch_key(s, v)].append(s)

    bdir = os.path.join(config.TRANSLATION, 'batches')
    os.makedirs(bdir, exist_ok=True)
    os.makedirs(os.path.join(config.TRANSLATION, 'vi'), exist_ok=True)
    id_map = {}
    next_id = 1
    n = 0
    for key in ORDER:
        items = sorted(groups[key], key=lambda s: (C[s]['hint'], s))
        parts = SPLIT.get(key, 1)
        total = sum(words(s) for s in items)
        chunks, cur, acc = [], [], 0
        for s in items:
            cur.append(s)
            acc += words(s)
            if len(chunks) < parts - 1 and acc >= total * (len(chunks) + 1) / parts:
                chunks.append(cur)
                cur = []
        chunks.append(cur)
        for i, chunk in enumerate(chunks):
            n += 1
            name = 'b%02d_%s%s' % (n, key, '_%d' % (i + 1) if parts > 1 else '')
            data = []
            for s in chunk:
                id_map[next_id] = s
                data.append({'id': next_id, 'mode': C[s]['class'], 'ctx': C[s]['hint'], 'en': s})
                next_id += 1
            json.dump({'batch': name, 'count': len(data), 'items': data},
                      open(os.path.join(bdir, name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
            print('%-38s %5d strings %6d words' % (name, len(data), sum(words(x) for x in chunk)))

    keep = sorted(s for s, v in C.items() if v['class'] == 'keep' and re.search(r'[A-Za-z]', s))
    with open(os.path.join(config.TRANSLATION, 'names_keep_english.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(k.replace('\n', ' ') for k in keep) + '\n')
    json.dump({str(k): v for k, v in id_map.items()}, open(os.path.join(config.WORK, 'id_map.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)
    print('total ids:', len(id_map), ' keep-English names:', len(keep))


if __name__ == '__main__':
    main()
