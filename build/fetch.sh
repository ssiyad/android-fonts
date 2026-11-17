#!/usr/bin/env bash
# Download the source fonts into build/cache and check their hashes.
# Roboto and Droid Sans Mono come from the commits that LineageOS 23.2 builds,
# so that the fallback glyphs match the fonts on the phone.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
cache=$here/cache
src=$cache/src
geist_ver=1.9.2
nerd_ver=v3.5.1
manjari_rev=4e5f06dbb274a27ebe71ed54ea706b3ee40eabd9
roboto=https://android.googlesource.com/platform/external/roboto-fonts/+/064c5ab9feb54e30ec26ca4bfc64f98aef8de489
lineage_base=https://raw.githubusercontent.com/LineageOS/android_frameworks_base/3428b1f9b6ab3536b90bbf1176d5037dfcb60fc4

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
	# Gitiles serves raw files as base64.
	fetch "$roboto/font/3.011/Roboto-Regular.ttf?format=TEXT" \
		Roboto-Regular.ttf 9e157d5ff70ae52cc8c527b36e89d9b3c69c6c814da79fa6237a0bf0895abc7c base64
	fetch "$roboto/NOTICE?format=TEXT" \
		Apache-2.0.txt cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30 base64
	fetch "$lineage_base/data/fonts/DroidSansMono.ttf" \
		DroidSansMono.ttf db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862
	extract
}

# fetch URL NAME SHA256 [base64]: download once, then always check the hash.
fetch() {
	local out="$cache/dl/$2"
	if [ ! -f "$out" ]; then
		curl -sSLf --retry 3 -o "$out.part" "$1"
		if [ "${4:-}" = base64 ]; then
			base64 -d "$out.part" >"$out.dec"
			mv "$out.dec" "$out.part"
		fi
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
	cp "$cache"/dl/Manjari-* "$cache/dl/Roboto-Regular.ttf" "$cache/dl/DroidSansMono.ttf" \
		"$cache/dl/Apache-2.0.txt" "$src/"
}

main "$@"
