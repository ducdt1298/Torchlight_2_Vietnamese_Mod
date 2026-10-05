# -*- coding: utf-8 -*-
"""After a game update: re-extract the game's strings (read-only) and put every string
that no existing batch covers into a new batch translation/batches/bNN_update_YYYYMMDD.

Existing batches and translations are kept as they are (their ids stay valid). Strings the
game no longer uses are simply ignored at build time.
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config
from vi_io import batch_names, load_batch, write_batch_txt


def main():
    for script in ('extract_strings.py', 'classify.py'):
        subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, script)], check=True)
    C = json.load(open(os.path.join(config.WORK, 'classified.json'), encoding='utf-8'))
    covered, max_id = set(), 0
    for n in batch_names():
        for it in load_batch(n)['items']:
            covered.add(it['en'])
            max_id = max(max_id, it['id'])
    new = sorted((s for s, v in C.items() if v['class'] in ('translate', 'decide') and s not in covered),
                 key=lambda s: (C[s]['hint'], s))
    keep = sorted(s for s, v in C.items() if v['class'] == 'keep')
    with open(os.path.join(config.TRANSLATION, 'names_keep_english.txt'), 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(keep) + '\n')
    if not new:
        print('No new strings to translate.')
        return
    name = 'b%02d_update_%s' % (len(batch_names()) + 1, time.strftime('%Y%m%d'))
    items = [{'id': max_id + 1 + i, 'mode': C[s]['class'], 'ctx': C[s]['hint'], 'en': s} for i, s in enumerate(new)]
    json.dump({'batch': name, 'count': len(items), 'items': items},
              open(os.path.join(config.TRANSLATION, 'batches', name + '.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    write_batch_txt(name)
    print('%d new strings -> translation/batches/%s.txt (translate into translation/vi/%s.part01.txt)' % (len(items), name, name))


if __name__ == '__main__':
    main()
