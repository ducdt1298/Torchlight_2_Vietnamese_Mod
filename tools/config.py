# -*- coding: utf-8 -*-
"""Paths used by the tools. The game folder is only ever READ by the build tools."""
import os

GAME_DIR = os.environ.get('TL2_GAME_DIR', r'D:\SteamLibrary\steamapps\common\Torchlight II')
PAK = os.path.join(GAME_DIR, 'PAKS', 'DATA.PAK')
MAN = os.path.join(GAME_DIR, 'PAKS', 'DATA.PAK.MAN')
EXE = os.path.join(GAME_DIR, 'Torchlight2.exe')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(ROOT, 'work')            # intermediate data (regenerable)
TRANSLATION = os.path.join(ROOT, 'translation')
FONTS = os.path.join(ROOT, 'fonts')
BUILD = os.path.join(ROOT, 'build')          # language pack files as they go into the PAK
OUTPUT = os.path.join(ROOT, 'output')        # patch ready to install

LANG_NAME = 'VIETNAMESE'
LANG_DISPLAY = 'Tiếng Việt'
# The game only accepts the IDs of the official languages (1-6); ID 7 made the game crash at start
# (CEGUI: font 'Serif' does not exist). 1 shares German's ID, as the old community mod did.
LANG_ID = int(os.environ.get('TL2VI_LANG_ID', 1))
PACK_DIR = 'MEDIA/TRANSLATIONS/VIETNAMESE/'

for d in (WORK, BUILD, OUTPUT):
    os.makedirs(d, exist_ok=True)
