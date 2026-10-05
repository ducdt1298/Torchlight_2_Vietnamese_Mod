# -*- coding: utf-8 -*-
"""Offline verification of the patch in output/ (never runs or modifies the game).

Reads the patched manifest the way the game does and resolves every entry against a
virtual patched DATA.PAK = original DATA.PAK (read-only) + output/PAKS/DATA.PAK.vi-append.
Checks:
  * every original directory and record is present and unchanged
  * every new record lands on a valid entry: sizes, zlib stream, CRC32
  * the language descriptor, translation table, fonts, .FONT files and scheme are consistent
  * every character used by the translations exists in the fonts that display them
  * (if present) output/full/PAKS/DATA.PAK equals original + append
"""
import hashlib
import io
import json
import os
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

from fontTools.ttLib import TTFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from tl2lib import FT_FOLDER, T_INT, T_STRING, crc32, man_files, parse_dat, parse_man, tl2hash
from vi_io import tokens

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)
        print('   FAIL', msg)
    return cond


class VirtualPak:
    def __init__(self, original, append):
        self.f = open(original, 'rb')
        self.size = os.path.getsize(original)
        self.tail = open(append, 'rb').read()

    def read_raw(self, off, n):
        if off >= self.size:
            return self.tail[off - self.size: off - self.size + n]
        self.f.seek(off)
        return self.f.read(n)

    def entry(self, off, size):
        usize, csize = struct.unpack('<II', self.read_raw(off, 8))
        data = self.read_raw(off + 8, csize or usize)
        if csize:
            d = zlib.decompressobj()
            data = d.decompress(data)
            check(d.eof and not d.unused_data, 'zlib stream not clean at %d' % off)
        check(usize == size == len(data), 'size mismatch at %d' % off)
        return data


