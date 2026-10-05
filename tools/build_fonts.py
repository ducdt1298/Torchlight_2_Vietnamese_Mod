# -*- coding: utf-8 -*-
"""Build the Vietnamese-capable UI fonts of the language pack.

The game's own fonts (except Arial) have no Vietnamese glyphs, so each is replaced by
an open-licensed font of similar style. Every replacement is
  1. instantiated to a static instance (the game's FreeType predates variable fonts),
  2. subset to Latin + Vietnamese + punctuation,
  3. scaled (via unitsPerEm) so its cap height matches the original font, keeping the
     game's font sizes and layouts valid,
  4. given vertical metrics close to the original line height (a little taller so
     stacked diacritics such as "Ấ" fit),
  5. renamed "TL2VI ..." (modified OFL fonts must not keep reserved names).
Arial is copied unchanged from the game: it already covers Vietnamese.
"""
import io
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from tl2lib import man_files, parse_man, read_entry

SRC = os.path.join(config.FONTS, 'src')
OUT = os.path.join(config.BUILD, 'MEDIA', 'TRANSLATIONS', 'VIETNAMESE', 'UI')

# file, variable axes, scale (cap height match), ascender/descender in em of the final font, family
FONTS = {
    'VI_SERIF.TTF': ('bitter__Bitter[wght].ttf', {'wght': 700}, 0.943, 0.80, 0.277, 'TL2VI Serif'),
    'VI_HUGE.TTF': ('alegreya__Alegreya[wght].ttf', {'wght': 900}, 1.12, 1.00, 0.30, 'TL2VI Huge'),
    'VI_TORCH.TTF': ('bangers__Bangers-Regular.ttf', None, 1.045, 1.15, 0.212, 'TL2VI Torch'),
    'VI_MONO.TTF': ('notosansmono__NotoSansMono[wdth,wght].ttf', {'wdth': 100, 'wght': 400}, 0.965, 0.95, 0.23, 'TL2VI Mono'),
}

VIET_LOWER = 'aàáảãạăằắẳẵặâầấẩẫậbcdđeèéẻẽẹêềếểễệghiìíỉĩịklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvxyỳýỷỹỵ'
VIET = sorted({c for c in VIET_LOWER + VIET_LOWER.upper() if ord(c) > 0x7F})


def charset():
    cps = set(range(0x20, 0x7F)) | set(range(0xA0, 0x180))
    cps |= {0x1A0, 0x1A1, 0x1AF, 0x1B0} | set(range(0x1EA0, 0x1EFA))
    cps |= set(range(0x2010, 0x2028)) | set(range(0x2030, 0x203B)) | {0x20AC, 0x2122, 0x2212, 0x2190, 0x2191, 0x2192, 0x2193}
    cps |= set(range(0x300, 0x310)) | {0x323}          # combining marks, in case un-normalized text slips through
    return cps


def build_one(out_name, src, axes, scale, asc, desc, family):
    font = TTFont(os.path.join(SRC, src))
    if axes:
        font = instancer.instantiateVariableFont(font, axes, updateFontNames=False)
    opts = subset.Options()
    opts.layout_features = ['kern']
    opts.name_IDs = ['*']
    opts.name_languages = ['*']
    opts.notdef_outline = True
    opts.glyph_names = False
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=charset())
    sub.subset(font)
    for tag in ('STAT', 'MVAR', 'HVAR', 'VVAR', 'avar', 'fvar', 'gvar', 'cvar', 'DSIG'):
        if tag in font:
            del font[tag]

    upm = font['head'].unitsPerEm
    new_upm = int(round(upm / scale))
    font['head'].unitsPerEm = new_upm            # outlines untouched: everything renders `scale` times larger
    a, d = int(round(asc * new_upm)), int(round(desc * new_upm))
    hhea, os2 = font['hhea'], font['OS/2']
    hhea.ascent, hhea.descent, hhea.lineGap = a, -d, 0
    os2.sTypoAscender, os2.sTypoDescender, os2.sTypoLineGap = a, -d, 0
    ymax = max(font['head'].yMax, a)
    ymin = min(font['head'].yMin, -d)
    os2.usWinAscent, os2.usWinDescent = ymax, -ymin

    name = font['name']
    for rec in list(name.names):
        if rec.nameID in (1, 3, 4, 6, 16, 17, 21, 22, 25):
            name.removeNames(nameID=rec.nameID)
    ps = family.replace(' ', '') + '-Regular'
    for nid, val in ((1, family), (2, 'Regular'), (3, ps + ';TL2 Vietnamese pack'), (4, family), (6, ps)):
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    old = name.getDebugName(5) or ''
    name.setName((old + '; modified for Torchlight II Vietnamese pack').strip('; '), 5, 3, 1, 0x409)

    buf = io.BytesIO()
    font.save(buf)
    data = buf.getvalue()
    check = TTFont(io.BytesIO(data))
    cmap = check.getBestCmap()
    missing = [c for c in VIET if ord(c) not in cmap]
    if missing:
        raise SystemExit('%s: missing Vietnamese glyphs %s' % (out_name, ''.join(missing)))
    with open(os.path.join(OUT, out_name), 'wb') as fh:
        fh.write(data)
    print('%-13s from %-44s %7d bytes  %4d chars  upm %d->%d' % (out_name, src, len(data), len(cmap), upm, new_upm))


def main():
    os.makedirs(OUT, exist_ok=True)
    for out_name, spec in FONTS.items():
        build_one(out_name, *spec)
    man = parse_man(open(config.MAN, 'rb').read())
    files = dict(man_files(man))
    with open(config.PAK, 'rb') as pak:
        arial = read_entry(pak, files['MEDIA/UI/ARIAL.TTF']['offset'])
    with open(os.path.join(OUT, 'ARIAL.TTF'), 'wb') as fh:
        fh.write(arial)
    print('ARIAL.TTF     copied from the game (%d bytes)' % len(arial))


if __name__ == '__main__':
    main()
