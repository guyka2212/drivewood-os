#!/bin/bash
# Drivewood desktop stage. Run from the live ISO after install-base.sh (target mounted on /mnt):
#   curl -s 10.0.2.2:8000/build/install-desktop.sh | bash
set -euo pipefail
T=/mnt; USERNAME=${USERNAME:-$(ls /mnt/home | head -1)}; SRC=${SRC:-http://10.0.2.2:8000}
LOG=/tmp/drivewood-desktop.log; exec > >(tee "$LOG") 2>&1
trap 'curl -s --data-binary @"$LOG" $SRC/install-desktop-log >/dev/null || true' EXIT
mountpoint -q $T || { echo "/mnt is not mounted (run install-base.sh first)"; exit 1; }

echo "== Drivewood files"
curl -fsS $SRC/build/stage.tar.gz | tar xz --no-same-owner -C $T
chmod 755 $T/usr/bin/drivewood-*
ln -sf ../usr/lib/os-release $T/etc/os-release

echo "== user setup for $USERNAME"
H=$T/home/$USERNAME
cp -rT $T/etc/skel/.config $H/.config
grep -q "# ---- Drivewood ----" $H/.bashrc || cat $T/usr/share/drivewood/bashrc >> $H/.bashrc
grep -q "# ---- Drivewood ----" $T/etc/skel/.bashrc || cat $T/usr/share/drivewood/bashrc >> $T/etc/skel/.bashrc
mkdir -p $H/Pictures/Wallpapers $H/Pictures/Screenshots $H/Downloads $H/Documents $H/.local/state/drivewood
ln -sfn /usr/share/drivewood/backgrounds/2-noon.png $H/.local/state/drivewood/background

echo "== DriveWood Link package"
rm -rf $T/var/tmp/dwlink; mkdir -p $T/var/tmp/dwlink
curl -fsS $SRC/link/drivewood-link-desktop.tar.gz | tar xz --no-same-owner -C $T/var/tmp/dwlink

arch-chroot $T /bin/bash -e <<CHROOT
chown -R $USERNAME:$USERNAME /home/$USERNAME /var/tmp/dwlink
cd /var/tmp/dwlink/packaging && sudo -u $USERNAME makepkg -f --nodeps 2>&1 | tail -3
pacman -U --noconfirm /var/tmp/dwlink/packaging/drivewood-link-*.pkg.tar.zst 2>&1 | tail -3
echo "== Zen Browser (official build)"
rm -rf /var/tmp/dwzen; cp -r /usr/share/drivewood/zen /var/tmp/dwzen; chown -R $USERNAME:$USERNAME /var/tmp/dwzen
cd /var/tmp/dwzen && sudo -u $USERNAME makepkg -f --nodeps 2>&1 | tail -3
pacman -U --noconfirm /var/tmp/dwzen/drivewood-zen-*.pkg.tar.zst 2>&1 | tail -3
cd / && rm -rf /var/tmp/dwzen
cat /usr/share/drivewood/version > /home/$USERNAME/.local/state/drivewood/finished
chown $USERNAME:$USERNAME /home/$USERNAME/.local/state/drivewood/finished
systemctl --global enable drivewood-sky.timer drivewood-update-check.timer
echo "== boot animation"
plymouth-set-default-theme drivewood
mkinitcpio -P 2>&1 | grep -E "error|successful" | tail -2
CHROOT
echo "== desktop stage done"
