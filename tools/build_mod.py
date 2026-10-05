# -*- coding: utf-8 -*-
"""Build the Vietnamese translation as a Torchlight II .MOD file (output/mod/).

Contents (nothing gameplay-related, so no game content is overridden):
  MEDIA/TRANSLATIONS/VIETNAMESE.DAT              language "Tiếng Việt" (ID 1, like the old community mod)
  MEDIA/TRANSLATIONS/VIETNAMESE/TRANSLATION.DAT  English -> Vietnamese table (work/vi_final.json)
  MEDIA/UI/<every UI TTF except ARIAL.TTF>       the game's own Arial, so every UI font has Vietnamese
                                                 glyphs while the mod is enabled ("one stable font")

Container layout mirrors a GUTS-built mod:
  header  u16 4, u16 mod version, 4 x u16 game version, u32 data offset, u32 manifest offset,
          wstr title/author/description/website/download, u64 GUID, 16 zero bytes
  data    u32 largest stored entry, u32 build id, then entries [u32 size][u32 stored][zlib]
          (manifest offsets are relative to the data offset)
  MAN     root dir '' -> 'MEDIA/', then every dir holding files, then every dir holding folders
Usage: python build_mod.py
"""
import hashlib
import json
import os
import random
import struct
import sys
import time
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from tl2lib import (FT_FOLDER, T_INT, T_STRING, crc32, man_files, parse_dat, parse_man, read_entry, tl2hash,
                    write_dat, write_man, wstr)

MOD_NAME = 'VIETHOA_ENVI.MOD'
TITLE = 'Việt hóa Torchlight II (Anh–Việt)'
DESCRIPTION = ('Việt hóa kiểu Anh–Việt: dịch hội thoại, nhiệm vụ, mô tả kỹ năng/vật phẩm và giao diện; '
               'giữ tên kỹ năng, vật phẩm, quái bằng tiếng Anh. Chỉ thêm gói ngôn ngữ và font, '
               'không thay đổi dữ liệu gameplay. Chọn Options > Language > Tiếng Việt.')
MOD_VERSION = 1
GAME_VERSION = (1, 25, 5, 2)          # value written by GUTS in mods that load fine in v1.26
TYPES = {'.DAT': 0, '.TTF': 12}


