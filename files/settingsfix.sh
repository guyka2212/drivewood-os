#!/bin/bash
S=http://10.0.2.2:8000
mkdir -p ~/.local/bin
curl -fsS -o ~/.local/bin/all-settings $S/os/all-settings && chmod +x ~/.local/bin/all-settings && echo "all-settings command installed"
curl -fsS -o ~/.config/fastfetch/config.jsonc $S/os/fastfetch.jsonc && echo "fastfetch updated"
curl -fsS -o ~/.config/driftwood-shell/Tide.qml $S/dshell/Tide.qml && echo "menu button updated"
B=~/.config/hypr/bindings.lua
sed -i 's/omarchy-menu toggle root/all-settings/g; s/"Omarchy menu (tap Super)"/"Drivewood menu (tap Super)"/' "$B"
grep -n "all-settings" "$B"
hyprctl reload >/dev/null
pkill -f "qs -n -p $HOME/.config/driftwood-shell"; sleep 0.5
setsid -f qs -n -p "$HOME/.config/driftwood-shell" >/dev/null 2>&1
# list any keybinding descriptions that still say Omarchy (shown in Learn > Keybindings)
hyprctl binds -j 2>/dev/null | grep -io '"description": *"[^"]*omarchy[^"]*"' | sort -u | curl -s --data-binary @- $S/bind-labels >/dev/null
echo done
