# pyright: reportAttributeAccessIssue=false
# uharfbuzz is a compiled module without type stubs.
"""Check the built fonts: OpenType Sanitizer, coverage, and HarfBuzz shaping.

Usage: verify.py SRC_DIR OUT_DIR

Shaping a sample in a built font must give the same glyphs and advances as
shaping it in the font it came from, at each weight and style.
"""

import sys
from pathlib import Path

import ots
import uharfbuzz as hb
from fontTools.ttLib import TTFont

sys.path.insert(0, str(Path(__file__).resolve().parent))  # run with python -I
from malayalam import SCALE, Shaper, syllables

LATIN = "Hamburgefonstiv 0123 fi ‘quotes’ — €"
FALLBACK = "Ελληνικά Ґґ ǅ ɐ ẞ ₹"
MALAYALAM = "മലയാളം ക്ഷേത്രം സ്ത്രീ കാർത്തിക"
MONO = "fn main() { -> != } Ελληνικά Ґґ ẞ ₹"


def main(src: Path, out: Path):
    checks = Checks(src, out)
    checks.sanitize()
    checks.geist_variable()
    checks.geist_static()
    checks.mono()
    checks.manjari()
    checks.manjari_weights()
    if checks.failures:
        print("\n".join(checks.failures))
        sys.exit(1)
    print(f"verify: {checks.count} checks passed")


class Checks:
    def __init__(self, src: Path, out: Path):
        self.src, self.out = src, out
        self.failures, self.count = [], 0

    def sanitize(self):
        for path in sorted(self.out.glob("*.ttf")):
            result = ots.sanitize(str(path), "/dev/null", capture_output=True)
            stderr = (result.stderr or b"").decode(errors="replace").strip()
            self.expect(result.returncode == 0, f"OTS rejects {path.name}: {stderr}")

    def geist_variable(self):
        vf = self.out / "Geist-VF.ttf"
        roboto = set(TTFont(self.src / "Roboto-Regular.ttf").getBestCmap() or {})
        covered = set(TTFont(vf).getBestCmap() or {})
        missing = {c for c in roboto - covered if c >= 0x20 and not 0x7F <= c < 0xA0}
        self.expect(not missing, f"Geist-VF misses {len(missing)} Roboto characters")
        for weight in (100, 400, 700, 900):
            for italic, axes in ((False, {}), (True, {"ital": 1}), (True, {"slnt": -10})):
                ref = self.src / ("Geist-Italic[wght].ttf" if italic else "Geist[wght].ttf")
                prefix = "it." if italic else ""
                self.same(vf, {"wght": weight, **axes}, ref, {"wght": weight}, LATIN, prefix)
        # Upright text must have no italic glyphs; italic text only italic glyphs.
        names = [n for n, _ in shape(vf, {"wght": 400}, FALLBACK)]
        upright = all(n != ".notdef" and not n.startswith(("it.", "rbi.")) for n in names)
        self.expect(upright, f"fallback glyphs: {names}")
        names = [n for n, _ in shape(vf, {"wght": 400, "ital": 1}, FALLBACK)]
        self.expect(all(n.startswith(("it.", "rbi.")) for n in names), f"italic fallback: {names}")

    def geist_static(self):
        for weight in (400, 700):
            self.same(
                self.out / f"Geist-{weight}.ttf", {}, self.src / "Geist[wght].ttf", {"wght": weight}, LATIN
            )
            self.same(
                self.out / f"Geist-{weight}-Italic.ttf",
                {},
                self.src / "Geist-Italic[wght].ttf",
                {"wght": weight},
                LATIN,
            )

    def mono(self):
        font = self.out / "GeistMono-400.ttf"
        text = MONO + "\ue0b0\uf120"
        advances = {a for n, a in shape(font, {}, text) if n not in ("uni200B",)}
        self.expect(advances == {600}, f"GeistMono advances are not all 600: {advances}")
        names = [n for n, _ in shape(font, {}, text)]
        self.expect(".notdef" not in names, f"GeistMono has .notdef in {names}")

    def manjari(self):
        vf = self.out / "Manjari-VF.ttf"
        for weight, master, prefix in (
            (100, "Thin", "th."),
            (400, "Regular", ""),
            (500, "Regular", ""),
            (600, "Bold", "bd."),
            (700, "Bold", "bd."),
        ):
            self.same(vf, {"wght": weight}, self.src / f"Manjari-{master}.ttf", {}, MALAYALAM, prefix, SCALE)

    def manjari_weights(self):
        """Every glyph of every syllable must come from the master of the weight."""
        vf = self.out / "Manjari-VF.ttf"
        for weight, prefixes in ((100, ("th.",)), (700, ("bd.",))):
            shaper = Shaper(vf, {"wght": weight})
            leaks = [t for t in syllables() if not all(g[0].startswith(prefixes) for g in shaper.glyphs(t))]
            self.expect(not leaks, f"Manjari-VF wght={weight}: {len(leaks)} syllables leak, e.g. {leaks[:8]}")
        shaper = Shaper(vf, {"wght": 400})
        leaks = [t for t in syllables() if any(g[0].startswith(("th.", "bd.")) for g in shaper.glyphs(t))]
        self.expect(not leaks, f"Manjari-VF wght=400: {len(leaks)} syllables leak, e.g. {leaks[:8]}")

    def same(self, font: Path, axes: dict, ref: Path, ref_axes: dict, text: str, prefix="", scale=1.0):
        got = shape(font, axes, text)
        want = [(prefix + n, round(a * scale)) for n, a in shape(ref, ref_axes, text)]
        # HVAR deltas can round an advance by 1 unit.
        ok = len(got) == len(want) and all(g[0] == w[0] and abs(g[1] - w[1]) <= 1 for g, w in zip(got, want))
        self.expect(ok, f"{font.name} {axes} differs from {ref.name} {ref_axes}:\n  {got}\n  {want}")

    def expect(self, ok: bool, message: str):
        self.count += 1
        if not ok:
            self.failures.append("FAIL " + message)


def shape(path: Path, axes: dict, text: str) -> list:
    """Return (glyph name, advance) pairs, as HarfBuzz shapes the text."""
    face = hb.Face(path.read_bytes())
    font = hb.Font(face)
    if axes:
        font.set_variations(axes)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf)
    return [
        (font.glyph_to_string(i.codepoint), p.x_advance) for i, p in zip(buf.glyph_infos, buf.glyph_positions)
    ]


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
