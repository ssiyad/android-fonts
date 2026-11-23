# pyright: reportAttributeAccessIssue=false, reportArgumentType=false, reportIndexIssue=false
# fontTools tables are dynamic; pyright cannot see their attributes.
"""Font operations that the build composes: instance, subset, rename, merge."""

from pathlib import Path

from fontTools.merge import Merger
from fontTools.pens.cu2quPen import Cu2QuPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.subset import Options, Subsetter
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.varLib import instancer

# Tables that cannot be merged, or that have no use in a static part.
DROP_TABLES = ["DSIG", "STAT", "meta", "kern", "gasp", "hdmx", "LTSH", "VDMX", "MVAR", "HVAR", "VORG"]


class Workdir:
    """Keeps the intermediate files of a build, so that a failed step is easy to inspect."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def save(self, font: TTFont, name: str) -> Path:
        path = self.root / name
        font.save(path)
        return path


def instance(path: Path, location: dict) -> TTFont:
    """Return a static instance of a variable font."""
    return instancer.instantiateVariableFont(TTFont(path), location)


def strip(font: TTFont, keep=None, upem=None) -> TTFont:
    """Remove hinting and unmergeable tables. With keep, keep only those characters."""
    options = Options()
    options.hinting = False
    options.glyph_names = True
    options.notdef_outline = True
    options.layout_features = ["*"]
    options.name_IDs = ["*"]
    options.name_languages = ["*"]
    options.name_legacy = True
    options.drop_tables += DROP_TABLES
    subsetter = Subsetter(options)
    if keep is None:
        subsetter.populate(glyphs=font.getGlyphOrder(), unicodes=unicodes(font))
    else:
        subsetter.populate(unicodes=keep)
    subsetter.subset(font)
    if upem and font["head"].unitsPerEm != upem:
        scale_upem(font, upem)
    # Fonts without stored names get them from the cmap, which hide() empties.
    keep_glyph_names(font)
    return font


def enlarge(font: TTFont, factor: float):
    """Scale outlines, metrics and positioning by factor, and keep the UPEM."""
    upem = font["head"].unitsPerEm
    scale_upem(font, round(upem * factor))
    font["head"].unitsPerEm = upem


def unicodes(font: TTFont) -> set:
    return set(font.getBestCmap() or {})


def hide(font: TTFont) -> TTFont:
    """Remove all characters from the cmap. The glyphs stay, for substitutions only."""
    for table in font["cmap"].tables:
        table.cmap = {}
    return font


def add_composite(font: TTFont, name: str, run: list):
    """Add a glyph made of the glyphs of a shaped run: (name, advance, x offset, y offset)."""
    pen = TTGlyphPen(font["glyf"])
    x = 0
    for glyph, advance, dx, dy in run:
        pen.addComponent(glyph, (1, 0, 0, 1, x + dx, dy))
        x += advance
    order = font.getGlyphOrder() + [name]
    font.setGlyphOrder(order)
    glyf = font["glyf"]
    glyf.glyphOrder = order
    glyf[name] = pen.glyph()
    glyf[name].recalcBounds(glyf)
    font["hmtx"][name] = (x, getattr(glyf[name], "xMin", 0))


def renamed(path: Path, prefix: str, out: Path) -> Path:
    """Save a copy of the font with every glyph name prefixed.

    Glyph references are glyph IDs in the binary, so a new glyph order applied
    before the tables are read renames all of them. fontTools.merge does the same.
    """
    order = TTFont(path).getGlyphOrder()
    font = TTFont(path)
    font.setGlyphOrder([prefix + name for name in order])
    # A table that was never read is saved as raw bytes; post holds the names.
    keep_glyph_names(font)
    font.save(out)
    return out


def merge(paths: list) -> TTFont:
    """Merge fonts. The first font wins for names, metrics and duplicate characters."""
    font = Merger().merge([str(p) for p in paths])
    keep_glyph_names(font)
    return font


def keep_glyph_names(font: TTFont):
    """Store glyph names. Later steps find glyphs by name, and the merger drops them."""
    _truetype_post(font["post"])


def to_truetype(font: TTFont) -> TTFont:
    """Convert CFF outlines to TrueType, so the font can merge with TrueType fonts."""
    order = font.getGlyphOrder()
    glyphset = font.getGlyphSet()
    glyf = newTable("glyf")
    glyf.glyphOrder = order
    glyf.glyphs = {}
    for name in order:
        pen = TTGlyphPen(None)
        glyphset[name].draw(Cu2QuPen(pen, max_err=1.0, reverse_direction=True))
        glyf[name] = pen.glyph()
    font["glyf"] = glyf
    font["loca"] = newTable("loca")
    del font["CFF "]
    font["head"].glyphDataFormat = 0
    _truetype_maxp(font["maxp"])
    _truetype_post(font["post"])
    _fix_lsb(font, glyf)
    font.sfntVersion = "\x00\x01\x00\x00"
    return font


def _truetype_maxp(maxp):
    maxp.tableVersion = 0x00010000
    maxp.maxZones = 1
    for field in (
        "maxTwilightPoints",
        "maxStorage",
        "maxFunctionDefs",
        "maxInstructionDefs",
        "maxStackElements",
        "maxSizeOfInstructions",
        "maxComponentElements",
        "maxComponentDepth",
    ):
        setattr(maxp, field, 0)


def _truetype_post(post):
    post.formatType = 2.0
    post.extraNames = []
    post.mapping = {}


def _fix_lsb(font: TTFont, glyf):
    hmtx = font["hmtx"]
    for name, (advance, _) in hmtx.metrics.items():
        glyph = glyf[name]
        glyph.recalcBounds(glyf)
        hmtx[name] = (advance, getattr(glyph, "xMin", 0))
