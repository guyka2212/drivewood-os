#!/bin/bash
curl -fsS -o ~/.config/omarchy/extensions/omarchy-menu.jsonc http://10.0.2.2:8000/os/omarchy-menu.jsonc && echo "menu overrides installed"
curl -fsS -o ~/.config/driftwood-shell/Tide.qml http://10.0.2.2:8000/dshell/Tide.qml && echo "tide updated"
pkill -f "qs -n -p $HOME/.config/driftwood-shell"; sleep 0.5
setsid -f qs -n -p "$HOME/.config/driftwood-shell" >/dev/null 2>&1
echo done
