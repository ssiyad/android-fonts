# Geist Fonts

A KernelSU module for the Nothing Phone (4a) on LineageOS 23.2. It replaces the
system fonts:

| Fonts | Replacement |
| --- | --- |
| Named Latin families: sans-serif, serif, Google Sans, cursive, casual, ... | Geist |
| Malayalam (`und-Mlym`) | Manjari 2.200 from [SMC](https://smc.org.in/fonts/manjari) |
| monospace, serif-monospace | Geist Mono Nerd Font |

Fonts of the other scripts (CJK, Devanagari, emoji, ...) stay, because Geist
does not have their characters.

## Install

1. Download `geist-fonts-<version>.zip` from the
   [releases](https://github.com/ssiyad/android-fonts/releases).
2. Disable other font modules.
3. Install the zip in the KernelSU manager and reboot.

Apps that unmount modules do not get the fonts. In the KernelSU manager, turn
off "Umount modules by default" in Settings, and turn on "Umount modules" only
in the App Profile of apps that must not see root (banking apps, for example).
Then force-stop the apps that are open. If an app unmounts modules, it shows
only the fonts that zygote opened before the unmount (for example Geist for
sans-serif), and the original fonts for the rest (for example Malayalam).

`fonts.list` names the font files of LineageOS 23.2 on the Nothing Phone (4a).
On another ROM, the module only replaces the files that exist; to cover all
fonts, build the module with that ROM (see Build). The log is
`/data/local/tmp/geist-fonts.log`.

## How it works

- `post-fs-data.sh` bind-mounts each font in `fonts/` over a system font. The
  font XMLs do not change. `fonts.list` gives the pairs.
- `build/slots.py` makes `fonts.list` from the font XMLs of the ROM. A variable
  slot gets a variable font. A static slot gets the static instance with the
  weight and style that the XML declares.
- If a boot does not complete, the next boot mounts nothing and the module
  disables itself. `service.sh` clears the guard after the boot completes. A
  reboot during boot (or KernelSU safe mode) also counts as a failed boot. To
  use the module again, enable it in the KernelSU manager.
- Symlinks (`DroidSans*.ttf` point to `Roboto-Regular.ttf`) are skipped: the
  mount on the target covers them.

## The fonts

- `Geist-VF.ttf`: Geist upright and italic in one font, with Roboto glyphs for
  the characters that Geist does not have (Greek, most Cyrillic, IPA, ...).
  Android sets `ital` for the Roboto slot and `slnt` for Google Sans italics;
  both switch to the italic glyphs.
- `GeistMono-400.ttf`: Geist Mono Nerd Font, with Droid Sans Mono glyphs for
  the missing characters.
- `Manjari-VF.ttf`: Manjari Thin, Regular and Bold in one font, 1.13 times
  the size of the original. Then the Malayalam letters have the same size next
  to Geist as Noto Sans Malayalam next to Roboto. The masters do
  not interpolate, so the `wght` axis selects one of them: 250 and below Thin,
  550 and above Bold. The switch is the last GSUB lookup (`rclt`), because
  HarfBuzz's Indic shaper must shape the Regular glyphs. Six Regular conjuncts
  that Bold does not have become composites of the glyphs that Bold shapes for
  the same text. Where Bold has a conjunct glyph that its own GSUB does not
  use (for example `y1k1` in യ്ക), the Bold conjunct shows.

## Known limits

- Geist has no `wdth` axis, so `sans-serif-condensed` and Roboto Flex widths
  render at normal width. Condensed text can need more space.
- Characters that the replacements do not have fall back to other system fonts:
  Manjari lacks U+0951, U+0952, U+0964 and U+0965 (Vedic and Devanagari
  dandas) and a few combining marks. Geist-VF lacks the private-use glyphs of
  Google Sans and Roboto Flex.
- `AndroidClock.ttf` becomes Geist, which has proportional digits.

## Build

Needs `uv`, `curl` and `unzip`.

```sh
./build.sh
```

This writes `../zips/geist-fonts-<version>.zip` (set `OUT` for another
directory). `build/verify.py` shapes test text with HarfBuzz and compares each
built font with its source font. If a built LineageOS tree is at `LINEAGE`
(default `~/android/lineage`), `build/slots.py` makes `fonts.list` again from
the font XMLs of the ROM.

## Release

Set `version` and `versionCode` in `module/module.prop`, commit, and push a tag
with the same version, for example `v2`. The `Release` workflow builds the zip
and publishes it with its SHA-256 as a GitHub release.

## Licenses

Geist, Manjari and Geist Mono Nerd Font use the SIL Open Font License 1.1.
Roboto and Droid Sans Mono use the Apache License 2.0. See `licenses/` in the
zip.
