#!/bin/bash
# Remove the temporary plymouth.debug boot flag and its log.
sudo bash <<'ROOT'
L=/boot/limine.conf
sed -i 's/ plymouth\.debug//g' "$L"
rm -f /var/log/plymouth-debug.log
echo "plymouth.debug left in limine.conf: $(grep -c 'plymouth.debug' "$L")"
grep -n -E "^(timeout|quiet):" "$L"
ROOT
