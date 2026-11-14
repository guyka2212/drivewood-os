#!/bin/bash
# Boot screen = the screensaver animation; no Omarchy text on the way up.
SRC=http://10.0.2.2:8000/plymouth/driftwood-boot
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
T=/tmp/dwboot; rm -rf "$T"; mkdir -p "$T"
curl -fsS -o "$T/files.txt" "$SRC/files.txt"
n=0; while read -r f; do [ -n "$f" ] && curl -fsS -o "$T/$f" "$SRC/$f" && n=$((n+1)); done < "$T/files.txt"
echo "downloaded $n files ($(du -sh "$T" | cut -f1))"

echo "== system part (asks for your password once)"
sudo bash -s "$T" <<'ROOT'
set -u
T=$1
B=/etc/driftwood-backup; mkdir -p "$B"
[ -e "$B/limine.conf.before-boot-anim" ] || cp -a /boot/limine.conf "$B/limine.conf.before-boot-anim"
[ -e "$B/plymouth-logo-theme" ] || cp -a /usr/share/plymouth/themes/driftwood "$B/plymouth-logo-theme"

echo "-- boot animation theme"
rm -rf /usr/share/plymouth/themes/driftwood
install -d -m 755 /usr/share/plymouth/themes/driftwood
install -m 644 "$T"/*.png "$T"/driftwood.script "$T"/driftwood.plymouth /usr/share/plymouth/themes/driftwood/
echo "installed $(ls /usr/share/plymouth/themes/driftwood | wc -l) files"
plymouth-set-default-theme driftwood && echo "default: $(plymouth-set-default-theme)"

echo "-- rebuilding boot image"
if command -v limine-mkinitcpio >/dev/null; then limine-mkinitcpio 2>&1 | tail -3; else mkinitcpio -P 2>&1 | tail -3; fi

echo "-- bootloader: no menu, no messages"
L=/boot/limine.conf
for kv in "timeout: 0" "quiet: yes"; do
  k=${kv%%:*}
  if grep -q "^$k:" "$L"; then sed -i "s/^$k:.*/$kv/" "$L"; else sed -i "1i $kv" "$L"; fi
done
head -12 "$L"
echo "entries:"; grep -n "^/" "$L"
ROOT
echo "sudo exit: $?"
echo "== done"
curl -s --data-binary @"$LOG" http://10.0.2.2:8000/boot-log >/dev/null
