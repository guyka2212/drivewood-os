#!/bin/bash
# Install DriveWood Link from the bridge (asks for your password once, for pacman).
LOG=/tmp/dwlink-install.log; exec > >(tee "$LOG") 2>&1
B=/tmp/dwlink-build; rm -rf "$B"; mkdir -p "$B"
curl -fsS http://10.0.2.2:8000/link/drivewood-link-desktop.tar.gz | tar xz -C "$B" && echo "fetched"
cd "$B/packaging" && makepkg -si --noconfirm 2>&1 | tail -15
sed -i "s/38;2;242;169;122m/38;2;143;180;230m/" ~/.bashrc
echo "installed: $(pacman -Q drivewood-link 2>&1)"
curl -s --data-binary @"$LOG" http://10.0.2.2:8000/link-install-log >/dev/null
