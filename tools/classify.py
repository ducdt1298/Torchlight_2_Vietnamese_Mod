# -*- coding: utf-8 -*-
"""Split the extracted strings into KEEP (stay English) and TRANSLATE groups.

Policy (from the project brief): names of skills, items, monsters and other proper
names stay English so players can talk about them with the international
community; dialogue and explanatory text is translated to Vietnamese.

Output: work/classified.json {english: {"class": "keep"|"translate"|"decide", "group": str, "hint": str}}
  keep      - a name context was found; never sent to translation
  translate - explanatory/dialogue context; translate (English names inside stay English)
  decide    - no reliable context (UI/exe strings, misc); translator keeps it English if it is a name
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

# (top folder, key) pairs that hold names -> keep English
NAME_KEYS = {
    ('UNITS', 'DISPLAYNAME'), ('UNITS', 'UNIDENTIFIED_NAME'), ('UNITS', 'DORMANTNAME'),
    ('SKILLS', 'DISPLAYNAME'),
    ('AFFIXES', 'PREFIX'), ('AFFIXES', 'SUFFIX'),
    ('DUNGEONS', 'DISPLAYNAME'), ('DUNGEONS', 'NAME_OVERRIDE'),
    ('QUESTS', 'DISPLAYNAME'), ('QUESTS', 'UNIQUE_MONSTER_NAME'),
    ('SETS', 'DISPLAYNAME'),
    ('WAYPOINTS', 'DISPLAYNAME'),
    ('MOVIES', 'DISPLAYNAME'),
    ('EMOTES', 'COMMAND'),            # chat commands typed by players
}
NAME_BLOCKS = {('GLOBALS.DAT', 'PETNAMES'), ('GLOBALS.DAT', 'TITLES')}


def top_of(path):
    return path.split('/')[1] if path.count('/') >= 1 else path


def group_of(path, bp, key):
    top = top_of(path)
    if top == 'QUESTS':
        m = re.match(r'MEDIA/QUESTS/([^/]+)/', path)
        return 'quest:' + (m.group(1) if m else 'misc')
    if top == 'SKILLS':
        return 'skill:' + path.split('/')[2] if path.count('/') >= 3 else 'skill:misc'
    if top == 'UNITS':
        parts = path.split('/')
        return 'unit:' + (parts[2] if len(parts) > 3 else 'misc')
    if top == 'EFFECTSLIST.DAT':
        return 'effects'
    return 'ui:' + top


def main():
    S = json.load(open(os.path.join(config.WORK, 'strings.json'), encoding='utf-8'))
    out = {}
    for s, v in S.items():
        ctx = v['ctx']
        is_name = any((top_of(f), k) in NAME_KEYS or (top_of(f), bp.split('/')[-1]) in NAME_BLOCKS
                      for f, bp, k in ctx)
        if not s.strip() or not re.search(r'[A-Za-z]', s):
            cls = 'keep'                       # nothing to translate (numbers, symbols)
        elif is_name:
            cls = 'keep'
        elif not ctx:
            cls = 'decide'                     # UI layouts / exe strings: no context
        elif all(top_of(f) == 'GLOBALS.DAT' or k == 'DISPLAYNAMECOMPLETE' for f, bp, k in ctx):
            cls = 'decide'                     # mixes item-type names and UI messages
        else:
            cls = 'translate'
        if ctx:
            f, bp, k = ctx[0]
            group = group_of(f, bp, k)
            hint = '%s | %s | %s' % (f.replace('MEDIA/', ''), bp.split('/')[-1], k)
        else:
            group, hint = 'ui:table', 'UI/exe string (no data context)'
        out[s] = {'class': cls, 'group': group, 'hint': hint}
    json.dump(out, open(os.path.join(config.WORK, 'classified.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)

    words = Counter()
    count = Counter()
    for s, v in out.items():
        count[v['class']] += 1
        words[v['class']] += len(re.findall(r"[A-Za-z']+", s))
    for c in ('keep', 'translate', 'decide'):
        print('%-9s %6d strings %7d words' % (c, count[c], words[c]))
    g = Counter()
    for s, v in out.items():
        if v['class'] != 'keep':
            g[v['group'][:24]] += len(re.findall(r"[A-Za-z']+", s))
    print('words by group (to translate/decide):')
    for k, n in g.most_common(40):
        print('   %7d %s' % (n, k))


if __name__ == '__main__':
    main()
