# Drivewood

A calm, fully custom desktop operating system built on **Arch Linux + Hyprland**.

- **Boot:** the DRIVEWOOD rain animation, no boot menu or messages, then a lock screen that doubles as the sign-in.
- **Desktop:** pixel-art lake and mountain skies that follow the time of day; bar, window borders and menus take their colours from the wallpaper.
- **Super menu:** tap Super for a greeting, search, favourites and quick actions. Super+Alt+Space opens every app.
- **Drivewood Settings:** 14 pages (display, input, keybindings, language, network, sound, appearance, apps, update, power, users, date & time, Link, about).
- **DriveWood Link:** send files and text between your own computers and Android phones over Wi-Fi at full quality, and take control of them. Desktop (Python/GTK 4) and Android (Kotlin) apps, accounts on Supabase.
- **Updates:** a small down arrow appears in the bar when a new release is out; one click updates Drivewood and keeps all your files and settings.

## Install
Boot the Arch Linux ISO, then follow `INSTRUCTIONS.md` (stage 5): `build/install-base.sh` and `build/install-desktop.sh` install everything. A `drivewood-installer.iso` comes with the first release.

## Repository layout
| Folder | What's inside |
|---|---|
| `build/` | The Drivewood build: installers, shell, configs, Settings app, update tools, release script |
| `link/` | DriveWood Link: `desktop/` (Python + GTK 4, Arch package) and `android/` (Kotlin app) |
| `legal/` | DriveWood Link Terms of Use and Privacy Policy |
| `files/` | The first prototype (built on Omarchy), kept for reference |
| `apps/` | Landscape (terminal landscape) and Tidepool (particle life) |
| `INSTRUCTIONS.md` | Everything about how Drivewood is built, with every script and example |

## Releases and updates
Each release on GitHub has a `drivewood-update-<version>.tar.gz` (+ `.sha256`). Installed systems check for it every 6 hours (`drivewood-update-check`) and show the arrow; `drivewood-update` verifies the checksum and installs it.

## Licence
GPL-3.0. See `LICENSE`. The names "Drivewood" and "DriveWood" and the logo identify this project; forks should use their own name.
