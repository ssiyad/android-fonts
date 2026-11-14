#!/usr/bin/env bash
# Build the module zip: fetch sources, build and verify the fonts, list the
# font slots of the ROM, package. LINEAGE points at the LineageOS tree.
set -euo pipefail
cd "$(dirname "$0")"
lineage=${LINEAGE:-$HOME/android/lineage}
rom=$lineage/out/target/product/frogger
version=$(sed -n 's/^version=//p' module/module.prop)
run() { uv run -q --project build python -I "$@"; }

build/fetch.sh
run build/build.py build/cache/src build/cache/out build/cache/work
run build/verify.py build/cache/src build/cache/out
run build/slots.py "$rom" >module/fonts.list.new
mv module/fonts.list.new module/fonts.list
run build/package.py module build/cache/out build/cache/src "../zips/geist-fonts-$version.zip"
