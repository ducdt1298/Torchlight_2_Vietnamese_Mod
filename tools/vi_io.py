# -*- coding: utf-8 -*-
"""Line-based text format used for translation batches (no escaping needed).

Batch input  (translation/batches/<batch>.txt):
    @@ <id> | <mode> | <context>
    <English text on one line>
Translation output (translation/vi/<batch>*.txt, any number of part files):
    @@ <id>
    <Vietnamese text on one line>

Strings never contain real newlines; the two characters backslash + n are the
game's own line-break marker and are copied as-is.
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

TOKEN_RE = re.compile(r'\[\[[^\]]*\]\]|\[[^\[\]]+\]|<[^<>]+>|\|c[0-9A-Fa-f]{8}|\|u|\\n')


def tokens(s):
    return sorted(TOKEN_RE.findall(s))


def batch_names():
    return sorted(os.path.splitext(os.path.basename(p))[0]
                  for p in glob.glob(os.path.join(config.TRANSLATION, 'batches', 'b*.json')))


def load_batch(name):
    return json.load(open(os.path.join(config.TRANSLATION, 'batches', name + '.json'), encoding='utf-8'))


def write_batch_txt(name):
    b = load_batch(name)
    lines = ['# %s: %d strings. Format: "@@ id | mode | context" then the English text on the next line.'
             % (name, b['count'])]
    for it in b['items']:
        lines.append('@@ %d | %s | %s' % (it['id'], it['mode'], it['ctx']))
        lines.append(it['en'])
    with open(os.path.join(config.TRANSLATION, 'batches', name + '.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(lines) + '\n')


def parse_vi_file(path):
    out = {}
    cur = None
    with open(path, encoding='utf-8-sig') as fh:
        for raw in fh.read().split('\n'):
            line = raw[:-1] if raw.endswith('\r') else raw
            m = re.match(r'^@@\s*(\d+)\s*(\|.*)?$', line)
            if m:
                cur = int(m.group(1))
                out[cur] = None
            elif cur is not None and out[cur] is None:
                out[cur] = line
            # lines after the text line (or before the first @@) are ignored
    return out


def load_translations(name):
    """All part files of a batch, later files override earlier ones."""
    res = {}
    files = sorted(glob.glob(os.path.join(config.TRANSLATION, 'vi', name + '*.txt')))
    for p in files:
        res.update(parse_vi_file(p))
    return res, files


if __name__ == '__main__':
    for n in batch_names():
        write_batch_txt(n)
    print('wrote .txt for', len(batch_names()), 'batches')
