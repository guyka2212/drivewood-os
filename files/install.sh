#!/bin/bash
# Installs the Driftwood customisation for Omarchy. Everything replaced is backed up first.
SRC=http://10.0.2.2:8000
LOG=$(mktemp)
exec > >(tee "$LOG") 2>&1
set -u

BACKUP="$HOME/.config/omarchy-backup-pre-driftwood"
echo "== backup -> $BACKUP"
if [ ! -d "$BACKUP" ]; then
  mkdir -p "$BACKUP/branding" "$BACKUP/hypr"
  cp -a ~/.config/omarchy/branding/. "$BACKUP/branding/"
  cp -a ~/.config/hypr/bindings.lua ~/.config/hypr/looknfeel.lua "$BACKUP/hypr/"
  omarchy-theme-current > "$BACKUP/previous-theme.txt"
fi
ls -R "$BACKUP"

echo "== theme files"
T=~/.config/omarchy/themes/driftwood
mkdir -p "$T/backgrounds"
for f in colors.toml icons.theme preview.png preview-unlock.png unlock.png \
         backgrounds/1-dawn.png backgrounds/2-noon.png backgrounds/3-dusk.png backgrounds/4-night.png; do
  curl -fsS -o "$T/$f" "$SRC/driftwood/$f" && echo "ok $f" || echo "FAILED $f"
done
cp /usr/share/omarchy/themes/tokyo-night/neovim.lua /usr/share/omarchy/themes/tokyo-night/vscode.json "$T/"

echo "== branding"
curl -fsS -o ~/.config/omarchy/branding/screensaver.txt "$SRC/screensaver.txt" && echo "ok screensaver"
curl -fsS -o ~/.config/omarchy/branding/about.txt "$SRC/about.txt" && echo "ok about"

echo "== launchers"
TERMCMD=xdg-terminal-exec; command -v xdg-terminal-exec >/dev/null || TERMCMD=alacritty
A=~/.local/share/applications
cat > "$A/tidepool.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Tidepool
Comment=Artificial life from a few simple rules
Exec=chromium --app=file://$HOME/tidepool/index.html
Icon=applications-science
Categories=Education;Science;
EOF
cat > "$A/driftwood.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Driftwood
Comment=An endless landscape drifting through your terminal
Exec=$TERMCMD $HOME/driftwood/driftwood.py
Icon=weather-clear-night
Categories=Graphics;
EOF
update-desktop-database "$A" 2>/dev/null; echo "terminal launcher: $TERMCMD"

echo "== keybindings"
BINDS=$(omarchy menu keybindings --print 2>/dev/null)
add_bind() {  # key, name, command
  if grep -q "\"$1\"" ~/.config/hypr/bindings.lua; then echo "already set: $1"; return; fi
  local k=$(echo "$1" | sed 's/ //g')
  if echo "$BINDS" | sed 's/ //g' | grep -qi "^$k\b\|[^A-Z]$k[^A-Z+]"; then echo "TAKEN, skipped: $1"; return; fi
  printf '\no.bind("%s", "%s", "%s")\n' "$1" "$2" "$3" >> ~/.config/hypr/bindings.lua
  echo "bound $1 -> $2"
}
echo "$BINDS" | grep -i -E 'ALT.*(D|T)\b' | head
add_bind "SUPER + ALT + D" "Driftwood" "$TERMCMD $HOME/driftwood/driftwood.py"
add_bind "SUPER + ALT + T" "Tidepool" "chromium --app=file://$HOME/tidepool/index.html"

echo "== look and feel"
if ! grep -q "driftwood look" ~/.config/hypr/looknfeel.lua; then
cat >> ~/.config/hypr/looknfeel.lua <<'EOF'

-- driftwood look: soft rounded windows
hl.config({
  decoration = {
    rounding = 10,
  },
})
EOF
echo "rounded corners added"
fi

echo "== apply"
hyprctl reload 2>&1 | tail -1
omarchy-theme-list | grep -i drift
omarchy-theme-set "Driftwood" 2>&1 | tail -5
sleep 3
echo "current theme: $(omarchy-theme-current)"
echo "background: $(readlink ~/.local/state/omarchy/current/background)"
hyprctl configerrors 2>&1 | head
echo "== done"
curl -s --data-binary @"$LOG" $SRC/install-log >/dev/null
