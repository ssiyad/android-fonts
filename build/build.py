"""Build the fonts of the module from build/cache/src.

Usage: build.py SRC_DIR OUT_DIR WORK_DIR

Geist-VF.ttf     Geist (upright and italic) with Roboto glyphs for the characters
                 that Geist does not have. Axes: wght 100-900 (outlines), ital 0-1
                 and slnt -10-0 (both switch to the italic glyphs with GSUB rvrn).
Geist-<w>.ttf    Static instances of the same, for static font slots.
GeistMono-400.ttf Geist Mono Nerd Font, with Droid Sans Mono glyphs for the missing
                 characters.
Manjari-VF.ttf   Manjari Thin, Regular and Bold in one font. The wght axis switches
                 between them with GSUB rvrn, because the three masters do not
                 interpolate.
Manjari-<w>.ttf  The static Manjari fonts.
"""

import shutil
import sys
from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, RuleDescriptor, SourceDescriptor
from fontTools.fontBuilder import FontBuilder
from fontTools.ttLib import TTFont
from fontTools.varLib import build as build_variable_font
from fontTools.varLib.featureVars import addFeatureVariations

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run with python -I
from fontparts import Workdir, hide, instance, keep_glyph_names, merge, renamed, strip, to_truetype, unicodes

WEIGHTS = range(100, 1000, 100)
STATIC_WEIGHTS = (100, 200, 300, 400, 500, 600, 700, 800, 900)
UPEM = 1000
# C0 and C1 controls: never take them from the fallback font.
CONTROLS = set(range(0x20)) | set(range(0x7F, 0xA0))


def main(src: Path, out: Path, work: Path):
    out.mkdir(parents=True, exist_ok=True)
    workdir = Workdir(work)
    geist = GeistBuilder(src, workdir)
    geist.build_variable(out / "Geist-VF.ttf")
    for weight in STATIC_WEIGHTS:
        geist.build_static(weight, False, out / f"Geist-{weight}.ttf")
        geist.build_static(weight, True, out / f"Geist-{weight}-Italic.ttf")
    MonoBuilder(src, workdir).build(out / "GeistMono-400.ttf")
    ManjariBuilder(src, workdir).build(out)


class GeistBuilder:
    """Geist with Roboto as the glyph fallback, upright and italic."""

    def __init__(self, src: Path, work: Workdir):
        self.upright = src / "Geist[wght].ttf"
        self.italic = src / "Geist-Italic[wght].ttf"
        self.roboto = src / "Roboto-Regular.ttf"
        self.work = work
        self.fallback = self._fallback_unicodes()

    def build_variable(self, out: Path):
        doc = DesignSpaceDocument()
        doc.addAxis(_axis("wght", "Weight", 100, 400, 900))
        doc.addAxis(_axis("ital", "Italic", 0, 0, 1))
        doc.addAxis(_axis("slnt", "Slant", -10, 0, 0))
        masters = {weight: self._master(weight) for weight in WEIGHTS}
        for weight, path in masters.items():
            source = SourceDescriptor()
            source.path = str(path)
            source.location = {"Weight": weight, "Italic": 0, "Slant": 0}
            doc.addSource(source)
        doc.addRule(self._italic_rule(TTFont(masters[400]).getGlyphOrder()))
        doc.rulesProcessingLast = False
        font, _, _ = build_variable_font(doc)
        keep_glyph_names(font)
        font.save(out)

    def build_static(self, weight: int, italic: bool, out: Path):
        geist, roboto = self._parts(weight, italic)
        merge([geist, roboto]).save(out)

    def _master(self, weight: int) -> Path:
        """Upright and italic glyphs of one weight. Italic glyph names get a prefix."""
        geist, roboto = self._parts(weight, False)
        geist_italic, roboto_italic = self._parts(weight, True, hidden=True)
        parts = [
            geist,
            renamed(geist_italic, "it.", self.work.root / f"geist-{weight}-it-renamed.ttf"),
            renamed(roboto, "rb.", self.work.root / f"roboto-{weight}-renamed.ttf"),
            renamed(roboto_italic, "rbi.", self.work.root / f"roboto-{weight}-it-renamed.ttf"),
        ]
        return self.work.save(merge(parts), f"master-{weight}.ttf")

    def _parts(self, weight: int, italic: bool, hidden=False) -> tuple:
        style = "it" if italic else "up"
        suffix = "-hidden" if hidden else ""
        geist = strip(instance(self.italic if italic else self.upright, {"wght": weight}))
        roboto = instance(self.roboto, {"wght": weight, "wdth": 100, "ital": int(italic)})
        roboto = strip(roboto, keep=self.fallback, upem=UPEM)
        if hidden:
            hide(geist)
            hide(roboto)
        return (
            self.work.save(geist, f"geist-{weight}-{style}{suffix}.ttf"),
            self.work.save(roboto, f"roboto-{weight}-{style}{suffix}.ttf"),
        )

    def _italic_rule(self, glyph_order: list) -> RuleDescriptor:
        """ital >= 0.5 or slnt <= -5 selects the italic glyphs."""
        names = set(glyph_order)
        rule = RuleDescriptor()
        rule.name = "italic"
        rule.conditionSets = [
            [{"name": "Italic", "minimum": 0.5, "maximum": 1}],
            [{"name": "Slant", "minimum": -10, "maximum": -5}],
        ]
        for name in glyph_order:
            if name.startswith(("it.", "rbi.")):
                continue
            target = "rbi." + name[3:] if name.startswith("rb.") else "it." + name
            if target in names:
                rule.subs.append((name, target))
        return rule

    def _fallback_unicodes(self) -> set:
        roboto = unicodes(TTFont(self.roboto))
        geist = unicodes(TTFont(self.upright))
        return roboto - geist - CONTROLS


