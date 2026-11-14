#!/bin/bash
# Play the installed boot theme live in an X11 window with debug logging, then report.
LOG=/tmp/ply-debug.log
sudo rm -f "$LOG"
sudo env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" plymouthd --debug --debug-file="$LOG" --mode=boot --tty=/dev/tty5
sleep 1
sudo env DISPLAY="$DISPLAY" plymouth show-splash
sleep 8
sudo env DISPLAY="$DISPLAY" plymouth quit
sleep 1
{
  echo "### renderer / script lines"
  sudo grep -i -E "renderer|script|could not|fail|error|warn|png|image" "$LOG" | grep -v -i "keyboard" | head -60
  echo "### tail"; sudo tail -25 "$LOG"
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/plytest
echo reported
