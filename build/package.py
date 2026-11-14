"""Make the KernelSU module zip.

Usage: package.py MODULE_DIR FONTS_DIR SRC_DIR OUT_ZIP

Takes the scripts from MODULE_DIR, the fonts that fonts.list names from
FONTS_DIR, and the font licenses from SRC_DIR.
"""

import sys
import zipfile
from pathlib import Path

LICENSES = ["Geist-OFL.txt", "Manjari-OFL.txt", "GeistMonoNerdFont-LICENSE.txt"]
NOTICE = """\
Geist (OFL-1.1): https://github.com/vercel/geist-font
Manjari (OFL-1.1): https://github.com/smc/manjari
Geist Mono Nerd Font (OFL-1.1, patcher MIT): https://github.com/ryanoasis/nerd-fonts
The Geist fonts contain glyphs of Roboto (Apache-2.0) for the characters that
Geist does not have. The Geist Mono font contains glyphs of Droid Sans Mono
(Apache-2.0) for the same reason. Both come from the LineageOS source tree.
"""


def main(module: Path, fonts: Path, src: Path, out: Path):
    used = sorted({line.split()[1] for line in (module / "fonts.list").read_text().splitlines() if line.strip()})
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(p for p in module.rglob("*") if p.is_file()):
            zf.write(path, path.relative_to(module).as_posix())
        for name in used:
            zf.write(fonts / name, f"fonts/{name}")
        for name in LICENSES:
            zf.write(src / name, f"licenses/{name}")
        zf.writestr("licenses/NOTICE.txt", NOTICE)
    print(f"{out}: {len(used)} fonts, {out.stat().st_size // 1024} KiB")


if __name__ == "__main__":
    main(*(Path(arg) for arg in sys.argv[1:5]))
