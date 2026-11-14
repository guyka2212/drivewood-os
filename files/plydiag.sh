#!/bin/bash
{
echo "### renderers"; ls /usr/lib/plymouth/renderers/ 2>&1
echo "### plugins"; ls /usr/lib/plymouth/ 2>&1 | head -30
echo "### plymouth version"; plymouthd --version 2>&1 | head -2; pacman -Q plymouth 2>&1
echo "### frame files"; file /usr/share/plymouth/themes/driftwood/f000.png /usr/share/plymouth/themes/driftwood/f276.png
ls /usr/share/plymouth/themes/driftwood | wc -l
echo "### mkinitcpio plymouth hook"; cat /usr/lib/initcpio/install/plymouth 2>&1 | head -60
echo "### debug log from last boot?"; ls -la /var/log/plymouth-debug.log /var/log/boot.log 2>&1
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/plydiag
