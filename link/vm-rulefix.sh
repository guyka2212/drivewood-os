#!/bin/bash
curl -fsS -o ~/.local/state/omarchy/toggles/hypr/drivewood-link.lua http://10.0.2.2:8000/link/desktop/packaging/drivewood-link-windows.lua
hyprctl reload >/dev/null; sleep 1; echo "config errors: $(hyprctl configerrors)"
