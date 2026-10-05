# -*- coding: utf-8 -*-
"""Validate translation outputs. Usage: python validate_translations.py [batch ...] [--all-errors]

Errors (must fix): missing id, empty text, token mismatch ([...] <...> |cXXXXXXXX |u \\n),
                   foreign script (CJK/Cyrillic/...), stray real control characters.
Warnings (review): translate-mode text left identical to English, glossary violations,
                   suspicious length. Leading/trailing spaces are restored automatically at build time.
"""
import os
import re
import sys
import unicodedata
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vi_io import batch_names, load_batch, load_translations, tokens

FOREIGN = re.compile(r'[Ѐ-ӿͰ-Ͽ぀-ヿ㐀-鿿가-힯฀-๿]')
GLOSSARY = [
    (re.compile(r'sát thương (lửa|băng|điện|độc|vật lý|nguyên tố)', re.I), 'damage types stay English: Fire/Ice/Electric/Poison/Physical/Elemental'),
    (re.compile(r'kháng (lửa|băng|điện|độc|vật lý)', re.I), 'damage types stay English'),
    (re.compile(r'\b(Sức mạnh|Khéo léo|Nhanh nhẹn|Thể lực|Sinh lực)\b'), 'attributes stay English: Strength/Dexterity/Focus/Vitality'),
    (re.compile(r'\b(Cuồng chiến binh|Pháp sư Ember|Kỹ sư|Kẻ lang thang|Người phương xa)\b', re.I), 'class names stay English'),
]
VIET = re.compile(r'[àáảãạăằắẳẵặâầấẩẫậđèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ]', re.I)


def check(name, show_all=False):
    b = load_batch(name)
    tr, files = load_translations(name)
    errors, warns = [], []
    ids = {it['id'] for it in b['items']}
    for it in b['items']:
        i, en, mode = it['id'], it['en'], it['mode']
        vi = tr.get(i)
        if vi is None:
            errors.append((i, 'missing'))
            continue
        if not vi.strip():
            errors.append((i, 'empty'))
            continue
        if unicodedata.normalize('NFC', vi) != vi:
            warns.append((i, 'not NFC (will be normalized)'))
        te, tv = tokens(en), tokens(vi)
        if te != tv:
            ce, cv = Counter(te), Counter(tv)
            errors.append((i, 'tokens: missing %s extra %s' % (dict(ce - cv), dict(cv - ce))))
        if FOREIGN.search(vi):
            errors.append((i, 'foreign script: %r' % FOREIGN.findall(vi)[:5]))
        if any(ord(c) < 32 for c in vi):
            errors.append((i, 'control character'))
        if mode == 'translate' and vi.strip() == en.strip() and re.search(r'[a-z]{3}', en):
            warns.append((i, 'identical to English (translate mode)'))
        for rx, msg in GLOSSARY:
            if rx.search(vi):
                warns.append((i, 'glossary: ' + msg))
        if vi.strip() != en.strip() and not VIET.search(vi) and re.search(r'[a-z]{4}', vi):
            warns.append((i, 'changed but no Vietnamese letters'))
        if len(en) >= 6 and len(vi) > 2.6 * len(en) + 10:
            warns.append((i, 'much longer than English (%d vs %d chars)' % (len(vi), len(en))))
    extra = sorted(set(tr) - ids)
    if extra:
        warns.append((extra[0], '%d ids not in this batch (ignored)' % len(extra)))
    done = sum(1 for it in b['items'] if tr.get(it['id']))
    print('%-34s files=%d  done %d/%d  errors=%d  warnings=%d' % (name, len(files), done, b['count'], len(errors), len(warns)))
    lim = None if show_all else 25
    en_of = {it['id']: it['en'] for it in b['items']}
    for i, msg in errors[:lim]:
        print('   ERROR  %s: %s\n          EN: %s\n          VI: %s' % (i, msg, en_of.get(i, '')[:200], (tr.get(i) or '')[:200]))
    for i, msg in warns[:lim]:
        print('   warn   %s: %s | EN: %s' % (i, msg, en_of.get(i, '')[:100]))
    return len(errors)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    names = batch_names()
    sel = [n for n in names if not args or any(n.startswith(a) or a in n for a in args)]
    total = sum(check(n, '--all-errors' in sys.argv) for n in sel)
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
