"""Malayalam test strings, and HarfBuzz shaping of them."""

# pyright: reportAttributeAccessIssue=false
# uharfbuzz is a compiled module without type stubs.

from itertools import product
from pathlib import Path

import uharfbuzz as hb

CONSONANTS = [chr(c) for c in range(0x0D15, 0x0D3A)]
VOWEL_SIGNS = ["", "ാ", "ി", "ീ", "ു", "ൂ", "ൃ", "െ", "േ", "ൈ"]
VIRAMA = "്"

# Manjari is drawn smaller than Geist. Noto Sans Malayalam is 1.064 times as tall
# as the Roboto x-height; at 1.13, Manjari keeps that ratio to the Geist x-height.
SCALE = 1.13


def syllables():
    """Yield consonant clusters of one, two and three consonants, with a vowel sign."""
    for c, v in product(CONSONANTS, VOWEL_SIGNS):
        yield c + v
    for a, b, v in product(CONSONANTS, CONSONANTS, VOWEL_SIGNS):
        yield a + VIRAMA + b + v
    for a, b, c, v in product(CONSONANTS, CONSONANTS, CONSONANTS, ("", "ു")):
        yield a + VIRAMA + b + VIRAMA + c + v


class Shaper:
    """Shapes text with one font, at one location."""

    def __init__(self, path: Path, axes: dict | None = None):
        self.font = hb.Font(hb.Face(path.read_bytes()))
        if axes:
            self.font.set_variations(axes)

    def glyphs(self, text: str) -> list:
        """Return (glyph name, x advance, x offset, y offset) for each glyph."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf)
        return [
            (self.font.glyph_to_string(i.codepoint), p.x_advance, p.x_offset, p.y_offset)
            for i, p in zip(buf.glyph_infos, buf.glyph_positions)
        ]


def decompositions(regular: Path, master: Path, names: set) -> dict:
    """For each glyph name of Regular, the glyphs that master shapes for the same text.

    Only glyphs that Regular makes from a whole syllable are found.
    """
    regular_shaper, master_shaper = Shaper(regular), Shaper(master)
    found = {}
    for text in syllables():
        run = regular_shaper.glyphs(text)
        if len(run) == 1 and run[0][0] in names and run[0][0] not in found:
            found[run[0][0]] = master_shaper.glyphs(text)
            if len(found) == len(names):
                break
    return found
