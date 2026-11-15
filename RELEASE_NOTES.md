# Drivewood 1.0.0 — the first release

Drivewood is a calm, fully custom desktop operating system built on **Arch Linux** and **Hyprland**, with its own shell, theme, settings app and a cross-device app, **DriveWood Link**. This is the first public release.

## Install
1. Download **`drivewood-installer.iso`** below and write it to a USB stick (for example with Ventoy, balenaEtcher or Rufus), or boot it in a virtual machine.
2. Boot from it and type **`drivewood-install`**.
3. Pick the disk, type `yes`, choose a username, and type your password when asked. Drivewood downloads its packages during the install, so you need an internet connection (wired works right away; for Wi-Fi run `iwctl` first).
4. Restart, remove the USB stick, and you're in.

> ⚠️ The installer **erases the whole disk you pick**. It currently supports BIOS (legacy) boot; UEFI-only computers need legacy/CSM boot turned on.

## What's in Drivewood 1.0.0

### Boot and sign-in
- The **DRIVEWOOD rain animation** plays while the computer starts: no boot menu, no scrolling text.
- The Drivewood **lock screen doubles as the sign-in**: blurred wallpaper, logo, clock and date.
- The screen locks after 5 minutes and turns off after 6 (both changeable in Settings → Power).

### Desktop
- **Pixel-art lake and mountain skies** for dawn, midday, dusk and night that **follow the real time of day**.
- **Colours follow the wallpaper**: the bar, menus and window borders take their accent colours from whatever wallpaper you pick.
- **The bar:** workspaces, window title, clock and date, CPU and memory, volume and power, with a horizon line in the wallpaper's colours.
- **The Super menu:** tap **Super** on its own for a greeting, search across apps and actions, favourites (Terminal, Browser, Files, Landscape, Link, Studio, Apps), and quick actions for the wallpaper and Settings.
- **All apps:** Super + Alt + Space.
- Gentle animations: windows pop in, workspaces glide, unfocused windows dim slightly.
- A matching terminal with a sky-blue prompt and a time-of-day greeting.

### Drivewood Settings (new, built from scratch)
One window, 14 pages, opened with **Super + I**:
- **Display:** resolution, refresh rate and scale for each screen.
- **Input:** key repeat, pointer speed, natural scrolling, tap to click.
- **Keybindings:** a searchable list of every shortcut.
- **Language:** up to four keyboard layouts (including Hebrew) and the key that switches them, plus the system language.
- **Network:** Wi-Fi networks and connecting, Bluetooth on/off, connecting and pairing.
- **Sound:** volume, mute, and choosing output and input devices.
- **Appearance:** wallpaper grid, "choose a picture", sky follows the clock, gaps, corners, dimming, animations.
- **Apps:** search Arch Linux's packages and install or remove them, plus Drivewood picks (VLC, GIMP, LibreOffice, OBS, Steam).
- **Update**, **Power**, **Users** (computer name, password), **Date & time** (time zone search, automatic time), **Link** and **About**.
Anything that needs administrator rights opens a terminal for your own password — the app never stores it.

### DriveWood Link (new)
Send files and text between your own computers and Android phones over Wi-Fi, and take control of them.
- **Full quality:** files go directly between your devices, encrypted, byte-for-byte identical (checked with SHA-256). They never pass through the internet.
- **Take control:** a Drivewood computer can control another Drivewood computer (mouse and keyboard) or your Android phone (the mouse acts as touch). The other device always has to accept, and a banner with a **Stop** button stays on screen the whole time.
- **Devices:** see which devices are nearby (ready to send), online on another network, or offline.
- Shared clipboard (off by default), transfer history, drag-and-drop onto a device, and "Share → DriveWood Link" on Android.
- **Your account:** sign up with email, username and password. You must accept the Terms of Use and Privacy Policy (unticked box, checked again by the server). Export your data or delete your account at any time.
- Comes pre-installed and starts in the background. The Android app (APK) is attached below.

### Apps included
- **Chromium** (browser), **Files**, the **foot** terminal.
- **Landscape:** an endless landscape drifting through your terminal (Super + Alt + D).
- **Tidepool:** artificial life from a few simple rules (Super + Alt + T).
- **Android Studio** can be installed from the instructions (`files/studio.sh`).

### Updates
- Drivewood checks GitHub for new releases 2 minutes after you sign in and every 6 hours after that.
- When there's an update, a small **down arrow** appears in the bar next to the CPU and memory bars. Click it, read what's new, confirm, and type your password once.
- **Updates never remove or change your own things:** your files, apps, Settings choices, your own shortcuts (`~/.config/hypr/custom.lua`) and your Link sign-in all stay.

## Keyboard shortcuts
| Keys | Action |
|---|---|
| Super (tap) | Drivewood menu |
| Super + Alt + Space | All apps |
| Super + Return | Terminal |
| Super + B / E | Browser / Files |
| Super + I | Settings |
| Super + W (or Q) | Close window |
| Super + L | Lock |
| Super + V / F | Float / full screen |
| Super + 1…0 | Workspaces (Shift to move a window) |
| Super + drag | Move a window (right-drag to resize) |
| Print / Shift + Print | Screenshot of an area / the screen |
| Super + Alt + L / D / T | Link / Landscape / Tidepool |

## Files in this release
- `drivewood-installer.iso` (+ `.sha256`): the installer.
- `drivewood-update-1.0.0.tar.gz` (+ `.sha256`): used by the built-in updater.
- `drivewood-link.apk`: DriveWood Link for Android.

## Known limitations
- The installer needs an internet connection and BIOS/legacy boot.
- In virtual machines, apps open slowly the first time (software graphics), and there's usually no Wi-Fi or sound card.
- DriveWood Link needs both devices on the same Wi-Fi network to send files or take control.

## Licence
Drivewood is open source under **GPL-3.0**.
