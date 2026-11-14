#!/bin/bash
# Run the newest app code from ~/.cache without reinstalling (for quick tests).
pkill -f "python3 -m drivewood_link" ; sleep 0.5
D=~/.cache/dwlink-try; rm -rf "$D"; mkdir -p "$D"
curl -fsS http://10.0.2.2:8000/link/drivewood-link-desktop.tar.gz | tar xz -C "$D"
cd "$D" && setsid -f python3 -m drivewood_link >/tmp/dwlink.log 2>&1
echo started
