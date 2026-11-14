#!/bin/bash
{ echo "### share/hypr"; ls -R /mnt/usr/share/hypr 2>&1 | head -30
  for f in $(find /mnt/usr/share/hypr -maxdepth 2 -name '*.lua' -o -maxdepth 2 -name '*.conf' | head -5); do echo "### $f"; cat "$f"; done
  echo "### quickshell"; ls /mnt/usr/lib/qt6/qml/Quickshell 2>&1 | head
  echo "### hyprlock example"; ls /mnt/usr/share/hypr* 2>/dev/null
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/hypr-example >/dev/null; echo sent
