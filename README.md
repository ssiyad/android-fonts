# Geist Fonts

A KernelSU module for the Nothing Phone (4a) on LineageOS 23.2. It replaces the
system fonts:

| Fonts | Replacement |
| --- | --- |
| Named Latin families: sans-serif, serif, Google Sans, cursive, casual, ... | Geist |
| Malayalam (`und-Mlym`) | Manjari |
| monospace, serif-monospace | Geist Mono Nerd Font |

Fonts of the other scripts (CJK, Devanagari, emoji, ...) stay, because Geist
does not have their characters.

## How it works

- `post-fs-data.sh` bind-mounts each font in `fonts/` over a system font. The
  font XMLs do not change. `fonts.list` gives the pairs.
- `build/slots.py` makes `fonts.list` from the font XMLs of the ROM. A variable
  slot gets a variable font. A static slot gets the static instance with the
  weight and style that the XML declares.
- If a boot does not complete, the next boot mounts nothing and the module
  disables itself. `service.sh` clears the guard after the boot completes.

## The fonts

- `Geist-VF.ttf`: Geist upright and italic in one font, with Roboto glyphs for
  the characters that Geist does not have (Greek, most Cyrillic, IPA, ...).
  Android sets `ital` for the Roboto slot and `slnt` for Google Sans italics;
  both switch to the italic glyphs.
- `GeistMono-400.ttf`: Geist Mono Nerd Font, with Droid Sans Mono glyphs for
  the missing characters.
- `Manjari-VF.ttf`: Manjari Thin, Regular and Bold in one font. The masters do
  not interpolate, so the `wght` axis selects one of them: below 250 Thin, from
  550 Bold. The switch is the last GSUB lookup (`rclt`), because HarfBuzz's
  Indic shaper must shape the Regular glyphs.

## Build

Needs `uv`, `curl`, `unzip` and a built LineageOS tree (`LINEAGE`, default
`~/android/lineage`).

```sh
./build.sh
```

This writes `../zips/geist-fonts-<version>.zip`. `build/verify.py` shapes test
text with HarfBuzz and compares each built font with its source font.

## Licenses

Geist, Manjari and Geist Mono Nerd Font use the SIL Open Font License 1.1.
Roboto and Droid Sans Mono use the Apache License 2.0. See `licenses/` in the
zip.
