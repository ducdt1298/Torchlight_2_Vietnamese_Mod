# -*- coding: utf-8 -*-
"""Torchlight II container formats: DATA.PAK, DATA.PAK.MAN and binary .DAT.

All integers are little-endian. A "wstr" is a u16 character count followed by
that many UTF-16LE code units (no terminator).

PAK      : 8-byte header [u32 largest stored entry size][u32 build id], then
           entries [u32 uncompressed size][u32 stored size][data]; stored size
           0 means the data is kept raw (uncompressed size bytes).
PAK.MAN  : [u16 version=2][u32 build id][wstr root "MEDIA/"][u32 total]
           [u32 dir count], then per directory [wstr path][u32 n] and n records
           [u32 crc32 of uncompressed data][u8 type][wstr name][u32 offset]
           [u32 uncompressed size][u64 FILETIME]. Sub-folders appear as type 7
           records (crc/offset/size 0) and again as their own directory.
Binary DAT: [u32 version=2][u32 n strings]{[u32 id][wstr]}, then a block tree:
           [u32 name hash][u32 n props]{[u32 key hash][u32 type][value]}
           [u32 n children]{block}.
"""
import struct
import zlib

# ---------------------------------------------------------------- primitives


class Reader:
    def __init__(self, buf, pos=0):
        self.b = buf
        self.p = pos

    def u8(self):
        v = self.b[self.p]
        self.p += 1
        return v

    def u16(self):
        v = struct.unpack_from('<H', self.b, self.p)[0]
        self.p += 2
        return v

    def u32(self):
        v = struct.unpack_from('<I', self.b, self.p)[0]
        self.p += 4
        return v

    def i32(self):
        v = struct.unpack_from('<i', self.b, self.p)[0]
        self.p += 4
        return v

    def u64(self):
        v = struct.unpack_from('<Q', self.b, self.p)[0]
        self.p += 8
        return v

    def i64(self):
        v = struct.unpack_from('<q', self.b, self.p)[0]
        self.p += 8
        return v

    def f32(self):
        v = struct.unpack_from('<f', self.b, self.p)[0]
        self.p += 4
        return v

    def f64(self):
        v = struct.unpack_from('<d', self.b, self.p)[0]
        self.p += 8
        return v

    def wstr(self):
        n = self.u16()
        s = self.b[self.p:self.p + 2 * n].decode('utf-16-le')
        self.p += 2 * n
        return s


