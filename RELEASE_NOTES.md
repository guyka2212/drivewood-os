# Drivewood 1.1.3

A small fix for the updater: updates no longer stop if you step away.

## Fixed
- **The screen stays awake while Drivewood updates.** Before, if an update waited for your password for more than 5 minutes, the screen locked, the password prompt timed out and nothing was installed. Now the screen doesn't lock or turn off while the update window is open, and it goes back to your normal lock timers as soon as the update is done.
- **A timed-out password prompt can be tried again.** If you still miss the password prompt, the updater asks whether to try again instead of stopping.

## Good to know
- The fix takes effect for the update **after** this one: updating to 1.1.3 still runs your current updater for its first part.
- As always, your files, apps, Settings choices, your own shortcuts and your Link sign-in all stay.
- No new installer this time: the 1.1.2 installer ISO installs Drivewood, and the built-in updater brings it to 1.1.3.

## Files in this release
- `drivewood-update-1.1.3.tar.gz` (+ `.sha256`): used by the built-in updater.
- `drivewood-link.apk`: DriveWood Link for Android.
