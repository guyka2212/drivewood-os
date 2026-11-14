# DriveWood Link: decisions (stage 4)

Decided with the user on 2026-11-14 and built the same day. Notes in *italics* say where the build differs from the first plan.

## Where it's built
All source code and builds go in `C:\Users\User\Documents\Drivewood\link\` on the main PC, not in the VM (the VM has only 20 GB). The VM is used only to test the finished Drivewood app.

## Platforms
- **Desktop:** Drivewood only (Linux, Hyprland/Wayland). Comes pre-installed in the OS.
- **Phone:** Android only (Kotlin, built with Android Studio, installed from an APK).

## Account (Supabase project "DriveWood", reached through the Supabase connection)
- Sign-in with Supabase Auth. *Built: email + password (Supabase rejects made-up emails), plus a username chosen at sign-up and shown on devices. Email confirmation is off.* Passwords are handled only by Supabase Auth and never stored in app tables.
- Tables, each with row-level security so a user only sees their own rows:
  - `profiles` (user id, username, accepted Terms/Privacy versions and date)
  - `devices` (device id, owner user id, device name, type: computer or phone, last seen, LAN address, certificate SHA-256)
  - `transfers` (history: who sent what to which device, size, time; no file contents)
- On first sign-in the phone or computer asks for a device name and registers itself.

## Sign-up consent (required)
- The sign-up screen (phone and computer) has a checkbox that is **unticked by default**: "I am at least 13 (16 in the EEA/UK) and I agree to the Terms of Use and the Privacy Policy". Both documents open in the app.
- The account can't be created until the box is ticked. The server rejects the sign-up too if consent is missing, so the checkbox can't be bypassed.
- `profiles` stores `terms_version`, `privacy_version` and `accepted_at`. When either document gets a new version, the app blocks use until the user accepts again (or deletes the account / exports their data).
- Settings → Account has Export data (JSON) and Delete account, as the Privacy Policy promises.
- History older than 90 days is deleted automatically, as the Privacy Policy promises. *Built as the `prune_history` trigger, which runs on every new history row.*
- Texts: `Drivewood/legal/TERMS.md` and `Drivewood/legal/PRIVACY.md` (version 1.0).

## Sending (LocalSend-style)
- Files, folders, text and links between your own devices on the same Wi-Fi.
- Devices find each other on the LAN (*built: UDP broadcast on port 47801; transfers and control on TCP 47800*). Files go **directly device-to-device** over an encrypted connection (TLS with the device keys) and are byte-identical: no compression, no quality loss. A checksum is verified after each file.
- Supabase only holds accounts, the device list and history. File contents never go through it.

## Take control
- **Only computers can take control.** A Drivewood computer can control another Drivewood computer or one of your Android phones.
- You see the other device's screen live and control it:
  - Computer → computer: mouse and keyboard.
  - Computer → phone: the mouse acts as touch, plus the keyboard.
- Underneath:
  - Linux target: *built with `grim` JPEG frames (about 12 per second) instead of the portal, and input written straight to `/dev/uinput`, which a udev rule opens for the logged-in user.*
  - Android target: MediaProjection for the screen, an Accessibility service for touch. The phone owner turns on the accessibility service once, accepts Android's screen-capture prompt each session, and sees a "being controlled" banner that can stop it at any time.
- Only devices signed in to the same account can connect, and the target must accept each session.

## Extra features
- Shared clipboard (off by default), transfer history, drag-and-drop onto a device, and the Android share menu. *Not built yet: a "Send to Link" item in the Files app's right-click menu.*
- *Added later:* a refresh button, nearby / online-elsewhere / offline states, Remove this device, a floating window on Drivewood, the sea-glass theme and animations.

## In the OS (stage 5)
- Pre-installed: Link app in Shoreline and the Tide favourites (*Link replaced Tidepool there*), a background service started with the session, the floating-window rules, and a "Link" page in the new Settings app.
