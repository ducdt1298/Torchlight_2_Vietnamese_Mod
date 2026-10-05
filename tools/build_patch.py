# -*- coding: utf-8 -*-
"""Create the DATA.PAK patch (method B): the language pack is appended to the end of
DATA.PAK and registered in DATA.PAK.MAN. Existing entries are never touched, so the
original game data stays byte-for-byte identical. The game folder is only READ.

Outputs (output/):
  PAKS/DATA.PAK.MAN            patched manifest
  PAKS/DATA.PAK.vi-append      bytes to append to the original DATA.PAK
  PAKS/DATA.PAK.MAN.original   copy of the original manifest (used by uninstall)
  patch_info.json              sizes + SHA-256 of original/patched files, added files
  full/PAKS/DATA.PAK(.MAN)     complete patched copies (only with --full)
Usage: python build_patch.py [--full]
"""
import copy
import hashlib
import json
import os
import shutil
import struct
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from tl2lib import FT_FOLDER, crc32, encode_entry, man_files, parse_man, write_man

TYPES = {'.DAT': 0, '.LAYOUT': 1, '.DDS': 4, '.PNG': 5, '.IMAGESET': 11, '.TTF': 12, '.FONT': 13,
         '.SCHEME': 19, '.LOOKNFEEL': 20}


def sha256_file(path, h=None):
    h = h or hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b''):
            h.update(chunk)
    return h


def collect_build_files():
    out = []
    root = os.path.join(config.BUILD, 'MEDIA')
    for dirpath, _, names in os.walk(root):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, config.BUILD).replace(os.sep, '/').upper()
            out.append((rel, open(full, 'rb').read()))
    return sorted(out)


def record_key(rec):
    return (rec['type'] == FT_FOLDER, rec['name'])


def insert_sorted(records, rec):
    """Insert keeping the manifest rule (files by name, then folders by name) without reordering others."""
    k = record_key(rec)
    pos = len(records)
    for i, r in enumerate(records):
        if record_key(r) > k:
            pos = i
            break
    records.insert(pos, rec)


def main():
    full = '--full' in sys.argv
    orig_man_bytes = open(config.MAN, 'rb').read()
    man = parse_man(orig_man_bytes)
    new_man = copy.deepcopy(man)
    orig_size = os.path.getsize(config.PAK)
    with open(config.PAK, 'rb') as fh:
        max_stored, build_id = struct.unpack('<II', fh.read(8))
    existing = set(p for p, _ in man_files(man))
    dirs = {d['path']: d for d in new_man['dirs']}

    now = int((time.time() + 11644473600) * 10 ** 7)      # Windows FILETIME
    tail = bytearray()
    added, added_records, added_dirs = [], 0, 0

    def ensure_dir(path):
        nonlocal added_records, added_dirs
        if path in dirs:
            return dirs[path]
        parent, _, _ = path[:-1].rpartition('/')
        parent += '/'
        p = ensure_dir(parent)
        insert_sorted(p['records'], {'crc': 0, 'type': FT_FOLDER, 'name': path[len(parent):],
                                     'offset': 0, 'size': 0, 'time': 0})
        added_records += 1
        d = {'path': path, 'records': []}
        dirs[path] = d
        added_dirs += 1
        return d

    for path, data in collect_build_files():
        if path in existing:
            raise SystemExit('refusing to override an existing game file: ' + path)
        ext = os.path.splitext(path)[1]
        if ext not in TYPES:
            raise SystemExit('unknown file type: ' + path)
        entry = encode_entry(data)
        stored = struct.unpack_from('<I', entry, 4)[0]
        if stored > max_stored:
            raise SystemExit('%s: stored size %d exceeds PAK header limit %d' % (path, stored, max_stored))
        folder, _, name = path.rpartition('/')
        d = ensure_dir(folder + '/')
        rec = {'crc': crc32(data), 'type': TYPES[ext], 'name': name,
               'offset': orig_size + len(tail), 'size': len(data), 'time': now}
        insert_sorted(d['records'], rec)
        tail += entry
        added_records += 1
        added.append({'path': path, 'offset': rec['offset'], 'size': len(data), 'stored': stored, 'crc32': rec['crc']})

    new_man['dirs'] = sorted(dirs.values(), key=lambda d: d['path'])
    new_man['total'] = man['total'] + added_records + added_dirs
    new_man_bytes = write_man(new_man)
    assert parse_man(new_man_bytes) == new_man

    out = os.path.join(config.OUTPUT, 'PAKS')
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, 'DATA.PAK.MAN'), 'wb').write(new_man_bytes)
    open(os.path.join(out, 'DATA.PAK.vi-append'), 'wb').write(bytes(tail))
    open(os.path.join(out, 'DATA.PAK.MAN.original'), 'wb').write(orig_man_bytes)

    h = sha256_file(config.PAK)
    orig_pak_sha = h.hexdigest()
    h.update(bytes(tail))
    patched_pak_sha = h.hexdigest()
    info = {
        'description': 'Torchlight II Vietnamese language pack, installed by appending to DATA.PAK (method B)',
        'built': time.strftime('%Y-%m-%d %H:%M:%S'),
        'language': {'name': config.LANG_NAME, 'display': config.LANG_DISPLAY, 'id': config.LANG_ID},
        'original': {'pak_size': orig_size, 'pak_sha256': orig_pak_sha,
                     'man_size': len(orig_man_bytes), 'man_sha256': hashlib.sha256(orig_man_bytes).hexdigest()},
        'patched': {'pak_size': orig_size + len(tail), 'pak_sha256': patched_pak_sha,
                    'man_size': len(new_man_bytes), 'man_sha256': hashlib.sha256(new_man_bytes).hexdigest()},
        'append': {'size': len(tail), 'sha256': hashlib.sha256(bytes(tail)).hexdigest()},
        'pak_header': {'max_stored_entry': max_stored, 'build_id': '%08x' % build_id},
        'man': {'records_added': added_records, 'dirs_added': added_dirs,
                'total_before': man['total'], 'total_after': new_man['total']},
        'files': added,
    }
    json.dump(info, open(os.path.join(config.OUTPUT, 'patch_info.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('added %d files (%d bytes appended), %d new manifest records, %d new dirs' % (
        len(added), len(tail), added_records, added_dirs))
    print('original DATA.PAK %d bytes -> patched %d bytes' % (orig_size, orig_size + len(tail)))

    if full:
        fdir = os.path.join(config.OUTPUT, 'full', 'PAKS')
        os.makedirs(fdir, exist_ok=True)
        dst = os.path.join(fdir, 'DATA.PAK')
        shutil.copyfile(config.PAK, dst)
        with open(dst, 'ab') as fh:
            fh.write(bytes(tail))
        open(os.path.join(fdir, 'DATA.PAK.MAN'), 'wb').write(new_man_bytes)
        print('full patched copy written to', fdir)


if __name__ == '__main__':
    main()