class MonoBuilder:
    """Geist Mono Nerd Font, with Droid Sans Mono as the glyph fallback."""

    def __init__(self, src: Path, work: Workdir):
        self.nerd = src / "GeistMonoNerdFont-Regular.otf"
        self.droid = src / "DroidSansMono.ttf"
        self.work = work

    def build(self, out: Path):
        nerd = strip(to_truetype(TTFont(self.nerd)))
        missing = unicodes(TTFont(self.droid)) - unicodes(nerd) - CONTROLS
        droid = strip(TTFont(self.droid), keep=missing, upem=UPEM)
        parts = [self.work.save(nerd, "mono-nerd.ttf"), self.work.save(droid, "mono-droid.ttf")]
        merge(parts).save(out)


class ManjariBuilder:
    """Manjari, with a wght axis that switches between Thin, Regular and Bold.

    The switch is in rclt, as the last GSUB lookup. HarfBuzz's Indic shaper finds
    the virama glyph through the cmap, so all shaping must run on the Regular
    glyphs. The Thin and Bold GSUB tables are dropped; their GPOS stays.
    """

    # Weight ranges for each master. Android asks for 500 often (medium), so
    # Regular covers it; 600 and up is Bold.
    THIN_MAX = 250
    BOLD_MIN = 550

    def __init__(self, src: Path, work: Workdir):
        self.src = src
        self.work = work

    def build(self, out: Path):
        for name, weight in (("Thin", 100), ("Regular", 400), ("Bold", 700)):
            shutil.copy(self.src / f"Manjari-{name}.ttf", out / f"Manjari-{weight}.ttf")
        self.build_variable(out / "Manjari-VF.ttf")

    def build_variable(self, out: Path):
        regular = self.work.save(strip(TTFont(self.src / "Manjari-Regular.ttf")), "manjari-400.ttf")
        thin = self._hidden("Thin", "th.")
        bold = self._hidden("Bold", "bd.")
        font = merge([regular, thin, bold])
        order = set(font.getGlyphOrder())
        base = [n for n in font.getGlyphOrder() if not n.startswith(("th.", "bd."))]
        builder = FontBuilder(font=font)
        builder.setupFvar([("wght", 100, 400, 700, "Weight")], [])
        builder.setupGvar({})
        addFeatureVariations(
            font,
            [
                ([{"wght": (-1.0, _normalize(self.THIN_MAX, 100, 400, 700))}], _map(base, "th.", order)),
                ([{"wght": (_normalize(self.BOLD_MIN, 100, 400, 700), 1.0)}], _map(base, "bd.", order)),
            ],
            featureTag="rclt",
        )
        font.save(out)

    def _hidden(self, name: str, prefix: str) -> Path:
        font = hide(strip(TTFont(self.src / f"Manjari-{name}.ttf")))
        del font["GSUB"]
        path = self.work.save(font, f"manjari-{name}-hidden.ttf")
        return renamed(path, prefix, self.work.root / f"manjari-{name}-renamed.ttf")


def _axis(tag: str, name: str, minimum: float, default: float, maximum: float) -> AxisDescriptor:
    axis = AxisDescriptor()
    axis.tag, axis.name = tag, name
    axis.minimum, axis.default, axis.maximum = minimum, default, maximum
    return axis


def _map(base: list, prefix: str, order: set) -> dict:
    return {name: prefix + name for name in base if prefix + name in order}


def _normalize(value: float, minimum: float, default: float, maximum: float) -> float:
    if value < default:
        return (value - default) / (default - minimum)
    return (value - default) / (maximum - default)


if __name__ == "__main__":
    main(*(Path(arg) for arg in sys.argv[1:4]))
