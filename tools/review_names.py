# -*- coding: utf-8 -*-
"""Check the "names stay English" rule inside translated sentences.

For every translated string, each multi-word proper name from names_keep_english.txt
(skills, items, monsters, places, quests...) that appears in the English text must still
appear in the Vietnamese text. Prints the violations (review them by hand; plural/possessive
forms like "Guardians" -> "các Guardian" are legitimate).
Usage: python review_names.py [batch ...]
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from vi_io import batch_names, load_batch, load_translations

TOKEN = re.compile(r'\[[^\]]*\]|<[^>]*>|\|c[0-9A-Fa-f]{8}|\|u|\\n')


def load_names():
    names = set()
    for line in open(os.path.join(config.TRANSLATION, 'names_keep_english.txt'), encoding='utf-8'):
        n = TOKEN.sub('', line).strip()
        words = n.split()
        if len(words) >= 2 and len(n) >= 8 and sum(w[:1].isupper() for w in words) >= 2:
            names.add(n)
    return sorted(names, key=len, reverse=True)


def main():
    names = load_names()
    first = {}
    for n in names:
        first.setdefault(n.split()[0], []).append(n)
    args = sys.argv[1:]
    total, bad = 0, Counter()
    for b in batch_names():
        if args and not any(a in b for a in args):
            continue
        batch = load_batch(b)
        tr, _ = load_translations(b)
        for it in batch['items']:
            vi = tr.get(it['id'])
            if not vi or vi.strip() == it['en'].strip():
                continue
            en = TOKEN.sub(' ', it['en'])
            words = set(re.findall(r"[A-Za-z][\w'-]*", en))
            found = [n for w in words for n in first.get(w, []) if re.search(r'(?<![\w])' + re.escape(n) + r'(?![\w])', en)]
            for n in found:
                core = n[4:] if n.startswith('The ') else n        # Vietnamese drops the article
                if core.lower() not in vi.lower() and core.rstrip('s').lower() not in vi.lower():
                    total += 1
                    bad[b] += 1
                    print('%s id %d: name "%s" missing\n    EN: %s\n    VI: %s' % (b, it['id'], n, it['en'][:160], vi[:160]))
    print('\nviolations: %d  %s' % (total, dict(bad)))


if __name__ == '__main__':
    main()
