#!/bin/bash
SRC=http://10.0.2.2:8000
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
I=~/.local/share/icons/hicolor/256x256/apps
mkdir -p "$I"
curl -fsS -o "$I/driftwood.png" $SRC/os/driftwood.png && echo "icon driftwood ok"
curl -fsS -o "$I/tidepool.png" $SRC/os/tidepool.png && echo "icon tidepool ok"
A=~/.local/share/applications
sed -i "s|^Icon=.*|Icon=$I/driftwood.png|" "$A/driftwood.desktop"
sed -i "s|^Icon=.*|Icon=$I/tidepool.png|" "$A/tidepool.desktop"
grep -H Icon "$A/driftwood.desktop" "$A/tidepool.desktop"
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor 2>/dev/null; update-desktop-database "$A" 2>/dev/null
curl -fsS -o ~/.local/bin/driftwood-sky $SRC/os/driftwood-sky && chmod +x ~/.local/bin/driftwood-sky && echo "sky script ok"
curl -fsS -o ~/.config/omarchy/extensions/omarchy-menu.jsonc $SRC/os/omarchy-menu.jsonc && echo "menu ok"
~/.local/bin/driftwood-sky --force
~/.local/bin/driftwood-sky
curl -s --data-binary @"$LOG" $SRC/install3-log >/dev/null
