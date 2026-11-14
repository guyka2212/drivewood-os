#!/bin/bash
# Record the screensaver's matrix effect (Driftwood colours, short rain) for the boot screen.
curl -fsS -o "$HOME/.config/omarchy/branding/screensaver.txt" http://10.0.2.2:8000/screensaver.txt
rm -f /tmp/ss.raw /tmp/ss.err
SECONDS=0
ttfx -i "$HOME/.config/omarchy/branding/screensaver.txt" --frame-rate 30 \
  --canvas-width 110 --canvas-height 18 --ignore-terminal-dimensions \
  --anchor-canvas c --anchor-text c --seed 7 --no-eol \
  matrix --rain-time 3 \
  --rain-color-gradient 1d3557 2f5d8a 5f93c8 8fb4e6 6ac8dc \
  --highlight-color e8f3ff \
  --final-gradient-stops 8fb4e6 6ac8dc e6dccb \
  --resolve-delay 2 > /tmp/ss.raw 2> /tmp/ss.err
code=$?
{ echo "exit=$code took=${SECONDS}s bytes=$(stat -c %s /tmp/ss.raw 2>/dev/null)"; head -c 600 /tmp/ss.err; } | curl -s --data-binary @- http://10.0.2.2:8000/capture-info >/dev/null
[ -s /tmp/ss.raw ] && curl -s --data-binary @/tmp/ss.raw http://10.0.2.2:8000/ss-raw >/dev/null
echo captured
