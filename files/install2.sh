#!/bin/bash
# Driftwood, round 2: prompt, greeting, menu, bar, motion, lock colours, time-of-day sky.
SRC=http://10.0.2.2:8000
LOG=$(mktemp); exec > >(tee "$LOG") 2>&1
B="$HOME/.config/omarchy-backup-pre-driftwood"
mkdir -p "$B/round2"
for f in ~/.config/starship.toml ~/.bashrc ~/.config/omarchy/shell.json ~/.config/omarchy/extensions/omarchy-menu.jsonc ~/.config/hypr/looknfeel.lua; do
  [ -e "$B/round2/$(basename "$f")" ] || cp -a "$f" "$B/round2/"
done
echo "== backed up: $(ls "$B/round2" | tr '\n' ' ')"

echo "== theme: lock-screen colours"
curl -fsS -o ~/.config/omarchy/themes/driftwood/shell.lock.toml $SRC/driftwood/shell.lock.toml && echo ok

echo "== prompt"
curl -fsS -o ~/.config/starship.toml $SRC/os/starship.toml && echo ok

echo "== omarchy menu"
curl -fsS -o ~/.config/omarchy/extensions/omarchy-menu.jsonc $SRC/os/omarchy-menu.jsonc && echo ok

echo "== time-of-day sky"
mkdir -p ~/.local/bin ~/.config/systemd/user
curl -fsS -o ~/.local/bin/driftwood-sky $SRC/os/driftwood-sky && chmod +x ~/.local/bin/driftwood-sky
curl -fsS -o ~/.config/systemd/user/driftwood-sky.service $SRC/os/driftwood-sky.service
curl -fsS -o ~/.config/systemd/user/driftwood-sky.timer $SRC/os/driftwood-sky.timer
systemctl --user daemon-reload
systemctl --user enable --now driftwood-sky.timer 2>&1
systemctl --user list-timers driftwood-sky.timer --no-pager 2>&1 | head -3

echo "== terminal greeting"
if ! grep -q "driftwood greeting" ~/.bashrc; then
cat >> ~/.bashrc <<'EOF'

# driftwood greeting: one quiet line about the sky when a terminal opens
driftwood_greet() {
  local h=$((10#$(date +%H))) icon msg
  if   (( h >= 5  && h < 8  )); then icon=$'\U000F059C'; msg="dawn over the lake"
  elif (( h >= 8  && h < 17 )); then icon=$'\U000F0599'; msg="clear skies over the ridge"
  elif (( h >= 17 && h < 20 )); then icon=$'\U000F059B'; msg="the peaks are turning pink"
  else                               icon=$'\U000F0594'; msg="stars over the water"; fi
  printf '\e[38;2;143;180;230m%s\e[0m  \e[38;2;125;127;143m%s, %s\e[0m\n' "$icon" "$msg" "$USER"
}
[[ -z $DRIFTWOOD_QUIET ]] && driftwood_greet
EOF
echo "greeting added"; fi

echo "== bar + dock"
python3 - <<'EOF'
import json, os
p = os.path.expanduser("~/.config/omarchy/shell.json")
d = json.load(open(p))
for item in d["bar"]["layout"]["center"]:
    if item.get("id") == "omarchy.clock":
        item["format"] = "ddd d MMM  ·  HH:mm"
pinned = d.setdefault("dock", {}).setdefault("pinned", [])
for app in ("driftwood", "tidepool"):
    if app not in pinned: pinned.append(app)
json.dump(d, open(p, "w"), indent=2)
print("clock + dock updated")
EOF

echo "== motion"
if ! grep -q "driftwood motion" ~/.config/hypr/looknfeel.lua; then
cat >> ~/.config/hypr/looknfeel.lua <<'EOF'

-- driftwood motion: windows float in gently, workspaces glide, unfocused windows rest a little dimmer
hl.curve("drift", { type = "bezier", points = { { 0.22, 1 }, { 0.36, 1 } } })
hl.animation({ leaf = "windowsIn", enabled = true, speed = 5, bezier = "drift", style = "popin 80%" })
hl.animation({ leaf = "workspaces", enabled = true, speed = 4, bezier = "drift", style = "slidefade 15%" })
hl.config({
  general = { gaps_in = 6, gaps_out = 12 },
  decoration = { dim_inactive = true, dim_strength = 0.08 },
})
EOF
echo "motion added"; fi
hyprctl reload >/dev/null; sleep 1
echo "config errors: $(hyprctl configerrors 2>&1)"

echo "== re-apply theme (stages lock colours), then set the sky"
omarchy-theme-set "Driftwood" 2>&1 | tail -3
sleep 3
~/.local/bin/driftwood-sky --force
echo "background: $(readlink ~/.local/state/omarchy/current/background)"
echo "== done"
curl -s --data-binary @"$LOG" $SRC/install2-log >/dev/null
