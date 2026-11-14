#!/bin/bash
cd /tmp && pacman -Sw --noconfirm --cachedir /tmp/pc hyprland >/dev/null 2>&1
P=$(ls /tmp/pc/hyprland-0*.pkg.tar.zst | head -1)
{ echo "### files"; bsdtar -tf "$P" | grep -E 'usr/share/hypr|example' | head -20
  for f in $(bsdtar -tf "$P" | grep -E 'usr/share/hypr/.*\.(lua|conf)$'); do echo "### $f"; bsdtar -xOf "$P" "$f"; done
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/hypr-example >/dev/null; echo sent
