#!/bin/bash
# Turn on Plymouth's boot-time debug log for the next boot (adds plymouth.debug to the kernel line).
sudo bash <<'ROOT'
L=/boot/limine.conf
cp -a "$L" /etc/driftwood-backup/limine.conf.before-debug
if ! grep -q "plymouth.debug" "$L"; then
  sed -i -E '/^[[:space:]]*(cmdline|kernel_cmdline):/ s/$/ plymouth.debug/' "$L"
fi
grep -n -E "cmdline" "$L" | cut -c1-80; grep -c "plymouth.debug" "$L"
ROOT
echo "ready - reboot next"
