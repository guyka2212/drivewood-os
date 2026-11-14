#!/bin/bash
# Driftwood, final round. User part first, then one sudo prompt for the system part.
SRC=http://10.0.2.2:8000
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
T=$(mktemp -d)

echo "== Driftwood menu button (bar plugin)"
P=~/.config/omarchy/plugins/driftwood-menu; mkdir -p "$P"
curl -fsS -o "$P/manifest.json" $SRC/plugin/driftwood-menu/manifest.json
curl -fsS -o "$P/BarWidget.qml" $SRC/plugin/driftwood-menu/BarWidget.qml
omarchy-shell shell rescanPlugins >/dev/null 2>&1; sleep 1
omarchy plugin enable driftwood.menu --before omarchy.workspaces 2>&1 | tail -2
python3 - <<'EOF'
import json, os
p = os.path.expanduser("~/.config/omarchy/shell.json")
d = json.load(open(p))
left = d["bar"]["layout"]["left"]
d["bar"]["layout"]["left"] = [w for w in left if w.get("id") != "omarchy.menu"]
if not any(w.get("id") == "driftwood.menu" for w in d["bar"]["layout"]["left"]):
    d["bar"]["layout"]["left"].insert(0, {"id": "driftwood.menu"})
json.dump(d, open(p, "w"), indent=2)
print("bar left:", [w["id"] for w in d["bar"]["layout"]["left"]])
EOF

echo "== fetching system files"
mkdir -p "$T/driftwood"
for f in driftwood.plymouth driftwood.script block0.png block1.png block2.png block3.png; do
  curl -fsS -o "$T/driftwood/$f" "$SRC/plymouth/driftwood/$f" || echo "FAILED $f"
done
curl -fsS -o "$T/os-release" $SRC/os/os-release

echo "== system part (asks for your password once)"
sudo bash -s "$T" <<'ROOT'
set -u
T=$1
B=/etc/driftwood-backup; mkdir -p "$B"
[ -e "$B/os-release" ] || cp -a /etc/os-release "$B/"
[ -e "$B/limine.conf" ] || cp -a /boot/limine.conf "$B/" 2>/dev/null
[ -e "$B/limine.default" ] || cp -a /etc/default/limine "$B/limine.default" 2>/dev/null
echo "backups: $(ls $B | tr '\n' ' ')"

echo "-- animated boot splash"
rm -rf /usr/share/plymouth/themes/driftwood
install -d -m 755 /usr/share/plymouth/themes/driftwood
install -m 644 "$T"/driftwood/* /usr/share/plymouth/themes/driftwood/
plymouth-set-default-theme driftwood && echo "default splash: $(plymouth-set-default-theme)"

echo "-- system name"
install -m 644 "$T/os-release" /etc/os-release && grep PRETTY /etc/os-release

echo "-- rebuilding boot image"
if command -v limine-mkinitcpio >/dev/null; then limine-mkinitcpio 2>&1 | tail -4; else mkinitcpio -P 2>&1 | tail -4; fi

echo "-- bootloader title"
grep -n -i "branding" /boot/limine.conf /etc/default/limine 2>/dev/null
sed -i -E 's/^([[:space:]]*interface_branding:[[:space:]]*).*/\1Driftwood/I' /boot/limine.conf
grep -n -i "interface_branding" /boot/limine.conf
ROOT
echo "sudo exit: $?"
rm -rf "$T"
echo "== done"
curl -s --data-binary @"$LOG" $SRC/system-log >/dev/null
