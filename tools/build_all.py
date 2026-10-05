# -*- coding: utf-8 -*-
"""Rebuild the mod from the translations (the game folder is only read).

  validate translations -> merge (build_pack.py: vi_final.json, REVIEW_vi.tsv) -> build_mod.py

Usage: python tools/build_all.py
The batches (translation/batches) are NOT regenerated: their ids link the translations to
the English text. After a game update use tools/update_strings.py to add new strings.
(The abandoned DATA.PAK method used build_patch.py / verify_patch.py; see legacy_pak_method/.)
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(script, *args, check=True):
    print('\n=== %s %s' % (script, ' '.join(args)))
    r = subprocess.run([sys.executable, '-X', 'utf8', os.path.join(HERE, script)] + list(args))
    if check and r.returncode != 0:
        sys.exit('step failed: ' + script)
    return r.returncode


def main():
    if not os.path.exists(os.path.join(HERE, '..', 'work', 'strings.json')):
        run('extract_strings.py')
        run('classify.py')
    if run('validate_translations.py', check=False):
        print('(validation reported errors: those strings are left out and stay English in game)')
    run('build_pack.py')
    run('build_mod.py')


if __name__ == '__main__':
    main()
