#!/usr/bin/env bash
# Build the module zip: fetch sources, build and verify the fonts, list the
# font slots of the ROM, package. LINEAGE points at the LineageOS tree; without
# a built tree, the committed fonts.list stays. The zip goes to OUT.
set -euo pipefail
cd "$(dirname "$0")"
lineage=${LINEAGE:-$HOME/android/lineage}
rom=$lineage/out/target/product/frogger
out=${OUT:-../zips}
version=$(sed -n 's/^version=//p' module/module.prop)
run() { uv run -q --project build python -I "$@"; }

build/fetch.sh
run build/build.py build/cache/src build/cache/out build/cache/work
run build/verify.py build/cache/src build/cache/out
if [ -d "$rom/system/etc" ]; then
	run build/slots.py "$rom" >module/fonts.list.new
	mv module/fonts.list.new module/fonts.list
else
	echo "no ROM at $rom: using the committed fonts.list"
fi
run build/package.py module build/cache/out build/cache/src "$out/geist-fonts-$version.zip"
