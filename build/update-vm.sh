#!/bin/bash
# Update a running Drivewood VM with the newest build (asks for your password once).
SRC=http://10.0.2.2:8000
curl -fsS -o /tmp/stage.tar.gz $SRC/build/stage.tar.gz || exit 1
sudo bash -c '
  tar xzf /tmp/stage.tar.gz --no-same-owner -C / --exclude=./etc/skel/.config/hypr/hypridle.conf --exclude=./etc/skel/.config/drivewood
  chmod 755 /usr/bin/drivewood-*
  sed -i "s/^command = \"Hyprland\"/command = \"start-hyprland\"/; s/agreety --cmd Hyprland/agreety --cmd start-hyprland/" /etc/greetd/config.toml
  update-desktop-database -q /usr/share/applications
' && echo "system files updated"
for f in hypr/hyprland.lua hypr/hyprlock.conf foot/foot.ini mako/config fastfetch/config.jsonc starship.toml; do
  install -D -m 644 /etc/skel/.config/$f ~/.config/$f
done
drivewood-palette >/dev/null && echo "wallpaper colours: ok"
hyprctl reload >/dev/null; echo "config errors: $(hyprctl configerrors)"
pkill -f "qs -n -p /usr/share/drivewood/shell"; sleep 0.5; setsid -f qs -n -p /usr/share/drivewood/shell >/dev/null 2>&1
makoctl reload 2>/dev/null
echo "== done"
