#!/bin/bash
M=/usr/share/omarchy/shell/plugins/menu
{
echo "### files"; ls -la $M; ls /usr/share/omarchy/config/omarchy/extensions/ 2>&1
echo "### where is the menu defined"; grep -rln '"setup"\|setup\.monitors\|"Setup"' /usr/share/omarchy/shell /usr/share/omarchy/default 2>/dev/null | head
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/menu-files
F=$(grep -rln 'setup\.' /usr/share/omarchy/shell /usr/share/omarchy/default 2>/dev/null | grep -i -E 'menu.*\.(json|jsonc|js)$' | head -1)
[ -n "$F" ] && curl -s --data-binary @"$F" "http://10.0.2.2:8000/menu-def" >/dev/null
echo "$F" | curl -s --data-binary @- http://10.0.2.2:8000/menu-def-path >/dev/null
curl -s --data-binary @$M/MenuModel.js http://10.0.2.2:8000/menumodel >/dev/null
echo sent
