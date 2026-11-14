"""Make the list of font files to replace, from the font XMLs of a ROM.

Usage: slots.py ROM_OUT_DIR > module/fonts.list

Each line is "<target path> <module font>". A font file gets:
  - Manjari, if a Malayalam family uses it.
  - Geist Mono, if a monospace family uses it.
  - Geist, if a named family (sans-serif, serif, google-sans, ...) uses it.
Fonts of the other scripts stay: Geist does not have their characters.
A variable font gets the variable replacement; a static font gets the static
instance with the weight and style that its XML entry declares.
"""

import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from fontTools.ttLib import TTFont

XMLS = {
    "system/etc/font_fallback.xml": "/system/fonts",
    "system/etc/fonts.xml": "/system/fonts",
    "product/etc/fonts_customization.xml": "/product/fonts",
}
MONO_FAMILIES = {"monospace", "serif-monospace"}
# Files that no XML uses. Apps can still open them by path.
UNREFERENCED = {
    "/system/fonts/DroidSans.ttf": "Geist-400.ttf",
    "/system/fonts/DroidSans-Bold.ttf": "Geist-700.ttf",
    "/system/fonts/RobotoStatic-Regular.ttf": "Geist-400.ttf",
    "/system/fonts/AndroidClock.ttf": "Geist-400.ttf",
}


@dataclass(frozen=True)
class Slot:
    path: str
    kind: str  # geist, mono, manjari or keep
    weight: int
    italic: bool


def main(rom: Path):
    slots = [slot for xml, fontdir in XMLS.items() for slot in read_slots(rom / xml, fontdir)]
    choices = dict(UNREFERENCED)
    for path in sorted({s.path for s in slots}):
        choice = choose(rom, [s for s in slots if s.path == path])
        if choice:
            choices[path] = choice
    for path, font in sorted(choices.items()):
        print(path, font)


def read_slots(xml: Path, fontdir: str):
    for family in ET.parse(xml).getroot().iter("family"):
        kind = family_kind(family)
        for font in family.iter("font"):
            yield Slot(
                path=f"{fontdir}/{(font.text or '').strip()}",
                kind=kind,
                weight=int(font.get("weight", 400)),
                italic=font.get("style") == "italic",
            )


def family_kind(family: ET.Element) -> str:
    name, lang = family.get("name"), family.get("lang") or ""
    if "Mlym" in lang:
        return "manjari"
    if name in MONO_FAMILIES:
        return "mono"
    if name:
        return "geist"
    return "keep"


def choose(rom: Path, slots: list) -> str | None:
    kinds = {s.kind for s in slots} - {"keep"}
    if not kinds:
        return None
    if len(kinds) > 1 or any(s.kind == "keep" for s in slots):
        sys.exit(f"{slots[0].path}: used by families of different kinds: {sorted({s.kind for s in slots})}")
    kind = kinds.pop()
    if kind == "mono":
        return "GeistMono-400.ttf"
    if is_variable(rom, slots[0].path):
        return "Geist-VF.ttf" if kind == "geist" else "Manjari-VF.ttf"
    styles = {(s.weight, s.italic) for s in slots}
    if len(styles) > 1:
        sys.exit(f"{slots[0].path}: static font with more than one style: {sorted(styles)}")
    weight, italic = styles.pop()
    if kind == "manjari":
        return f"Manjari-{min((100, 400, 700), key=lambda w: abs(w - weight))}.ttf"
    return f"Geist-{weight}{'-Italic' if italic else ''}.ttf"


def is_variable(rom: Path, path: str) -> bool:
    return "fvar" in TTFont(rom / path.lstrip("/"), lazy=True)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
