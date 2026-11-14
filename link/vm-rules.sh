#!/bin/bash
{ grep -rn -i "float" ~/.config/hypr/*.lua /usr/share/omarchy/default/hypr/*.lua /usr/share/omarchy/default/hypr/**/*.lua 2>/dev/null | head -25
  echo ---; ls ~/.config/hypr /usr/share/omarchy/default/hypr
  echo ---; hyprctl clients -j | python3 -c 'import json,sys;[print(c["class"],c["title"],c["floating"]) for c in json.load(sys.stdin)]'
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/vm-rules >/dev/null; echo sent
