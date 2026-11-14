#!/bin/bash
curl -fsS -o ~/.config/hypr/hyprland.lua http://10.0.2.2:8000/build/desktop/config/hypr/hyprland.lua && hyprctl reload >/dev/null
echo "config errors: $(hyprctl configerrors)"; hyprctl binds -j | grep -c '"Close window"' | sed 's/^/close binds: /'
