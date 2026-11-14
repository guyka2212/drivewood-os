#!/bin/bash
# Rename the OS from Driftwood to Drivewood everywhere it is visible.
SRC=http://10.0.2.2:8000
LOG=/tmp/rename.log; exec > >(tee "$LOG") 2>&1

echo "== theme: driftwood -> drivewood"
T=~/.config/omarchy/themes
if [ -d "$T/driftwood" ] && [ ! -d "$T/drivewood" ]; then mv "$T/driftwood" "$T/drivewood"; fi
curl -fsS -o "$T/drivewood/unlock.png" $SRC/driftwood/unlock.png && echo "lock-screen logo updated"
sed -i 's/== driftwood ]]/== drivewood ]]/; s/Driftwood theme/Drivewood theme/' ~/.local/bin/driftwood-sky
grep -n "drivewood" ~/.local/bin/driftwood-sky

echo "== menus, fastfetch, app entry"
curl -fsS -o ~/.config/omarchy/extensions/omarchy-menu.jsonc $SRC/os/omarchy-menu.jsonc
sed -i 's/Driftwood \$version/Drivewood $version/' ~/.config/fastfetch/config.jsonc
sed -i 's/^Name=Driftwood$/Name=Drivewood Landscape/' ~/.local/share/applications/driftwood.desktop
grep -h "^Name=" ~/.local/share/applications/driftwood.desktop

echo "== shell"
for f in Tide.qml; do curl -fsS -o ~/.config/driftwood-shell/$f $SRC/dshell/$f; done

echo "== fetch boot animation"
B=/tmp/dwboot; rm -rf "$B"; mkdir -p "$B"
curl -fsS -o "$B/files.txt" $SRC/plymouth/driftwood-boot/files.txt
while read -r f; do [ -n "$f" ] && curl -fsS -o "$B/$f" "$SRC/plymouth/driftwood-boot/$f"; done < "$B/files.txt"
curl -fsS -o /tmp/os-release $SRC/os/os-release
curl -fsS -o /tmp/dw-logo.png $SRC/driftwood/unlock.png
echo "fetched $(ls "$B" | wc -l) boot files"

echo "== system part (asks for your password once)"
sudo bash -s <<'ROOT'
set -u
B=/tmp/dwboot
install -m 644 /tmp/os-release /etc/os-release && grep PRETTY /etc/os-release
rm -rf /usr/share/plymouth/themes/driftwood
install -d -m 755 /usr/share/plymouth/themes/driftwood
install -m 644 "$B"/*.png "$B"/driftwood.script "$B"/driftwood.plymouth /usr/share/plymouth/themes/driftwood/
plymouth-set-default-theme driftwood
install -m 644 /tmp/dw-logo.png /usr/share/sddm/themes/omarchy/logo.png && echo "login logo updated"
if command -v limine-mkinitcpio >/dev/null; then limine-mkinitcpio 2>&1 | tail -2; else mkinitcpio -P 2>&1 | tail -2; fi
L=/boot/limine.conf
for kv in "timeout: 0" "quiet: yes"; do k=${kv%%:*}; grep -q "^$k:" "$L" && sed -i "s/^$k:.*/$kv/" "$L" || sed -i "1i $kv" "$L"; done
sed -i -E 's/^(interface_branding:).*/\1 Drivewood/' "$L"
grep -n -E "^(timeout|quiet|interface_branding):" "$L"
ROOT
echo "sudo exit: $?"

echo "== apply"
omarchy-theme-set Drivewood 2>&1 | tail -2
sleep 3
~/.local/bin/driftwood-sky --force
pkill -f "qs -n -p $HOME/.config/driftwood-shell"; sleep 0.5; setsid -f qs -n -p "$HOME/.config/driftwood-shell" >/dev/null 2>&1
echo "theme now: $(omarchy-theme-current)"
echo "== done"
curl -s --data-binary @"$LOG" $SRC/rename-log >/dev/null
