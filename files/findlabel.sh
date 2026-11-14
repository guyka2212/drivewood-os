#!/bin/bash
{ grep -rn '"Omarchy menu"' ~/.config/hypr ~/.local/state/omarchy/toggles /usr/share/omarchy/default/hypr 2>/dev/null
  hyprctl binds -j | python3 -c 'import json,sys;[print(b) for b in json.load(sys.stdin) if "Omarchy" in b.get("description","")]'
} | curl -s --data-binary @- http://10.0.2.2:8000/label-src >/dev/null; echo sent
