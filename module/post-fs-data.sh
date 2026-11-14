#!/system/bin/sh
# Geist fonts. Runs before zygote. The mounts are bind mounts, so they are gone
# at reboot, and each boot starts from the original files.
#
# fonts.list has one "<target> <module font>" per line. build/slots.py makes it
# from the font XMLs of the ROM. The XMLs stay as they are: a second family with
# a name that exists already makes Typeface.<clinit> throw in zygote.
MODDIR=${0%/*}
LOG=/data/local/tmp/geist-fonts.log
exec >>"$LOG" 2>&1
echo "=== geist-fonts post-fs-data $(date) ==="

main() {
	if [ -f "$MODDIR/boot-pending" ]; then
		echo "the last boot did not complete: disable the module, mount nothing"
		rm -f "$MODDIR/boot-pending"
		touch "$MODDIR/disable"
		return
	fi
	touch "$MODDIR/boot-pending"
	while read -r dst src; do
		case "$dst" in '' | '#'*) continue ;; esac
		swap "$MODDIR/fonts/$src" "$dst"
	done <"$MODDIR/fonts.list"
}

# Bind-mount font $1 over font $2, with the SELinux label of $2.
swap() {
	if [ ! -f "$1" ] || [ ! -f "$2" ]; then
		echo "skip: $1 or $2 is missing"
		return
	fi
	# The mount would land on the target of the link, which has its own line.
	if [ -L "$2" ]; then
		echo "skip: $2 is a symlink"
		return
	fi
	relabel "$1" "$2"
	if mount -o bind "$1" "$2"; then
		echo "swap: ${1##*/} -> $2"
	else
		echo "swap FAILED: $2"
	fi
}

# Give $1 the SELinux label of $2, or system_file.
relabel() {
	# shellcheck disable=SC2012 # toybox has no stat for labels
	ctx=$(ls -Zd "$2" 2>/dev/null | awk '{print $1}')
	case "$ctx" in u:*) ;; *) ctx=u:object_r:system_file:s0 ;; esac
	chcon "$ctx" "$1"
}

main
echo "=== done ==="
