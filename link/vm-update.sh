#!/bin/bash
# Floating-window rules + reinstall the newest DriveWood Link (asks for your password once).
LOG=/tmp/dwlink-update.log; exec > >(tee "$LOG") 2>&1
mkdir -p ~/.local/state/omarchy/toggles/hypr
curl -fsS -o ~/.local/state/omarchy/toggles/hypr/drivewood-link.lua http://10.0.2.2:8000/link/desktop/packaging/drivewood-link-windows.lua && echo "window rules installed"
hyprctl reload >/dev/null; sleep 1; echo "config errors: $(hyprctl configerrors)"
pkill -f "python3 -m drivewood_link"; sleep 0.5
B=/tmp/dwlink-build; rm -rf "$B"; mkdir -p "$B"
curl -fsS http://10.0.2.2:8000/link/drivewood-link-desktop.tar.gz | tar xz -C "$B"
cd "$B/packaging" && makepkg -sif --noconfirm 2>&1 | tail -4
setsid -f drivewood-link >/dev/null 2>&1
echo "== done"
curl -s --data-binary @"$LOG" http://10.0.2.2:8000/link-update-log >/dev/null
