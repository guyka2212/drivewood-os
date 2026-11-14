#!/bin/bash
F=~/.config/hypr/bindings.lua
# drop the earlier attempts (everything from the driftwood marker to the end of the file)
sed -i '/^-- driftwood: tap Super/,$d' "$F"
curl -fsS http://10.0.2.2:8000/os/super-tap.lua >> "$F"
hyprctl reload >/dev/null; sleep 1
{ echo "errors: $(hyprctl configerrors)"; hyprctl binds -j | jq -c '.[] | select(.key=="Super_L") | {release, non_consuming, modmask, description}'; } | curl -s --data-binary @- http://10.0.2.2:8000/superfix
