# Drivewood 1.1.2

A new browser, a Drivewood boot screen for the installer, and a smarter updater.

## New
- **Zen Browser replaces Chromium.** Super + B, the Browser button in the Super menu and Tidepool now open Zen, and it's the default browser for links. It's Zen's official build (1.24.2b), checked against its SHA-256 before it's installed. New Zen versions come with Drivewood updates.
- **Drivewood boot screen on the installer.** The installer USB's boot menu now shows the Drivewood logo and name instead of Arch Linux's.

## Changed
- **Updating from 1.0.0:** the update installs Zen and makes it your default browser, unless you'd already picked a different one. Chromium is **not** removed, so your bookmarks and logins stay; you can uninstall it yourself in Settings → Apps. New installs come with Zen only.
- **Smarter updater:** after installing the new system files, the updater hands over to the newly installed version for the last steps. That way a release can bring its own install steps (like installing Zen), even when you update from an older version.
- The installer ISO's version number now matches the Drivewood version.

## Fixed
- Typing `drivewood-install` on the installer USB no longer fails with "permission denied".

## Good to know
- Updating to 1.1.2 downloads Zen (about 115 MB), so it takes a few minutes longer than usual and needs an internet connection.
- As before, your files, apps, Settings choices, your own shortcuts and your Link sign-in all stay.
- The installer still needs an internet connection and BIOS/legacy boot.

## Files in this release
- `drivewood-installer.iso` (+ `.sha256`): the installer.
- `drivewood-update-1.1.2.tar.gz` (+ `.sha256`): used by the built-in updater.
- `drivewood-link.apk`: DriveWood Link for Android.
