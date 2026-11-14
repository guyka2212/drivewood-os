#!/bin/bash
curl -fsS -o ~/.config/driftwood-shell/Tide.qml http://10.0.2.2:8000/files/dshell/Tide.qml && echo "super menu updated"
curl -fsS -o ~/.config/omarchy/extensions/omarchy-menu.jsonc http://10.0.2.2:8000/files/os/omarchy-menu.jsonc && echo "system menu updated"
pkill -f "qs -n -p $HOME/.config/driftwood-shell"; sleep 0.5
setsid -f qs -n -p "$HOME/.config/driftwood-shell" >/dev/null 2>&1
echo done
