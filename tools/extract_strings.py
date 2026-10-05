# -*- coding: utf-8 -*-
"""Extract every translatable English string from the game (read-only) with context.

Sources:
  * TRANSLATE-typed properties of every binary .DAT (except MEDIA/TRANSLATIONS/)
  * ORIGINAL column of the six official TRANSLATION.DAT tables (covers UI layouts
    and strings built into the exe)
Output: work/strings.json  {english: {"ctx": [[file, block path, key], ...], "official": bool}}
        work/keynames.json {hash: name}  (DAT key names recovered from the exe)
"""
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from tl2lib import (FT_DAT, T_TRANSLATE, man_files, parse_dat, parse_man, read_entry, tl2hash)


def load_keynames():
    path = os.path.join(config.WORK, 'keynames.json')
    if os.path.exists(path):
        return {int(k): v for k, v in json.load(open(path, encoding='utf-8')).items()}
    exe = open(config.EXE, 'rb').read()
    cand = set(m.group().decode('ascii') for m in re.finditer(rb'[A-Za-z0-9_ ]{2,48}', exe))
    cand |= set(m.group().decode('utf-16-le') for m in re.finditer(rb'(?:[A-Za-z0-9_ ]\x00){2,48}', exe))
    names = {}
    for s in cand:
        for v in (s.upper(), s.upper().strip()):
            names.setdefault(tl2hash(v), v)
    json.dump({str(k): v for k, v in names.items()}, open(path, 'w', encoding='utf-8'))
    return names


def main():
    keyname = load_keynames()
    man = parse_man(open(config.MAN, 'rb').read())
    files = dict(man_files(man))
    pak = open(config.PAK, 'rb')

    ctx = defaultdict(list)
    for path, rec in sorted(files.items()):
        if rec['type'] != FT_DAT or not path.endswith('.DAT') or path.startswith('MEDIA/TRANSLATIONS/'):
            continue
        try:
            _, root = parse_dat(read_entry(pak, rec['offset']))
        except Exception as ex:  # noqa: BLE001 - one malformed file must not stop the scan
            print('skip', path, ex)
            continue

        def walk(b, trail):
            here = trail + [keyname.get(b['name'], '#%08x' % b['name'])]
            for key, typ, val in b['props']:
                if typ == T_TRANSLATE and val and val.strip():
                    ctx[val].append([path, '/'.join(here), keyname.get(key, '#%08x' % key)])
            for k in b['kids']:
                walk(k, here)
        walk(root, [])

    official = set()
    O, T = tl2hash('ORIGINAL'), tl2hash('TRANSLATION')
    for d in man['dirs']:
        if d['path'].startswith('MEDIA/TRANSLATIONS/') and d['path'].count('/') == 3:
            for rec in d['records']:
                if rec['name'] == 'TRANSLATION.DAT':
                    _, root = parse_dat(read_entry(pak, rec['offset']))
                    for k in root['kids']:
                        p = {a: v for a, _, v in k['props']}
                        if p.get(O):
                            official.add(p[O])

    out = {}
    for s in set(ctx) | official:
        out[s] = {'ctx': ctx.get(s, []), 'official': s in official}
    json.dump(out, open(os.path.join(config.WORK, 'strings.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print('strings: %d (from DAT %d, official tables %d, DAT-only %d, table-only %d)' % (
        len(out), len(ctx), len(official), len(set(ctx) - official), len(official - set(ctx))))


if __name__ == '__main__':
    main()