def main():
    info = json.load(open(os.path.join(config.OUTPUT, 'patch_info.json'), encoding='utf-8'))
    out = os.path.join(config.OUTPUT, 'PAKS')
    orig_man = parse_man(open(config.MAN, 'rb').read())
    new_bytes = open(os.path.join(out, 'DATA.PAK.MAN'), 'rb').read()
    new_man = parse_man(new_bytes)
    vpak = VirtualPak(config.PAK, os.path.join(out, 'DATA.PAK.vi-append'))

    print('[1] original game data untouched')
    check(os.path.getsize(config.PAK) == info['original']['pak_size'], 'game DATA.PAK size differs from build time')
    check(hashlib.sha256(open(config.MAN, 'rb').read()).hexdigest() == info['original']['man_sha256'],
          'game DATA.PAK.MAN differs from build time')
    check(hashlib.sha256(new_bytes).hexdigest() == info['patched']['man_sha256'], 'patched MAN hash')
    check(len(vpak.tail) == info['append']['size'], 'append size')
    new_dirs = {d['path']: d for d in new_man['dirs']}
    changed = 0
    for d in orig_man['dirs']:
        nd = new_dirs.get(d['path'])
        if not check(nd is not None, 'dir missing: ' + d['path']):
            continue
        if nd['records'] != d['records']:
            changed += 1
            rest = [r for r in nd['records'] if r in d['records']]
            check(rest == d['records'], 'original records altered in ' + d['path'])
            check(d['path'] == 'MEDIA/TRANSLATIONS/', 'unexpected modified dir ' + d['path'])
    check(changed == 1, 'exactly one original dir gains records (MEDIA/TRANSLATIONS/), got %d' % changed)
    check([d['path'] for d in new_man['dirs']] == sorted(new_dirs), 'dir list sorted')
    for key in ('version', 'build_id', 'root'):
        check(new_man[key] == orig_man[key], 'MAN header field changed: ' + key)
    print('    %d dirs, %d original records checked' % (len(orig_man['dirs']), sum(len(d['records']) for d in orig_man['dirs'])))

    print('[2] new entries')
    orig_files = dict(man_files(orig_man))
    new_files = {p: r for p, r in man_files(new_man) if p not in orig_files}
    check(set(new_files) == {f['path'] for f in info['files']}, 'new file list matches patch_info')
    data = {}
    for p, r in sorted(new_files.items()):
        check(r['offset'] >= info['original']['pak_size'], 'new entry inside original data: ' + p)
        blob = vpak.entry(r['offset'], r['size'])
        check(crc32(blob) == r['crc'], 'crc ' + p)
        data[p] = blob
    # every folder record points to an existing dir record and vice versa
    for d in new_man['dirs']:
        for r in d['records']:
            if r['type'] == FT_FOLDER:
                check(d['path'] + r['name'] in new_dirs, 'folder record without dir: ' + d['path'] + r['name'])
    ends = sorted((r['offset'], r['offset'] + 8 + struct.unpack('<I', vpak.read_raw(r['offset'] + 4, 4))[0]) for r in new_files.values())
    check(ends[0][0] == info['original']['pak_size'] and ends[-1][1] == info['patched']['pak_size'], 'appended entries cover the tail')
    check(all(a[1] == b[0] for a, b in zip(ends, ends[1:])), 'appended entries are contiguous')
    print('    %d files read back OK' % len(data))

    print('[3] language pack content')
    P = config.PACK_DIR
    _, desc = parse_dat(data['MEDIA/TRANSLATIONS/VIETNAMESE.DAT'])
    props = {k: (t, v) for k, t, v in desc['props']}
    check(desc['name'] == tl2hash('LANGUAGE'), 'descriptor root')
    check(props.get(tl2hash('NAME')) == (T_STRING, config.LANG_NAME), 'descriptor NAME')
    check(props.get(tl2hash('DISPLAYNAME')) == (T_STRING, config.LANG_DISPLAY), 'descriptor DISPLAYNAME')
    check(props.get(tl2hash('ID')) == (T_INT, config.LANG_ID), 'descriptor ID')
    tf = props.get(tl2hash('TRANSLATIONFILE'), (0, ''))[1]
    check(tf.upper() in new_files, 'TRANSLATIONFILE resolves: ' + tf)
    ids = set()
    for p, r in orig_files.items():
        if re.match(r'MEDIA/TRANSLATIONS/[^/]+\.DAT$', p):
            _, od = parse_dat(vpak.entry(r['offset'], r['size']))
            ids.add([v for k, t, v in od['props'] if k == tl2hash('ID')][0])
    check(config.LANG_ID in ids, 'language ID %d is one of the official IDs %s (other IDs crash the game)' % (config.LANG_ID, sorted(ids)))
    fp = desc['kids'][0]['props']
    target = [v for k, t, v in fp if k != tl2hash('ORIGINAL')][0]
    check(any(p.startswith(target.upper()) for p in new_files), 'FOLDERPAIR target exists: ' + target)

    _, table = parse_dat(data[tf.upper()])
    final = json.load(open(os.path.join(config.WORK, 'vi_final.json'), encoding='utf-8'))
    O, T = tl2hash('ORIGINAL'), tl2hash('TRANSLATION')
    pairs = {}
    for k in table['kids']:
        pp = {a: v for a, _, v in k['props']}
        pairs[pp[O]] = pp[T]
    check(pairs == final, 'translation table equals vi_final.json')
    known = set(json.load(open(os.path.join(config.WORK, 'strings.json'), encoding='utf-8')))
    check(all(en in known for en in pairs), 'every ORIGINAL is a real game string')
    check(all(tokens(en) == tokens(vi) for en, vi in pairs.items()), 'tokens preserved in every translation')
    print('    %d translations' % len(pairs))

    print('[4] fonts')
    ui = P + 'UI/'
    scheme = data[ui.upper() + 'HUD/SCHEMES/CEGUIWIDGETS.SCHEME'].decode('utf-8')
    ET.fromstring(scheme)
    used_chars = set(''.join(pairs.values())) | set(''.join(pairs))
    used_chars = {c for c in used_chars if ord(c) >= 32}
    tmpl = 'MEDIA/TRANSLATIONS/GERMAN/UI/'
    ours = sorted(p[len(ui):] for p in new_files if p.startswith(ui.upper()))
    theirs = sorted(p[len(tmpl):] for p in orig_files if p.startswith(tmpl))
    check(ours == theirs, 'UI folder has exactly the same files as the official German pack')

    def resolve(path):
        """Game path -> blob, applying our FOLDERPAIR (MEDIA/UI/ -> pack UI/) first, like the game."""
        path = path.upper()
        if path.startswith('MEDIA/UI/') and ui.upper() + path[len('MEDIA/UI/'):] in new_files:
            path = ui.upper() + path[len('MEDIA/UI/'):]
        if path in data:
            return path, data[path]
        if path in orig_files:
            r = orig_files[path]
            return path, vpak.entry(r['offset'], r['size'])
        return path, None

    for fname in re.findall(r'Filename="([^"]+)"', scheme):
        if re.search(r'(?i)\.(imageset|looknfeel|font)$', fname):
            check(resolve(fname)[1] is not None, 'scheme file resolves: ' + fname)
    for fname in re.findall(r'Filename="([^"]+\.font)"', scheme, re.I):
        path, blob = resolve(fname)
        if 'CJK' in path:                  # CJK fonts keep pointing at the game's own files
            continue
        node = ET.fromstring(blob.decode('utf-8'))
        ttf, tblob = resolve(node.get('Filename'))
        if not check(tblob is not None, '%s -> TTF resolves: %s' % (fname, ttf)):
            continue
        font = TTFont(io.BytesIO(tblob))
        cmap = font.getBestCmap()
        missing = sorted(c for c in used_chars if ord(c) not in cmap)
        check(not missing, '%s (%s) lacks glyphs: %r' % (node.get('Name'), ttf, ''.join(missing)[:40]))
        print('    %-15s size %-3s %-48s all %d used chars present' % (node.get('Name'), node.get('Size'), ttf, len(used_chars)))

    fullp = os.path.join(config.OUTPUT, 'full', 'PAKS', 'DATA.PAK')
    if os.path.exists(fullp):
        print('[5] full patched copy')
        h = hashlib.sha256()
        with open(fullp, 'rb') as fh:
            for chunk in iter(lambda: fh.read(1 << 24), b''):
                h.update(chunk)
        check(h.hexdigest() == info['patched']['pak_sha256'], 'full copy hash == original + append')

    print('\nRESULT:', 'OK' if not fails else '%d FAILURES' % len(fails))
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
