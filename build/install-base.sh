#!/bin/bash
# Drivewood base installer. Run from the Arch live ISO as root:
#   curl -s 10.0.2.2:8000/build/install-base.sh | bash
# ERASES the whole disk below, installs Arch + every Drivewood package, a user, Limine and
# autologin. The user types their own password (asked once near the end).
set -euo pipefail
DISK=${DISK:-/dev/sda}
if [ -z "${USERNAME:-}" ]; then read -rp "Username for the new system (a-z): " USERNAME </dev/tty; fi
USERNAME=${USERNAME:-user}
HOST=${HOST:-drivewood}
TZONE=${TZONE:-Asia/Jerusalem}
LOG=/tmp/drivewood-install.log
exec > >(tee "$LOG") 2>&1
report() { curl -s --data-binary @"$LOG" http://10.0.2.2:8000/install-base-log >/dev/null || true; }
trap report EXIT

echo "== Drivewood installer: disk $DISK, user $USERNAME, host $HOST"
[ -b "$DISK" ] || { echo "no disk $DISK"; exit 1; }

echo "== partitions (MBR): 1 GiB FAT32 /boot + ext4 /"
umount -R /mnt 2>/dev/null || true
wipefs -af "$DISK"
sfdisk "$DISK" <<EOF
label: dos
,1GiB,c,*
,,83
EOF
sleep 1
P1=${DISK}1; P2=${DISK}2
mkfs.fat -F 32 -n DWBOOT "$P1"
mkfs.ext4 -F -L drivewood "$P2"
mount "$P2" /mnt
mount --mkdir "$P1" /mnt/boot

echo "== packages (this is the long part)"
PKGS=(
  base base-devel linux linux-firmware intel-ucode amd-ucode sudo nano git
  networkmanager bluez bluez-utils zram-generator
  limine plymouth greetd
  hyprland quickshell hyprlock hypridle swaybg xdg-desktop-portal-hyprland xdg-desktop-portal-gtk polkit
  pipewire pipewire-pulse pipewire-alsa wireplumber brightnessctl playerctl
  foot chromium nautilus fastfetch starship imagemagick mako
  python python-gobject python-cairo gtk4 openssl grim slurp wl-clipboard libnotify
  ttf-jetbrains-mono-nerd noto-fonts noto-fonts-emoji papirus-icon-theme
  qt6-wayland qt6-svg qt6-declarative
)
pacman -Sy --noconfirm archlinux-keyring
pacstrap -K /mnt "${PKGS[@]}"

echo "== system config"
genfstab -U /mnt >> /mnt/etc/fstab
ROOT_UUID=$(blkid -s UUID -o value "$P2")
arch-chroot /mnt /bin/bash -e <<CHROOT
ln -sf /usr/share/zoneinfo/$TZONE /etc/localtime
hwclock --systohc
sed -i 's/^#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
locale-gen
echo LANG=en_US.UTF-8 > /etc/locale.conf
echo $HOST > /etc/hostname
printf '127.0.0.1 localhost\n::1 localhost\n127.0.1.1 $HOST.localdomain $HOST\n' > /etc/hosts
printf '[zram0]\nzram-size = ram / 2\n' > /etc/systemd/zram-generator.conf

useradd -m -G wheel,video,input,audio -s /bin/bash $USERNAME
printf 'Defaults lecture=never
%%wheel ALL=(ALL:ALL) ALL
' > /etc/sudoers.d/10-wheel
chmod 440 /etc/sudoers.d/10-wheel
passwd -l root

# boot screen is added by the desktop stage; plymouth hook goes in now
sed -i 's/^HOOKS=.*/HOOKS=(base systemd plymouth autodetect microcode modconf kms keyboard sd-vconsole block filesystems fsck)/' /etc/mkinitcpio.conf
echo 'KEYMAP=us' > /etc/vconsole.conf
mkinitcpio -P

# Limine (BIOS): no menu, no messages, Drivewood branding
mkdir -p /boot/limine
cp /usr/share/limine/limine-bios.sys /boot/limine/
limine bios-install $DISK
cat > /boot/limine/limine.conf <<LIM
timeout: 0
quiet: yes
interface_branding: Drivewood

/Drivewood
    protocol: linux
    path: boot():/vmlinuz-linux
    cmdline: root=UUID=$ROOT_UUID rw quiet splash loglevel=3 rd.udev.log_level=3 vt.global_cursor_default=0 systemd.show_status=false
    module_path: boot():/initramfs-linux.img
LIM

# autologin straight into Hyprland; the lock screen then acts as the login
mkdir -p /etc/greetd
cat > /etc/greetd/config.toml <<GRT
[terminal]
vt = 1
[default_session]
command = "agreety --cmd start-hyprland"
user = "greeter"
[initial_session]
command = "start-hyprland"
user = "$USERNAME"
GRT

systemctl enable NetworkManager bluetooth greetd
CHROOT

echo "== set the password for $USERNAME (type it twice; it's also your sudo password)"
until arch-chroot /mnt passwd "$USERNAME" </dev/tty >/dev/tty 2>&1; do echo "try again"; done

echo "== base install done"
