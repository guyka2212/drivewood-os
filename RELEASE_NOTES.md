# Drivewood 1.1.7

A fix for Super + Tab.

## Fixed
- **Super + Tab now always switches workspace.** Before, it only jumped between workspaces that had windows on them, so with all your apps on one workspace it did nothing. Now it steps through workspaces 1 to 5 in order, empty ones included, and wraps from 5 back to 1. Super + Shift + Tab goes the other way.

## Good to know
- As always, your files, apps, Settings choices, your own shortcuts and your Link sign-in all stay.
- No new installer this time: the 1.1.2 installer ISO installs Drivewood, and the built-in updater brings it to 1.1.7.

## Files in this release
- `drivewood-update-1.1.7.tar.gz` (+ `.sha256`): used by the built-in updater.
- `drivewood-link.apk`: DriveWood Link for Android.
