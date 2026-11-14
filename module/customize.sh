# Sourced by the KernelSU installer.
SELF=${MODPATH##*/}

set_perm_recursive "$MODPATH" 0 0 0755 0644
rm -f "/data/adb/modules/$SELF/boot-pending"

# Two modules that bind-mount the same font files fight; the last mount wins.
for dir in /data/adb/modules/*; do
	id=${dir##*/}
	[ "$id" = "$SELF" ] && continue
	[ -f "$dir/disable" ] || [ -f "$dir/remove" ] && continue
	if [ -d "$dir/system/fonts" ] || [ -d "$dir/system/product/fonts" ] ||
		grep -qs "/fonts/" "$dir/post-fs-data.sh" "$dir/service.sh"; then
		ui_print "! Module '$id' also changes fonts. Disable it, or the fonts mix."
	fi
done

ui_print "- After a boot that does not complete, the module disables itself."
ui_print "- Log: /data/local/tmp/geist-fonts.log"
