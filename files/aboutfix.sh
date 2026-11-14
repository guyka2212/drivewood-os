#!/bin/bash
curl -fsS -o ~/.config/fastfetch/config.jsonc http://10.0.2.2:8000/os/fastfetch.jsonc && echo "about info updated"
curl -fsS -o ~/.config/omarchy/extensions/omarchy-menu.jsonc http://10.0.2.2:8000/os/omarchy-menu.jsonc && echo "menu updated"
