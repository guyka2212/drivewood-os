#!/bin/bash
{ echo "### firmware"; [ -d /sys/firmware/efi ] && echo UEFI || echo BIOS
  echo "### disks"; lsblk -dno NAME,SIZE,TYPE
  echo "### net"; ip -4 -br a | grep -v lo
  echo "### mem"; free -m | head -2
  pacman -Sy --noconfirm >/dev/null 2>&1
  echo "### packages"
  for p in hyprland quickshell hyprlock hypridle hyprpaper swaybg foot chromium nautilus plymouth limine greetd greetd-tuigreet sddm fastfetch starship imagemagick python-gobject gtk4 grim slurp wl-clipboard libnotify mako ttf-jetbrains-mono-nerd pipewire wireplumber xdg-desktop-portal-hyprland networkmanager brightnessctl playerctl uwsm yaru-icon-theme papirus-icon-theme python-cairo; do
    v=$(pacman -Si "$p" 2>/dev/null | awk -F': ' '/^Version/{print $2; exit}'); echo "$p ${v:-NOT-FOUND}"; done
} 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/probe >/dev/null; echo sent
