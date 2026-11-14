#!/bin/bash
{ echo "### config errors"; hyprctl configerrors
  echo "### processes"; for p in qs swaybg mako hypridle drivewood_link; do printf '%s: ' $p; pgrep -f "$p" >/dev/null && echo running || echo MISSING; done
  echo "### user units"; systemctl --user is-active drivewood-sky.timer drivewood-link.service
  echo "### palette"; cat ~/.local/state/drivewood/palette.json; echo; ls ~/.local/state/drivewood
  echo "### background"; readlink -f ~/.local/state/drivewood/background
  echo "### binds with Super_L"; hyprctl binds -j | python3 -c 'import json,sys;[print(b["key"],b["release"],b["description"]) for b in json.load(sys.stdin) if "Super" in b["key"]]'
  echo "### disk"; df -h / | tail -1
  echo "### link"; pacman -Q drivewood-link; ls -la /dev/uinput
  echo "### which start-hyprland"; command -v start-hyprland
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/check >/dev/null; echo sent
