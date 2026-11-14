#!/bin/bash
# Driftwood round 3: Super-alone menu, Driftwood logo, generated editor colours, glassy bar, gradient borders.
SRC=http://10.0.2.2:8000
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
B="$HOME/.config/omarchy-backup-pre-driftwood/round3"; mkdir -p "$B"
cp -an ~/.config/hypr/bindings.lua ~/.config/hypr/looknfeel.lua ~/.config/omarchy/shell.json "$B/"
T=~/.config/omarchy/themes/driftwood

echo "== logo (boot splash + lock screen)"
curl -fsS -o "$T/unlock.png" $SRC/driftwood/unlock.png && file "$T/unlock.png"

echo "== let Omarchy generate Neovim / VS Code colours from the Driftwood palette"
rm -f "$T/neovim.lua" "$T/vscode.json" && echo "removed copied Tokyo Night editor files"

echo "== glassy bar"
python3 - <<'EOF'
import json, os
p = os.path.expanduser("~/.config/omarchy/shell.json")
d = json.load(open(p)); d["bar"]["background"] = "glassy"
json.dump(d, open(p, "w"), indent=2); print("bar background:", d["bar"]["background"])
EOF

echo "== Super alone opens the Omarchy menu"
if ! grep -q "driftwood: tap Super" ~/.config/hypr/bindings.lua; then
cat >> ~/.config/hypr/bindings.lua <<'EOF'

-- driftwood: tap Super on its own to open the Omarchy menu (replaces Super + Space).
-- It fires on release, and Hyprland skips it if another key was pressed while Super was held.
hl.unbind("SUPER + SPACE")
o.bind("SUPER + Super_L", "Omarchy menu", { menu = "root" }, { release = true, ignore_mods = true })
EOF
echo "added"; fi

echo "== gradient window borders"
if ! grep -q "driftwood border" ~/.config/hypr/looknfeel.lua; then
cat >> ~/.config/hypr/looknfeel.lua <<'EOF'

-- driftwood border: sunrise-to-dusk gradient on the focused window
hl.config({
  general = {
    col = {
      active_border = { colors = { "rgba(f2a97aee)", "rgba(c79ad6ee)" }, angle = 45 },
      inactive_border = "rgba(33364aaa)",
    },
  },
})
-- end driftwood border
EOF
fi

echo "== re-apply theme"
omarchy-theme-set "Driftwood" 2>&1 | tail -3
sleep 3
hyprctl reload >/dev/null; sleep 1
ERR=$(hyprctl configerrors 2>&1)
if [[ -n $ERR && $ERR != *"no errors"* ]]; then
  echo "config error: $ERR"
  if [[ $ERR == *looknfeel* ]]; then
    sed -i '/-- driftwood border/,/-- end driftwood border/d' ~/.config/hypr/looknfeel.lua
    hyprctl reload >/dev/null; echo "gradient removed; errors now: $(hyprctl configerrors)"
  fi
else
  echo "config errors: none"
fi
ls "$T"; ls ~/.local/state/omarchy/current/theme/ | grep -E 'neovim|vscode'
head -12 ~/.local/state/omarchy/current/theme/neovim.lua
~/.local/bin/driftwood-sky --force
hyprctl binds 2>/dev/null | grep -B2 -A8 -i "super_l" | head -20
echo "== done"
curl -s --data-binary @"$LOG" $SRC/install4-log >/dev/null
