#!/bin/bash
# Colours that follow the wallpaper: palette script, theme accents, shell restart.
SRC=http://10.0.2.2:8000
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1

echo "== palette script"
curl -fsS -o ~/.local/bin/driftwood-palette $SRC/os/driftwood-palette && chmod +x ~/.local/bin/driftwood-palette

echo "== theme accents: sky + cyan instead of peach + violet"
T=~/.config/omarchy/themes/driftwood
curl -fsS -o "$T/colors.toml" $SRC/driftwood/colors.toml
curl -fsS -o "$T/shell.toml" $SRC/driftwood/shell.toml
sed -i 's/rgba(f2a97aee)/rgba(8fb4e6ee)/; s/rgba(c79ad6ee)/rgba(6ac8dcee)/' ~/.config/hypr/looknfeel.lua
grep -n "active_border = {" ~/.config/hypr/looknfeel.lua

echo "== re-apply theme, restore the time-of-day sky"
omarchy-theme-set Driftwood 2>&1 | tail -2
sleep 3
~/.local/bin/driftwood-sky --force

echo "== first palette"
~/.local/bin/driftwood-palette
echo "config errors: $(hyprctl configerrors)"
echo "== done"
curl -s --data-binary @"$LOG" $SRC/palette-log >/dev/null
