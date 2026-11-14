# Drivewood Settings (from scratch, new build only)

The new Drivewood build gets its own settings app instead of patching Omarchy's menu.
It is a Quickshell window in the Drivewood shell, styled like Tide and Shoreline
(colours from the wallpaper palette). Nothing in it calls omarchy-* scripts.
It uses plain Arch tools only: hyprctl, nmcli, bluetoothctl, wpctl, timedatectl, localectl, pacman/yay, fwupdmgr, passwd.

Open it with:
- the "All settings" button in the Super menu
- the `all-settings` command (`all-settings network` jumps to one page)
- SUPER + SHIFT + Copilot key

## Pages

| Page | What it does | Tool underneath |
|---|---|---|
| Display | Resolution, refresh rate, scale, arrangement, night light | hyprctl keyword monitor, hyprsunset |
| Input | Keyboard repeat rate/delay, mouse and touchpad speed, natural scroll, tap to click | hyprctl keyword input:* (saved to a Drivewood input.lua) |
| Keybindings | Searchable list of every shortcut, edit or add your own | hyprctl binds -j, ~/.config/hypr/bindings.lua |
| Language | System language, keyboard layouts and switch key | localectl, hyprctl keyword input:kb_layout |
| Network | Wi-Fi list and connect, wired status, VPN, Bluetooth devices | nmcli, bluetoothctl |
| Sound | Output/input device, volume, mute | wpctl |
| Appearance | Wallpaper, "sky follows the clock", font, gaps, corners, opacity, animations | driftwood-sky, driftwood-palette, hyprctl |
| Apps | Search, install and remove apps (official repos + AUR), with Drivewood's own list of picks | pacman, yay |
| Update | Update the system, firmware updates, last update time | pacman -Syu (in a terminal), fwupdmgr |
| Power | Screen-off and lock timers, suspend, battery | hypridle config, systemctl |
| Users | Change password, user name, avatar | passwd (typed by the user in a terminal), chfn |
| Date & time | Time zone, automatic time, 12/24 h clock | timedatectl |
| Link | DriveWood Link sign-in and device name (after stage 4) | DriveWood Link app |
| About | Drivewood version, hardware, landscape logo | fastfetch with the Drivewood config |

## Rules
- No Omarchy text, logos, links or commands anywhere in the app.
- Anything that needs a password opens a terminal where the user types it; the app never stores it.
- Each page writes its own small file under ~/.config/drivewood/, so a page can be reset without touching the others.