def wstr(s):
    b = s.encode('utf-16-le')
    if len(b) // 2 > 0xFFFF:
        raise ValueError('string too long for wstr: %d chars' % (len(b) // 2))
    return struct.pack('<H', len(b) // 2) + b


def tl2hash(s):
    """Hash used for DAT block and property names (Knuth DEK, seeded with len)."""
    h = len(s)
    for c in s:
        h = ((h >> 27) ^ (h << 5) ^ ord(c)) & 0xFFFFFFFF
    return h


def crc32(data):
    return zlib.crc32(data) & 0xFFFFFFFF


# ---------------------------------------------------------------- PAK.MAN

FT_DAT, FT_LAYOUT, FT_FOLDER, FT_TTF, FT_FONT = 0, 1, 7, 12, 13


def parse_man(buf):
    r = Reader(buf)
    man = {'version': r.u16(), 'build_id': r.u32(), 'root': r.wstr(),
           'total': r.u32(), 'dirs': []}
    ndirs = r.u32()
    for _ in range(ndirs):
        path = r.wstr()
        n = r.u32()
        recs = []
        for _ in range(n):
            recs.append({'crc': r.u32(), 'type': r.u8(), 'name': r.wstr(),
                         'offset': r.u32(), 'size': r.u32(), 'time': r.u64()})
        man['dirs'].append({'path': path, 'records': recs})
    if r.p != len(buf):
        raise ValueError('MAN has %d trailing bytes' % (len(buf) - r.p))
    return man


def write_man(man):
    out = bytearray()
    out += struct.pack('<HI', man['version'], man['build_id'])
    out += wstr(man['root'])
    out += struct.pack('<II', man['total'], len(man['dirs']))
    for d in man['dirs']:
        out += wstr(d['path'])
        out += struct.pack('<I', len(d['records']))
        for rec in d['records']:
            out += struct.pack('<IB', rec['crc'], rec['type'])
            out += wstr(rec['name'])
            out += struct.pack('<IIQ', rec['offset'], rec['size'], rec['time'])
    return bytes(out)


def man_files(man):
    """Yield (full_path, record) for every non-folder record."""
    for d in man['dirs']:
        for rec in d['records']:
            if rec['type'] != FT_FOLDER:
                yield d['path'] + rec['name'], rec


# ---------------------------------------------------------------- PAK entries


def read_entry(f, offset):
    """Read and decompress the entry at `offset` of an open PAK file."""
    f.seek(offset)
    usize, csize = struct.unpack('<II', f.read(8))
    data = f.read(csize if csize else usize)
    if csize:
        data = zlib.decompress(data)
    if len(data) != usize:
        raise ValueError('entry at %d: size mismatch' % offset)
    return data


def encode_entry(data, level=9):
    """Encode `data` as a PAK entry (header + zlib stream)."""
    comp = zlib.compress(data, level)
    return struct.pack('<II', len(data), len(comp)) + comp


# ---------------------------------------------------------------- binary DAT

T_INT, T_FLOAT, T_DOUBLE, T_UINT, T_STRING, T_BOOL, T_INT64, T_TRANSLATE = 1, 2, 3, 4, 5, 6, 7, 8


def parse_dat(buf):
    """Return (version, root_block). Blocks: {'name': hash, 'props': [(key, type, value)], 'kids': [...]}.
    String-typed values are returned as Python strings."""
    r = Reader(buf)
    version = r.u32()
    strings = {}
    for _ in range(r.u32()):
        sid = r.u32()
        strings[sid] = r.wstr()

    def block():
        name = r.u32()
        props = []
        for _ in range(r.u32()):
            key, typ = r.u32(), r.u32()
            if typ == T_INT:
                val = r.i32()
            elif typ == T_FLOAT:
                val = r.f32()
            elif typ == T_DOUBLE:
                val = r.f64()
            elif typ in (T_UINT, T_BOOL):
                val = r.u32()
            elif typ in (T_STRING, T_TRANSLATE):
                val = strings.get(r.u32(), '')
            elif typ == T_INT64:
                val = r.i64()
            else:
                raise ValueError('unknown DAT value type %d at %d' % (typ, r.p))
            props.append((key, typ, val))
        kids = [block() for _ in range(r.u32())]
        return {'name': name, 'props': props, 'kids': kids}

    root = block()
    return version, root


def write_dat(root, version=2):
    """Serialize a block tree (see parse_dat) to binary DAT. Strings are deduplicated."""
    ids = {}
    order = []

    def sid(s):
        if s not in ids:
            ids[s] = len(order) + 1
            order.append(s)
        return ids[s]

    body = bytearray()

    def block(b):
        body.extend(struct.pack('<II', b['name'], len(b['props'])))
        for key, typ, val in b['props']:
            body.extend(struct.pack('<II', key, typ))
            if typ == T_INT:
                body.extend(struct.pack('<i', val))
            elif typ == T_FLOAT:
                body.extend(struct.pack('<f', val))
            elif typ == T_DOUBLE:
                body.extend(struct.pack('<d', val))
            elif typ in (T_UINT, T_BOOL):
                body.extend(struct.pack('<I', val))
            elif typ in (T_STRING, T_TRANSLATE):
                body.extend(struct.pack('<I', sid(val)))
            elif typ == T_INT64:
                body.extend(struct.pack('<q', val))
            else:
                raise ValueError('unknown DAT value type %d' % typ)
        body.extend(struct.pack('<I', len(b['kids'])))
        for k in b['kids']:
            block(k)

    block(root)
    head = bytearray(struct.pack('<II', version, len(order)))
    for s in order:
        head += struct.pack('<I', ids[s]) + wstr(s)
    return bytes(head + body)


def block(name, props=(), kids=()):
    """Convenience constructor: props given as (NAME, type, value) with NAME a string."""
    return {'name': tl2hash(name),
            'props': [(tl2hash(k), t, v) for k, t, v in props],
            'kids': list(kids)}
