#!/bin/bash
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
curl -fsS -o ~/.local/bin/driftwood-palette http://10.0.2.2:8000/os/driftwood-palette && chmod +x ~/.local/bin/driftwood-palette
sed -i '/-- driftwood border/,/-- end driftwood border/d' ~/.config/hypr/looknfeel.lua
echo "looknfeel border block left: $(grep -c 'driftwood border' ~/.config/hypr/looknfeel.lua)"
~/.local/bin/driftwood-palette
sleep 1
cat ~/.local/state/omarchy/toggles/hypr/driftwood-border.lua
echo "config errors: $(hyprctl configerrors)"
hyprctl getoption general:col.active_border 2>&1 | head -3
curl -s --data-binary @"$LOG" http://10.0.2.2:8000/palette2-log >/dev/null
