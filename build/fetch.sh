#!/usr/bin/env bash
# Download the source fonts into build/cache and check their hashes.
# Roboto and Droid Sans Mono come from the LineageOS tree, so that the
# fallback glyphs match the fonts on the phone.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
cache=$here/cache
src=$cache/src
lineage=${LINEAGE:-$HOME/android/lineage}

geist_ver=1.9.2
nerd_ver=v3.5.1
manjari_rev=4e5f06dbb274a27ebe71ed54ea706b3ee40eabd9

main() {
	mkdir -p "$cache/dl" "$src"
	fetch "https://github.com/vercel/geist-font/releases/download/v$geist_ver/geist-font-v$geist_ver.zip" \
		geist.zip 15f066d58dcb99fb10014a49913009fdaf41e464cfb8851a44b44e593c95d3d8
	fetch "https://github.com/ryanoasis/nerd-fonts/releases/download/$nerd_ver/GeistMono.zip" \
		geistmono-nf.zip 4799a6c340f3993cea7f59c256c723afb3e70233471ea9042d92f153b87ef83e
	for f in Regular:16460924696bfea2a2f71b4201d8786867c6413b548ecbd22bc6bfe55be90f95 \
		Bold:f19fef695b28e5448ae87451dfbab426676cadf4b59340558a157c0071b69d26 \
		Thin:0eab2fd482b2b0e6cd469c53d09513a2303ff91c86dc8c1ba42acfc73242bd72; do
		fetch "https://raw.githubusercontent.com/google/fonts/$manjari_rev/ofl/manjari/Manjari-${f%%:*}.ttf" \
			"Manjari-${f%%:*}.ttf" "${f#*:}"
	done
	fetch "https://raw.githubusercontent.com/google/fonts/$manjari_rev/ofl/manjari/OFL.txt" \
		Manjari-OFL.txt 2e144823e28b854ff5e1d41db9a2180fdb1d8e44a71c2ae4fca5c4b2a5adde4c
	extract
}

# fetch URL NAME SHA256: download once, then always check the hash.
fetch() {
	local out="$cache/dl/$2"
	if [ ! -f "$out" ]; then
		curl -sSLf --retry 3 -o "$out.part" "$1"
		mv "$out.part" "$out"
	fi
	echo "$3  $out" | sha256sum -c --quiet
}

extract() {
	unzip -q -o -j "$cache/dl/geist.zip" -d "$src" \
		'geist-font/Geist/variable/Geist[[]wght].ttf' \
		'geist-font/Geist/variable/Geist-Italic[[]wght].ttf' \
		'geist-font/OFL.txt'
	mv "$src/OFL.txt" "$src/Geist-OFL.txt"
	unzip -q -o -j "$cache/dl/geistmono-nf.zip" -d "$src" GeistMonoNerdFont-Regular.otf LICENSE
	mv "$src/LICENSE" "$src/GeistMonoNerdFont-LICENSE.txt"
	cp "$cache"/dl/Manjari-* "$src/"
	cp "$lineage/external/roboto-fonts/font/3.011/Roboto-Regular.ttf" "$src/"
	cp "$lineage/frameworks/base/data/fonts/DroidSansMono.ttf" "$src/"
}

main "$@"
