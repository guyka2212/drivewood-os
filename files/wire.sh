#!/bin/bash
# Make the Driftwood shell the desktop: keys, autostart, hide the stock bar.
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
QS="qs -p $HOME/.config/driftwood-shell ipc call driftwood"
B=~/.config/hypr/bindings.lua
cp -n "$B" ~/.config/omarchy-backup-pre-driftwood/round3/bindings.before-shell.lua 2>/dev/null

echo "== Super tap -> Tide (falls back to the Omarchy menu)"
sed -i "s#\"omarchy-menu toggle root\", { release = true }#\"$QS menu || omarchy-menu toggle root\", { release = true }#" "$B"
grep -n "tap Super" "$B"

echo "== Super+Alt+Space -> Shoreline"
if ! grep -q "driftwood shoreline" "$B"; then
  cat >> "$B" <<EOF

-- driftwood shoreline: the Apps window (falls back to Omarchy's)
o.rebind("SUPER + ALT + SPACE", "Apps", "$QS apps || omarchy-shell omarchy.dock apps")
EOF
fi
hyprctl reload >/dev/null; sleep 1
echo "config errors: $(hyprctl configerrors)"

echo "== autostart"
A=~/.config/hypr/autostart.lua
grep -q "driftwood-shell" "$A" || printf '\n-- Driftwood shell: Driftline bar, Tide menu, Shoreline apps\no.launch_on_start("qs -n -p %s/.config/driftwood-shell")\n' "$HOME" >> "$A"
tail -3 "$A"

echo "== hide the stock bar"
omarchy-toggle-bar on
echo "== done"
curl -s --data-binary @"$LOG" http://10.0.2.2:8000/wire-log >/dev/null
