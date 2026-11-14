#!/bin/bash
{
echo "### jsonc refs in Menu.qml"; grep -n -o -E '[A-Za-z_/.]*\.jsonc[^"]{0,0}' /usr/share/omarchy/shell/plugins/menu/Menu.qml | sort -u | head
echo "### menu jsonc files"; find /usr/share/omarchy -name '*.jsonc' 2>/dev/null
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/menu-paths
F=$(find /usr/share/omarchy -name '*.jsonc' 2>/dev/null | grep -i menu | grep -v '/config/' | head -1)
[ -n "$F" ] && curl -s --data-binary @"$F" http://10.0.2.2:8000/menu-shipped >/dev/null
echo "sent $F"
