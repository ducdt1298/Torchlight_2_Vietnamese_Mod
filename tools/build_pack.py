# -*- coding: utf-8 -*-
"""Build the Vietnamese language pack files under build/MEDIA/TRANSLATIONS/.

  VIETNAMESE.DAT                          language descriptor (shown as "Tiếng Việt" in Options > Language)
  VIETNAMESE/TRANSLATION.DAT              English -> Vietnamese table
  VIETNAMESE/UI/...                       exact clone of the official German pack's UI folder, except that
                                          every .FONT uses the game's Arial (full Vietnamese coverage) and
                                          the scheme points to VIETNAMESE instead of GERMAN
The first build used custom fonts (build_fonts.py) and a hand-made UI folder; the game crashed at
start (CEGUI: font 'Serif' does not exist), so the pack now mirrors an official pack 1:1.

Only strings that pass validation are included; anything else simply stays English in game.
Also writes translation/REVIEW_vi.tsv (all translations with context) for human review.
"""
import json
import os
import re
import shutil
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from tl2lib import (T_INT, T_STRING, man_files, parse_dat, parse_man, read_entry, tl2hash, write_dat)
from vi_io import batch_names, load_batch, load_translations, tokens

PACK = os.path.join(config.BUILD, 'MEDIA', 'TRANSLATIONS')
UI = os.path.join(PACK, 'VIETNAMESE', 'UI')
FOLDERPAIR_TARGET_KEY = tl2hash('TRANSLATED')     # FOLDERPAIR = ORIGINAL -> TRANSLATED
TEMPLATE_LANG = 'GERMAN'                           # official pack whose UI folder is cloned
FONT_TTF = 'media/ui/arial.ttf'                    # one stable font for everything (as German does for Serif)


def merge_translations():
    final, rejected, kept = {}, [], 0
    review = []
    C = json.load(open(os.path.join(config.WORK, 'classified.json'), encoding='utf-8'))
    for name in batch_names():
        b = load_batch(name)
        tr, _ = load_translations(name)
        for it in b['items']:
            en, vi = it['en'], tr.get(it['id'])
            if en not in C:
                continue                      # string no longer used by the current game version
            if vi is None or not vi.strip():
                rejected.append((it['id'], 'missing'))
                continue
            vi = unicodedata.normalize('NFC', vi.strip())
            lead = en[:len(en) - len(en.lstrip())]
            trail = en[len(en.rstrip()):]
            vi = lead + vi + trail
            review.append((it['id'], C.get(en, {}).get('group', '(no longer in game)'), it['ctx'], en, vi))
            if vi == en:
                kept += 1
                continue
            if tokens(vi) != tokens(en):
                rejected.append((it['id'], 'token mismatch'))
                continue
            if any(ord(c) < 32 for c in vi):
                rejected.append((it['id'], 'control char'))
                continue
            final[en] = vi
    return final, rejected, kept, review


def base_files():
    man = parse_man(open(config.MAN, 'rb').read())
    files = dict(man_files(man))
    pak = open(config.PAK, 'rb')
    return (lambda p: read_entry(pak, files[p]['offset'])), files


def main():
    shutil.rmtree(UI, ignore_errors=True)
    os.makedirs(UI, exist_ok=True)
    final, rejected, kept, review = merge_translations()
    json.dump(final, open(os.path.join(config.WORK, 'vi_final.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    with open(os.path.join(config.TRANSLATION, 'REVIEW_vi.tsv'), 'w', encoding='utf-8-sig', newline='\n') as fh:
        fh.write('id\tgroup\tcontext\tenglish\tvietnamese\n')
        for row in review:
            fh.write('\t'.join(str(x).replace('\t', ' ') for x in row) + '\n')

    # --- TRANSLATION.DAT
    O, T = tl2hash('ORIGINAL'), tl2hash('TRANSLATION')
    kids = [{'name': tl2hash('TRANSLATION'), 'props': [(O, T_STRING, en), (T, T_STRING, vi)], 'kids': []}
            for en, vi in final.items()]
    table = write_dat({'name': tl2hash('TRANSLATIONS'), 'props': [], 'kids': kids})
    open(os.path.join(PACK, 'VIETNAMESE', 'TRANSLATION.DAT'), 'wb').write(table)

    # --- VIETNAMESE.DAT (same layout as the official descriptors; no AUDIO_TRACK -> English voice-over)
    desc = {'name': tl2hash('LANGUAGE'), 'props': [
        (tl2hash('DISPLAYNAME'), T_STRING, config.LANG_DISPLAY),
        (tl2hash('NAME'), T_STRING, config.LANG_NAME),
        (tl2hash('TRANSLATIONFILE'), T_STRING, config.PACK_DIR + 'TRANSLATION.dat'),
        (tl2hash('ID'), T_INT, config.LANG_ID)],
        'kids': [{'name': tl2hash('FOLDERPAIR'), 'props': [
            (tl2hash('ORIGINAL'), T_STRING, 'MEDIA/UI/'),
            (FOLDERPAIR_TARGET_KEY, T_STRING, config.PACK_DIR + 'UI/')], 'kids': []}]}
    open(os.path.join(PACK, 'VIETNAMESE.DAT'), 'wb').write(write_dat(desc))

    # --- UI folder: clone of the template language's UI folder
    get, files = base_files()
    prefix = 'MEDIA/TRANSLATIONS/%s/UI/' % TEMPLATE_LANG
    cloned = 0
    for p in sorted(files):
        if not p.startswith(prefix):
            continue
        rel = p[len(prefix):]
        data = get(p)
        if rel.endswith('.FONT'):
            data, n = re.subn(rb'Filename="[^"]*"', b'Filename="' + FONT_TTF.encode() + b'"', data, count=1)
            assert n == 1, rel
        elif rel.endswith('.SCHEME'):
            data, n = re.subn(rb'(?i)media/translations/' + TEMPLATE_LANG.encode() + b'/', b'media/translations/VIETNAMESE/', data)
            assert n > 0, rel
        dst = os.path.join(UI, *rel.split('/'))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)
        cloned += 1
    print('UI folder: %d files cloned from %s (all fonts -> %s)' % (cloned, TEMPLATE_LANG, FONT_TTF))

    # sanity: the table parses back
    _, root = parse_dat(table)
    assert len(root['kids']) == len(final)
    print('translations in table: %d   kept English: %d   rejected: %d' % (len(final), kept, len(rejected)))
    for i, why in rejected[:20]:
        print('   rejected id %s: %s' % (i, why))
    print('TRANSLATION.DAT %d bytes' % len(table))


if __name__ == '__main__':
    main()
