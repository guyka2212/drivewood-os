#!/bin/bash
B=~/.config/hypr/bindings.lua
if ! grep -q 'code:201", "Drivewood menu"' "$B"; then
cat >> "$B" <<'LUA'

-- Copilot key: same Drivewood menu, without the old label
hl.unbind("SUPER + SHIFT + code:201")
o.bind("SUPER + SHIFT + code:201", "Drivewood menu", "all-settings")
LUA
fi
hyprctl reload >/dev/null; sleep 1
hyprctl binds -j | grep -c '"description": "Omarchy' | sed 's/^/omarchy labels left: /'
