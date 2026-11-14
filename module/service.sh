#!/system/bin/sh
# The boot completed, so the fonts work: clear the boot-loop guard that
# post-fs-data.sh set.
MODDIR=${0%/*}

until [ "$(getprop sys.boot_completed)" = 1 ]; do
	sleep 1
done
rm -f "$MODDIR/boot-pending"
echo "boot completed $(date)" >>/data/local/tmp/geist-fonts.log
