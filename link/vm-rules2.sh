#!/bin/bash
{ ls /usr/share/omarchy/default/hypr/apps | head; echo ---
  F=$(ls /usr/share/omarchy/default/hypr/apps/*.lua | head -3); for f in $F; do echo "## $f"; head -20 "$f"; done
  echo ---; grep -rn "float = true" /usr/share/omarchy/default/hypr/apps/*.lua | head -5
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/vm-rules2 >/dev/null; echo sent
