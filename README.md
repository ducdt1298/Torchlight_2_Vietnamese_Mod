# Torchlight II — Vietnamese Translation (mixed English–Vietnamese)

A **from-scratch** Vietnamese translation for Torchlight II **v1.26.0.1** (Steam), built on the game's own
multi-language system. Nothing is reused from the old community "VN-MOD": that mod overrides almost 7,000 game data
files with copies from 2016, which removes content from the current game.

## Translation style

- **Translated to Vietnamese**: dialogue, quests, skill/item/effect descriptions, UI, tutorials, tips.
- **Kept in English**: names of skills, items, monsters, bosses, NPCs, pets, places, quests, item sets, character
  classes, the 4 base attributes (Strength/Dexterity/Focus/Vitality), damage types
  (Physical/Fire/Ice/Electric/Poison), rarities, item types and chat commands.
  In-game names therefore match the international forums and other players.

Examples: `+25% Fire Damage` → `+25% sát thương Fire`; `Requires Level 30` → `Yêu cầu cấp 30`.

Full rules and glossary (in Vietnamese, for translators): [translation/STYLE_GUIDE.md](translation/STYLE_GUIDE.md).

### Build statistics (game v1.26.0.1)

| | Strings |
|---|---|
| All text strings in the game | 13,898 |
| Proper names automatically kept in English (items, monsters, skills, places, quests…) | 6,723 |
| Sent to translation (~78,700 English words) | 7,175 |
| → translated to Vietnamese and included in the table | **6,786** |
| → kept in English by the translator (proper names, terms, debug strings) | 389 |
| Rejected because of formatting errors | 0 |

## How it works — the `VIETHOA_ENVI.MOD` file

The translation is a **mod** (`output\mod\VIETHOA_ENVI.MOD`, about 2.3 MB). **No game file is modified.** The mod
contains only:

```
MEDIA/TRANSLATIONS/VIETNAMESE.DAT                    the "Tiếng Việt" language (Options > Language), ID 1
MEDIA/TRANSLATIONS/VIETNAMESE/TRANSLATION.DAT        English -> Vietnamese table
MEDIA/UI/*.TTF (except ARIAL.TTF)                    replaced by the game's Arial -> all text shows full diacritics
```

- The mod has no gameplay data (items, monsters, quests, UI layouts…), so it cannot remove content like the old VN-MOD.
- While the mod is enabled, every UI font is Arial, even when the language is set to English.
- When playing with mods the game uses a separate save folder, `modsave\` (characters in `save\` do not show up in mod
  mode).

The earlier approach — appending the language pack to `DATA.PAK` — made game v1.26 crash at startup and was abandoned.
Its scripts are kept in `legacy_pak_method\` for reference only.

## Installation

The built mod is not stored in this repository (see [Building](#building)). Once `output\mod\VIETHOA_ENVI.MOD` exists:

1. Close Torchlight II and ModLauncher.
2. Run **`install_mod.bat`**. It copies the mod to `Documents\My Games\Runic Games\Torchlight 2\mods\` and selects it
   in ModLauncher. The previous selection is backed up as `modlauncher.sch.vi-backup`.
3. Start the game. In the launcher window click **"Play with mods"** (the lower button).
4. Go to **Options → Language → Tiếng Việt**, quit the game, then start it again with **"Play with mods"**.

## Uninstallation

Run **`uninstall_mod.bat`**: it deletes `VIETHOA_ENVI.MOD` from the mods folder and restores the previous mod
selection. Alternatively, just click "Play" (without mods) in the launcher.

## Building

Requirements: Python 3 and an installed copy of Torchlight II. The build only **reads** the game folder and never
writes to it. If the game is not at `D:\SteamLibrary\steamapps\common\Torchlight II`, set the `TL2_GAME_DIR`
environment variable to its folder.

```
python tools\build_all.py           # extract strings (first run), validate, build the pack and the mod
install_mod.bat
```

The first run extracts the game's strings into `work\` (intermediate data, not versioned). The output is
`output\mod\VIETHOA_ENVI.MOD`. The mod's GUID is kept in `output\mod\mod_info.json`; keep that file so that rebuilt
mods keep the same GUID (characters remember the mods they were played with).

`fontTools` is only needed by `tools\build_fonts.py`, which belongs to the abandoned custom-font build.

## After a game update

The mod does not depend on `DATA.PAK`, so it usually keeps working after an update. If the game adds new strings:

```
python tools\update_strings.py      # create a new translation batch in translation\batches\
python tools\build_all.py           # rebuild the mod
install_mod.bat
```

Never regenerate the existing batches (`tools\make_batches.py`): their ids link the translations to the English text.

## Editing or adding translations

- Translations live in `translation\vi\<batch>.partNN.txt`. Each entry has 2 lines: `@@ <id>` and the Vietnamese
  text. The matching English text is in `translation\batches\<batch>.txt`. To fix entries, add a file such as
  `translation\vi\<batch>.partfixNN.txt` (files that sort later override earlier ones) or edit the text in place.
- Every translation with its context, for review: `translation\REVIEW_vi.tsv` (opens in Excel).
- After editing:
  ```
  python tools\validate_translations.py   # check [VALUE] tokens, |c..|u color codes, \n ...
  python tools\review_names.py            # check that proper names stayed English
  python tools\build_all.py               # rebuild the mod and run the checks
  install_mod.bat                         # install the new build (overwrites the old one)
  ```
  A string with broken tokens is automatically left out of the build (the game shows English for it), so it can
  never break the game.

## Repository layout

| Path | Contents |
|---|---|
| `install_mod.bat`, `uninstall_mod.bat` | install / uninstall the mod (`.ps1` scripts do the work) |
| `translation\` | style guide, translation batches (`batches\`), translations (`vi\`), review file |
| `tools\` | Python tools: string extraction, classification, pack/mod build, validation |
| `tools\tl2lib.py` | readers/writers for the game's PAK, PAK.MAN and binary DAT formats |
| `output\mod\` | built mod (`VIETHOA_ENVI.MOD`, not versioned) and `mod_info.json` |
| `fonts\src\` | open-source fonts and their licenses, used only by the abandoned custom-font build |
| `legacy_pak_method\` | abandoned DATA.PAK install scripts (reference only) |
| `build\`, `work\` | generated files (not versioned) |

## Fonts

The game's own fonts (except Arial) have no Vietnamese glyphs. While the mod is enabled, **every UI font is the
game's own Arial**, which covers all Vietnamese diacritics. The old VN mod did the same, and the official German pack
also uses Arial for its Serif fonts.

The first build used a separate font for each style (Bitter/Alegreya/Bangers/Noto, see `tools\build_fonts.py` and
`fonts\`) with language ID 7 and a hand-made UI folder. The game crashed at startup
(CEGUI: font 'Serif' does not exist), so that approach was replaced by the one above.

## Notes

- The mod has **not yet been verified in game**. All checks were done offline: PAK/MAN/MOD formats, hashes, CRCs,
  tokens and the install/uninstall scripts. If something goes wrong, run `uninstall_mod.bat`.
- Multiplayer: the mod only adds language files and fonts; gameplay data is unchanged. In theory you can play with
  people who do not have it, but this has not been tested.
- Voice-over stays English. Some strings hard-coded in the exe may still show in English. Long sentences may overflow
  their box in a few places.

## License and credits

Torchlight II and its game data belong to their respective owners. This repository contains only the translation,
the tools and the scripts; the build reads the game data from your own copy of the game. The fonts in `fonts\src\` are under
the SIL Open Font License, except Roboto Slab (Apache License 2.0); each license file sits next to its font.