def rolling_hash(data):
    """2nd u32 of a PAK/MOD data section. The game recomputes it and rejects the whole archive on a
    mismatch ("Unable to load mod"; for DATA.PAK: no UI resources -> crash). Algorithm from
    heiybb/TL2-RE (reverse-engineered from EditorGuts.dll); verified here against VN-MOD.MOD,
    EDITORMOD.MOD and the game's own DATA.PAK."""
    n = len(data)
    if n <= 8:
        return 0
    divisor = 25 + ((695696193 * n) & 0xFFFFFFFF) % 51
    stride = max(2, n // divisor)
    h = n & 0xFFFFFFFF
    for k in range(8, n, stride):
        b = data[k]
        h = ((b - 256 if b >= 128 else b) + 33 * h) & 0xFFFFFFFF
    b = data[n - 1]
    return ((b - 256 if b >= 128 else b) + 33 * h) & 0xFFFFFFFF


def manifest_hash(man):
    """u32 at offset 2 of a PAK.MAN / MOD manifest, also validated by the game (same source)."""
    n = len(man)
    stride = 15 + ((695696193 * n) & 0xFFFFFFFF) % 11
    h = 8234
    for k in range(0, n, stride):
        b = man[k]
        h = ((b - 256 if b >= 128 else b) + 33 * h) & 0xFFFFFFFF
    return h


def build_files():
    final = json.load(open(os.path.join(config.WORK, 'vi_final.json'), encoding='utf-8'))
    O, T = tl2hash('ORIGINAL'), tl2hash('TRANSLATION')
    table = write_dat({'name': tl2hash('TRANSLATIONS'), 'props': [], 'kids': [
        {'name': tl2hash('TRANSLATION'), 'props': [(O, T_STRING, en), (T, T_STRING, vi)], 'kids': []}
        for en, vi in final.items()]})
    desc = write_dat({'name': tl2hash('LANGUAGE'), 'props': [
        (tl2hash('DISPLAYNAME'), T_STRING, config.LANG_DISPLAY),
        (tl2hash('NAME'), T_STRING, config.LANG_NAME),
        (tl2hash('TRANSLATIONFILE'), T_STRING, config.PACK_DIR + 'TRANSLATION.dat'),
        (tl2hash('ID'), T_INT, config.LANG_ID)], 'kids': []})
    files = {'MEDIA/TRANSLATIONS/VIETNAMESE.DAT': desc, config.PACK_DIR + 'TRANSLATION.DAT': table}

    man = parse_man(open(config.MAN, 'rb').read())
    game = dict(man_files(man))
    with open(config.PAK, 'rb') as pak:
        arial = read_entry(pak, game['MEDIA/UI/ARIAL.TTF']['offset'])
    for p in sorted(game):
        if p.startswith('MEDIA/UI/') and p.count('/') == 2 and p.endswith('.TTF') and p != 'MEDIA/UI/ARIAL.TTF':
            files[p] = arial
    return files, len(final)


def build_mod(files):
    rnd = random.SystemRandom()
    now = int((time.time() + 11644473600) * 10 ** 7)
    data = bytearray()
    records = {}                                           # dir -> list of file records
    max_stored = 0
    for path in sorted(files):
        blob = files[path]
        comp = zlib.compress(blob, 6)
        entry = struct.pack('<II', len(blob), len(comp)) + comp
        folder, _, name = path.rpartition('/')
        records.setdefault(folder + '/', []).append({'crc': crc32(blob), 'type': TYPES[os.path.splitext(name)[1]],
                                                     'name': name, 'offset': 8 + len(data), 'size': len(blob), 'time': now})
        max_stored = max(max_stored, len(comp))
        data += entry
    # folder structure
    subdirs = {}
    for d in list(records):
        parts = d.rstrip('/').split('/')
        for i in range(1, len(parts)):
            parent, child = '/'.join(parts[:i]) + '/', parts[i] + '/'
            subdirs.setdefault(parent, set()).add(child)
    dirs = [{'path': '', 'records': [{'crc': 0, 'type': FT_FOLDER, 'name': 'MEDIA/', 'offset': 0, 'size': 0, 'time': 0}]}]
    for d in sorted(records):
        dirs.append({'path': d, 'records': sorted(records[d], key=lambda r: r['name'])})
    for d in sorted(subdirs):
        dirs.append({'path': d, 'records': [{'crc': 0, 'type': FT_FOLDER, 'name': c, 'offset': 0, 'size': 0, 'time': 0}
                                             for c in sorted(subdirs[d])]})
    nrec = sum(len(d['records']) for d in dirs)
    nfold = sum(1 for d in dirs for r in d['records'] if r['type'] == FT_FOLDER)
    man = {'version': 2, 'build_id': 0, 'root': 'MEDIA/',
           'total': nrec + len(dirs) + nfold - 1, 'dirs': dirs}
    man_bytes = bytearray(write_man(man))
    man['build_id'] = manifest_hash(man_bytes)     # offset 2 is never sampled, so patching after is consistent
    struct.pack_into('<I', man_bytes, 2, man['build_id'])
    man_bytes = bytes(man_bytes)

    info_path = os.path.join(config.OUTPUT, 'mod', 'mod_info.json')
    if os.path.exists(info_path):              # keep the GUID stable: characters remember the mods they used
        guid = int(json.load(open(info_path, encoding='utf-8'))['guid'])
    else:
        guid = rnd.getrandbits(62) | (1 << 61)
    head = bytearray(struct.pack('<HH4H', 4, MOD_VERSION, *GAME_VERSION))
    strings = wstr(TITLE) + wstr('') + wstr(DESCRIPTION) + wstr('') + wstr('')
    data_off = len(head) + 8 + len(strings) + 8 + 16
    data_section = bytearray(struct.pack('<II', max_stored, 0) + bytes(data))
    struct.pack_into('<I', data_section, 4, rolling_hash(data_section))
    data_section = bytes(data_section)
    man_off = data_off + len(data_section)
    head += struct.pack('<II', data_off, man_off) + strings + struct.pack('<Q', guid) + bytes(16)
    assert len(head) == data_off
    return bytes(head) + data_section + man_bytes, guid, man


def verify(blob, files):
    """Parse the .MOD back like the game/ModLauncher and check every entry."""
    r = 0
    ver, modver = struct.unpack_from('<HH', blob, 0)
    data_off, man_off = struct.unpack_from('<II', blob, 12)
    assert ver == 4
    man = parse_man(blob[man_off:])
    got = {}
    for d in man['dirs']:
        for rec in d['records']:
            if rec['type'] == FT_FOLDER:
                continue
            usize, csize = struct.unpack_from('<II', blob, data_off + rec['offset'])
            raw = zlib.decompress(blob[data_off + rec['offset'] + 8: data_off + rec['offset'] + 8 + csize])
            assert len(raw) == usize == rec['size'] and crc32(raw) == rec['crc'], d['path'] + rec['name']
            got[d['path'] + rec['name']] = raw
            r += 1
    assert got == files, 'content mismatch'
    data_section, man_bytes = blob[data_off:man_off], blob[man_off:]
    assert struct.unpack_from('<I', data_section, 4)[0] == rolling_hash(data_section), 'data rolling hash'
    assert struct.unpack_from('<I', man_bytes, 2)[0] == manifest_hash(man_bytes), 'manifest hash'
    stored = struct.unpack_from('<I', blob, data_off)[0]
    assert stored >= max(struct.unpack_from('<I', blob, data_off + rec['offset'] + 4)[0]
                         for d in man['dirs'] for rec in d['records'] if rec['type'] != FT_FOLDER)
    _, desc = parse_dat(got['MEDIA/TRANSLATIONS/VIETNAMESE.DAT'])
    return r, {k: v for k, t, v in desc['props']}


def self_test():
    """Both hash functions must reproduce the values stored in the game's own DATA.PAK / DATA.PAK.MAN."""
    man = open(config.MAN, 'rb').read()
    assert struct.unpack_from('<I', man, 2)[0] == manifest_hash(man), 'manifest hash no longer matches the game'
    n = os.path.getsize(config.PAK)
    divisor = 25 + ((695696193 * n) & 0xFFFFFFFF) % 51
    stride = max(2, n // divisor)
    with open(config.PAK, 'rb') as f:
        stored = struct.unpack('<II', f.read(8))[1]
        h = n
        for k in list(range(8, n, stride)) + [n - 1]:
            f.seek(k)
            b = f.read(1)[0]
            h = ((b - 256 if b >= 128 else b) + 33 * h) & 0xFFFFFFFF
    assert h == stored, 'data rolling hash no longer matches the game'


def main():
    self_test()
    files, n = build_files()
    blob, guid, man = build_mod(files)
    count, desc = verify(blob, files)
    out = os.path.join(config.OUTPUT, 'mod')
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, MOD_NAME)
    open(path, 'wb').write(blob)
    info = {'file': MOD_NAME, 'guid': str(guid), 'size': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(),
            'translations': n, 'files': sorted(files), 'built': time.strftime('%Y-%m-%d %H:%M:%S')}
    json.dump(info, open(os.path.join(out, 'mod_info.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('%s: %d bytes, %d files verified, %d translations, GUID %d' % (MOD_NAME, len(blob), count, n, guid))
    print('descriptor:', [desc.get(tl2hash(k)) for k in ('DISPLAYNAME', 'NAME', 'TRANSLATIONFILE', 'ID')])
    print('manifest: %d dirs, total %d' % (len(man['dirs']), man['total']))


if __name__ == '__main__':
    main()
