# Drivewood: how it was built

Drivewood is a fully custom desktop built on Arch Linux + Hyprland. On the first VM it was
layered on top of Omarchy 4.5. This file records everything that was done, every script,
and examples, so the whole OS can be rebuilt from an empty Arch install
(stage 5) and turned into `drivewood-installer.iso` (stage 6).

---

## 1. What is in this folder

```
Drivewood/
├── INSTRUCTIONS.md        this file
├── legal/                 TERMS.md + PRIVACY.md for DriveWood Link (version 1.0, placeholders to fill)
├── link/                  DriveWood Link: desktop app, Android app, VM install scripts (section 7)
├── apps/
│   ├── driftwood/         "Landscape": endless terminal landscape (Python, works on Linux and Windows)
│   └── tidepool/          "Tidepool": particle-life simulation (one HTML file)
└── files/                 everything that was installed on the VM
    ├── bridge.py          tiny file server used to move files into the VM
    ├── dshell/            the custom desktop shell (Quickshell / QML)
    │   ├── shell.qml        entry point + IPC (menu / apps / close / debug)
    │   ├── Theme.qml        colours from the wallpaper, helpers, app list
    │   ├── Bar.qml          "Driftline" top bar
    │   ├── Tide.qml         "Tide" Super menu
    │   └── Shoreline.qml    "Shoreline" Apps window
    ├── driftwood/         the Drivewood theme (colours, wallpapers, logo, lock colours)
    ├── os/                system pieces (scripts, configs, menu overrides, specs)
    ├── plymouth/
    │   └── driftwood-boot/  the boot animation (297 frames + Plymouth script)
    ├── plugin/            early bar-button plugin (replaced by dshell, kept for reference)
    ├── make_*.py          generators for the theme, logo, icons and boot animation
    ├── render_frames.py   turns the recorded screensaver into PNG frames
    ├── capture.sh         records the screensaver animation inside the VM
    └── *.sh               install scripts, in the order listed in section 4
```

---

## 2. Rules that were followed

- **Passwords are never typed by Claude.** Every script that needs root runs `sudo` once and the
  user types the password at the prompt. The disk password at boot is typed by the user too.
- **Backups before changes.** User files go to `~/.config/omarchy-backup-pre-driftwood/`,
  system files to `/etc/driftwood-backup/`.
- **No orange or purple.** Accent colours come from the wallpaper (sky blue / cyan family). DriveWood Link has its own fixed sea-glass theme (teal). The palette's `orange = "#f2a97a"` in `colors.toml` is only the terminal's ANSI orange slot; it isn't used by the desktop.
- **No Omarchy text visible anywhere**: boot, login, lock, bar, menus, About, fastfetch, keybinding labels.
- **Supabase**: the DriveWood Link app (stage 4) uses the Supabase project "DriveWood" through
  Supabase Auth. Passwords are never stored in a table by the app.

---

## 3. How files get into the VM (the bridge)

Typing long commands into the VM gets garbled, so all work was done with tiny commands that
download a script from the host and run it.

On the Windows host (serve the whole Drivewood folder):
```bash
python C:/Users/User/Documents/Drivewood/files/bridge.py "C:/Users/User/Documents/Drivewood"
```
- `GET` serves the folder on `127.0.0.1:8000`. Inside the VM (QEMU user networking) that is `10.0.2.2:8000`.
- With the whole folder served, OS scripts are under `/files/` and Link scripts under `/link/`, for example `curl -s 10.0.2.2:8000/files/menufix.sh|bash` or `curl -s 10.0.2.2:8000/link/vm-update.sh|bash`. During the first build the bridge served `files/` directly, which is why the table below shows `curl -s 10.0.2.2:8000/<script>`.
- Keep the bridge running in the background while working. If it's restarted with a wrong (relative) folder, every request returns an HTML 404 page, and `bash` then fails with `syntax error near unexpected token newline`.
- `POST` saves the request body into `inbox/<name>.txt` next to bridge.py, which is how scripts send logs back.

Inside the VM:
```bash
curl -s 10.0.2.2:8000/install.sh|bash
```
Send a log back from a script:
```bash
some-command 2>&1 | curl -s --data-binary @- http://10.0.2.2:8000/my-log
```
Things to watch out for:
- The screensaver starts after 150 s idle and steals keystrokes (Esc closes it).
- The lock screen appears after 300 s and needs the user's password.
- Typed text sometimes loses its first letters (`lear` instead of `clear`) or repeats characters. Keep commands short, avoid chaining with `;`, and check the line before pressing Enter (Ctrl+U clears it).
- A newly opened window (for example DriveWood Link) takes keyboard focus. Click the terminal before typing, or the command lands in the app.
- The first VM's pacman database was never downloaded (`database file for 'core' does not exist`). Don't add packages that need a download on that VM; the new build runs `pacman -Syu` during install.

---

## 4. What was done, in order

Every script is in `files/`. Run each one in the VM as `curl -s 10.0.2.2:8000/<script>|bash`.

| # | Script | What it does |
|---|---|---|
| 1 | `install.sh` | Backs up branding/bindings, installs the theme (colours, 4 wallpapers, logo), screensaver and About text, launchers for Landscape and Tidepool, SUPER+ALT+D / SUPER+ALT+T, rounded corners, applies the theme. |
| 2 | `install2.sh` | Lock-screen colours, Starship prompt (`os/starship.toml`), time-of-day sky timer, terminal greeting, window motion (popin/slidefade, gaps, dimming). |
| 3 | `install3.sh` | App icons for Landscape and Tidepool, updated sky script. |
| 4 | `install4.sh` | Logo for boot and lock, editor colours generated from the palette, glassy bar, first Super-tap attempt, gradient borders. |
| 5 | `system.sh` | **sudo once.** Bar button plugin (later replaced), first Plymouth splash, `/etc/os-release` name, initramfs rebuild, Limine branding. |
| 6 | `superfix.sh` | Final Super-tap binding (`os/super-tap.lua`): tap Super alone opens the menu, Super+key shortcuts still work. |
| 7 | `wire.sh` | Makes the custom shell the desktop: Super tap → Tide, SUPER+ALT+SPACE → Shoreline, autostart `qs`, hides the stock bar. |
| 8 | `palette-install.sh`, `palette2.sh` | Colours that follow the wallpaper (`os/driftwood-palette`), sky/cyan accents, border colour written to a toggle file. |
| 9 | `capture.sh` → `render_frames.py` → `make_boot_theme.py` | Records the screensaver matrix animation with ttfx, renders 297 PNG frames, builds the Plymouth script. |
| 10 | `boot.sh` | **sudo once.** Installs the boot animation, rebuilds the boot image, Limine `timeout: 0` and `quiet: yes`. |
| 11 | `studio.sh` | Android Studio from Google's official archive (SHA-256 checked) into `~/.local/opt`, with a desktop entry. |
| 12 | `rename.sh` | **sudo once.** Rename to **Drivewood**: theme folder, logo, os-release, boot animation with the DRIVEWOOD word, login logo, Limine `interface_branding: Drivewood`. |
| 13 | `menufix.sh` | Menu overrides (`os/omarchy-menu.jsonc`): hides Plugins, trims Setup to Monitors/Keybindings/Input/Language/Network, hides every Omarchy/preinstalled-theme item. |
| 14 | `aboutfix.sh` | About opens a Drivewood fastfetch (`os/fastfetch.jsonc`): sky-blue landscape logo, no channel or branch lines. |
| 15 | `settingsfix.sh` | `all-settings` command (`os/all-settings`), kernel line shows "Linux x.y.z Drivewood", Super/menu buttons use `all-settings`. |
| 16 | `labelfix.sh` | Relabels the last "Omarchy menu" keybinding (Copilot key) to "Drivewood menu". |
| 17 | `link/vm-lockfix.sh` | Lock-screen password box border from orange to sky blue (`driftwood/shell.lock.toml` → `border-active = "#8fb4e6"`), then re-applies the theme. |
| 18 | `link/vm-colours.sh` | Last orange removed: prompt arrow and repo name (`os/starship.toml`) and the terminal greeting icon (`~/.bashrc`) are sky blue. `install2.sh` and `os/os-release` (`ANSI_COLOR`) were fixed at the source too. |
| 19 | `link/vm-install.sh` | **sudo once.** Builds and installs the DriveWood Link package (`makepkg -si`) and makes the greeting sky blue. |
| 20 | `link/vm-update.sh` | **sudo once.** Installs the Link floating-window rules, rebuilds and reinstalls the newest Link package, and reopens the app. Run it after every Link change. |
| 21 | `link/vm-tide.sh` | Super menu favourite Tidepool → **Link**, and the system menu's Drivewood section Tidepool → DriveWood Link. Restarts the shell. |

Link helpers: `link/vm-try.sh` runs the newest Link code from `~/.cache` without reinstalling, `link/vm-rulefix.sh` re-applies only the window rules, and `link/vm-check.sh` / `vm-rules.sh` / `vm-rules2.sh` report installed packages and Hyprland window-rule examples back through the bridge.

Diagnostic helpers, kept for debugging: `plydebug-on.sh`/`plydebug-off.sh` (Plymouth debug log at boot),
`plydiag.sh`, `plytest.sh` (live Plymouth test), `menudump.sh`/`menudump2.sh` (dump the shipped menu),
`findlabel.sh` (find keybinding labels).

---

## 5. The pieces, explained

### 5.1 Theme (`files/driftwood/`)
- `colors.toml`: palette. Main accent `#8fb4e6` (sky), second accent `#6ac8dc` (cyan).
- `backgrounds/1-dawn.png 2-noon.png 3-dusk.png 4-night.png`: pixel-art lake and mountains at four times of day.
- `unlock.png`: the DRIVEWOOD logo, used on the boot splash, lock screen and login screen.
- `shell.toml`, `shell.lock.toml`: bar and lock-screen colours (the lock box border is `#8fb4e6`). `icons.theme`: `Yaru-wartybrown-dark`.
- `os/starship.toml`: the prompt (pine icon, folder, git, slow-command timer, sky-blue `❯`).
- Generated by `make_theme.py` (wallpapers, colours) and `make_logo.py` (block-letter logo; the FONT table holds the letters).

Example: regenerate the logo after changing the word:
```bash
python files/make_logo.py
```

### 5.2 Wallpaper follows the clock (`os/driftwood-sky` + `.service` + `.timer`)
- Periods: dawn 05–08, midday 08–17, dusk 17–20, night 20–05.
- A user systemd timer runs it every 5 minutes. It only switches when a new period starts, so a wallpaper you pick yourself stays until then.
- It only acts while the `drivewood` theme is active.
```bash
~/.local/bin/driftwood-sky --force     # jump to the right sky now
systemctl --user list-timers driftwood-sky.timer
```

### 5.3 Colours from the wallpaper (`os/driftwood-palette`)
- Reduces the wallpaper to 8 colours with ImageMagick.
- Picks the accent by area × saturation^0.6. accent2 is the accent with its hue shifted by −0.06. The background comes from the darkest colour.
- Writes `~/.local/state/driftwood/palette.json` (read live by the shell).
- Writes `~/.local/state/omarchy/toggles/hypr/driftwood-border.lua` (window border gradient) and runs `hyprctl reload`.
- The shell watches the background symlink and reruns it whenever the wallpaper changes.
```bash
driftwood-palette                      # from the current wallpaper
driftwood-palette ~/Pictures/x.png     # from any image
cat ~/.local/state/driftwood/palette.json
```

### 5.4 The custom shell (`files/dshell/`, deployed to `~/.config/driftwood-shell`)
Runs on Quickshell 0.3.2:
```bash
qs -n -p ~/.config/driftwood-shell
qs -p ~/.config/driftwood-shell ipc call driftwood menu    # toggle Tide
qs -p ~/.config/driftwood-shell ipc call driftwood apps    # toggle Shoreline
qs -p ~/.config/driftwood-shell ipc call driftwood close
```
- **Driftline (Bar.qml):** floating pill with workspaces, window title, clock (HH:mm + date), CPU/RAM/volume, power button, and a time-of-day horizon line.
- **Tide (Tide.qml):** the Super menu.
  - A greeting and search across apps and actions.
  - Favourites: Terminal, Browser, Files, Landscape, **Link** (DriveWood Link, replaced Tidepool), Studio, Apps. Tidepool is still installed and in the Apps window. The All settings → Drivewood submenu also lists DriveWood Link instead of Tidepool.
  - Quick actions: Next wallpaper, Sky to clock, All settings.
  - Text-only power buttons. The hint reads "press Super to close".
- **Shoreline (Shoreline.qml):** full Apps window with search, no title text.
- **Theme.qml:** live colours from palette.json, `run()` / `quote()` helpers, and the app list. It loads DesktopEntries lazily and hides entries listed by Omarchy's `shell/services/hidden-entries.sh`. The new build needs its own small replacement for this script.

Restart the shell after changing a QML file:
```bash
pkill -f "qs -n -p $HOME/.config/driftwood-shell"; setsid -f qs -n -p "$HOME/.config/driftwood-shell"
```

### 5.5 Keys (`~/.config/hypr/bindings.lua`)
- Tap **Super** alone → Tide. It's a plain `release = true` bind, which Hyprland cancels if another key is pressed while Super is held (`os/super-tap.lua`).
- **SUPER+ALT+SPACE** → Shoreline. **SUPER+ALT+D** → Landscape. **SUPER+ALT+T** → Tidepool.
- Things that did NOT work: `ignore_mods` and `transparent` on the Super bind.

Live config overrides go in `~/.local/state/omarchy/toggles/hypr/*.lua`, followed by `hyprctl reload`.

### 5.6 Boot (no Omarchy text, animated DRIVEWOOD)
1. `capture.sh`: records ttfx's matrix effect on `screensaver.txt` (110×18, seed 7, rain-time 3, sky/cyan gradient).
2. `render_frames.py raw out/ 2`: draws every 2nd frame as a 1100×360 PNG.
3. `make_boot_theme.py`: writes `driftwood.script` (plays frames at 30 fps, then holds the word with a pulse), `driftwood.plymouth` and `files.txt`.
4. Install to `/usr/share/plymouth/themes/driftwood`, then `plymouth-set-default-theme driftwood` and `limine-mkinitcpio`.
5. Limine `/boot/limine.conf`: `timeout: 0`, `quiet: yes`, `interface_branding: Drivewood`.

Note: the SeaBIOS/iPXE text at power-on comes from the VM firmware, not the OS, so it can't be changed from inside.
An early mistake: the boot screen looked black because the slow shutdown (~90 s) plus a fast boot hid it. It was confirmed working with `plydebug-on.sh`.

### 5.7 Name and About
- `os/os-release`: `NAME="Drivewood"`, `PRETTY_NAME="Drivewood"`. In the new build, also change `ID`, URLs and `LOGO`, which still point at Omarchy here.
- `os/fastfetch.jsonc` → `~/.config/fastfetch/config.jsonc`: landscape logo (`about.txt`) in sky blue, "Drivewood <version>", "Linux <kernel> Drivewood".
- `about.txt` / `screensaver.txt`: the landscape and the DRIVEWOOD banner (88 columns wide).

### 5.8 Menus (`os/omarchy-menu.jsonc` → `~/.config/omarchy/extensions/`)
- An entry with the same id overrides the shipped one **completely** (copy icon and label too). `"when": "false"` hides it.
- The parser only strips **whole-line** `//` comments, so never put a comment after a value.
- Shipped menu: `/usr/share/omarchy/default/omarchy/omarchy-menu.jsonc`. Labels: `default/i18n/en/menu.json`. The full audit tree is in `os/menu-tree.txt`.
- `all-settings` (`os/all-settings`) wraps the menu:
```bash
all-settings            # main menu
all-settings setup      # one section: setup, appearance, install, remove, update, learn, trigger
```

### 5.9 Apps
- **Landscape** (`apps/driftwood/driftwood.py`): `python driftwood.py`. Works on Linux (termios) and Windows (msvcrt).
- **Tidepool** (`apps/tidepool/index.html`): open in a browser. In the OS it runs as `drivewood-tidepool`, which opens `/usr/share/drivewood/apps/tidepool/index.html` in a Zen window.
- **Android Studio**: `studio.sh` (official Google archive, checksum verified, `~/.local/opt/android-studio`).

---

## 6. Undo (on the first VM)

```bash
omarchy-theme-set "$(cat ~/.config/omarchy-backup-pre-driftwood/previous-theme.txt)"
cp ~/.config/omarchy-backup-pre-driftwood/hypr/*.lua ~/.config/hypr/
rm ~/.config/omarchy/extensions/omarchy-menu.jsonc
omarchy-toggle-bar off
```
Then remove the `qs` line from `~/.config/hypr/autostart.lua`.

System files: `sudo cp /etc/driftwood-backup/os-release /etc/os-release`, restore `limine.conf` from the same folder, then run `plymouth-set-default-theme omarchy && sudo limine-mkinitcpio`.

---

## 7. Next stages

### Stage 4: DriveWood Link (done)
Decisions are in `files/os/link-spec.md`: Drivewood desktop + Android, take control only from computers. It comes **pre-installed** in the new build.
A LocalSend-style app for desktop and phone:
- Send files and text over Wi-Fi at full quality.
- A device list with "take control".
- Sign-in through Supabase Auth on the "DriveWood" project. Profiles, devices and device names live in tables protected by row-level security.
- Phone app: sign in → pick a device name → features.

#### DriveWood Link: user guide

**What it does**
- **Send:** files, folders, text and links to any of your devices on the same Wi-Fi. They arrive byte-for-byte identical (no compression) and are checked with a checksum.
- **Devices:** a list of your computers and phones, each in one of three states:
  - **Nearby** (teal, pulsing dot): announced itself on this network in the last 12 seconds. Files, Text and Take control are enabled.
  - **Online, on another network** (sand dot): checked in with Supabase in the last 2.5 minutes (each device checks in every 60 seconds), but isn't on this Wi-Fi. A VM behind QEMU's private network, or a phone on mobile data, shows like this.
  - **Offline** (grey dot): the app isn't running there.
- **Take control (computers only):** watch and control another computer (mouse + keyboard) or your Android phone (the mouse acts as touch) live over Wi-Fi.
- **Shared clipboard:** copy on one device, paste on another.
- **History:** what was sent, when, and to which device.

**How it's added to Drivewood (pre-installed)**
| Part | Where |
|---|---|
| App | `/usr/lib/drivewood-link/` with a `drivewood-link` command in `/usr/bin` |
| Background service | `drivewood-link.service` (systemd user service, starts with the session) |
| Launcher | `drivewood-link.desktop`, shown in Shoreline and the Tide favourites |
| Settings | new build: a "Link" page in Drivewood Settings that opens the app (planned in `files/os/settings-spec.md`) |
| Super menu | **Link** favourite (`cmd: "drivewood-link"` in `dshell/Tide.qml`) and the `driftwood.link` entry in `os/omarchy-menu.jsonc` |
| Firewall | TCP 47800 (transfers + control), UDP 47801 (finding devices on the LAN) |
| Window rules | `link/desktop/packaging/drivewood-link-windows.lua` → `~/.local/state/omarchy/toggles/hypr/drivewood-link.lua` (new build: the Drivewood Hyprland config). The app opens as a centred 540×600 floating window. Sign-in and sign-up are inside it. Terms, Privacy, "Text to…" and "Controlling…" open as their own floating windows. Write the patterns without backslashes (`^org.drivewood.Link$`), because a `\.` inside a Lua string is an error. |

**Source code (all on the main PC, in `Drivewood/link/`)**
```
link/
├── desktop/
│   ├── drivewood_link/        the Drivewood app (Python 3 + GTK 4)
│   │   ├── config.py            Supabase URL/key, ports, legal versions
│   │   ├── supa.py              sign-up/sign-in/refresh + REST (standard library only)
│   │   ├── net.py               wire format, device certificate, LAN discovery
│   │   ├── core.py              server, sending, take control, history, export, delete
│   │   ├── control.py           being controlled: grim frames + virtual mouse/keyboard (uinput)
│   │   ├── ui.py                the window (sign-in, sign-up with consent, devices, history, account)
│   │   └── legal/               TERMS.md + PRIVACY.md shown in the app
│   └── packaging/             PKGBUILD, .install hooks, launcher, systemd user service, udev rule,
│                              uinput module file, icon (svg), drivewood-link-windows.lua (Hyprland rules)
├── android/                   the phone app (Kotlin, no extra libraries)
│   └── app/src/main/java/org/drivewood/link/
│       Supa.kt, Net.kt, LinkService.kt, ControlAccessibilityService.kt, MainActivity.kt, Activities.kt, Ui.kt
│       (+ AndroidManifest.xml, res/xml/accessibility.xml, assets/TERMS.md + PRIVACY.md)
├── drivewood-link-desktop.tar.gz   desktop app + packaging, used by the vm-*.sh scripts
└── vm-*.sh                    VM install/update scripts (steps 17–21 in section 4)
```

**How it works**
- **Wire format** (same on both): a 4-byte length, a JSON header, then the raw bytes. Message types: `hello`, `text`, `clip`, `file`, `control`, `frame`, `input`, `bye`.
- **Security on every connection:**
  1. TLS, with the other device's certificate **pinned** to the SHA-256 it registered in Supabase.
  2. The connecting device proves it's signed in to the **same account**: the receiver checks its access token with Supabase and makes sure the device id belongs to that account.
- **Files** are sent with a SHA-256 checksum. The receiver keeps the file only if the checksum matches. Files land in `~/Downloads/DriveWood Link` (computer) or `Download/DriveWood Link` (phone).
- **Take control:**
  - Only a computer can start it.
  - The target is always asked first. On the phone that's a full-screen prompt, and Android's own screen-capture consent each time.
  - While it runs, a banner with **Stop** stays on screen.
  - Drivewood target: frames from `grim` (about 12 per second), mouse and keyboard through a virtual device.
  - Phone target: frames from MediaProjection. Clicks and drags become touches, the right button is Back, the middle button is Home, and typing goes into the focused text field through the accessibility service.
- **Supabase project "DriveWood":**
  - Tables `profiles`, `devices`, `transfers`, all with row-level security.
  - Trigger `handle_new_user` refuses any sign-up without consent and the current document versions.
  - Functions `accept_legal`, `delete_my_account` and `legal_versions`, plus `prune_history`, which deletes history older than 90 days.
- **Where the connection details live:** project URL `https://vknultzvokyblinqsxxs.supabase.co` (region ap-northeast-1, Tokyo) and the publishable key are in `desktop/drivewood_link/config.py` and `android/.../Supa.kt` (`Config`). The publishable key is meant to ship inside apps; row-level security protects the data. The database password is never used by the apps.
- **Changing the Terms or Privacy Policy:** edit `legal/*.md`, copy them to `desktop/drivewood_link/legal/` and `android/app/src/main/assets/`, raise the version in `public.legal_versions()` (SQL), `config.py` and `Supa.kt`, and rebuild both apps. Every user is then asked to accept the new version.
- **Accounts use a real email address** (Supabase rejects made-up ones). A username (a–z, 0–9, _) is chosen at sign-up and shown on devices. **Email confirmation is off** (Supabase dashboard → Authentication → Sign In / Providers → Confirm email), so new users are signed in straight after signing up.

**Build the phone app (on the main PC)**
```bash
cd C:/Users/User/Documents/Drivewood/link/android && JAVA_HOME="/c/Program Files/Android/Android Studio/jbr" ./gradlew.bat assembleDebug
```
The APK ends up in `link/android/app/build/outputs/apk/debug/app-debug.apk`. You can also open the `link/android` folder in Android Studio and press Run.

**Install on Drivewood**
- The new build installs it automatically.
- On a running Drivewood VM, start the bridge and run:
```bash
curl -s 10.0.2.2:8000/link/vm-install.sh|bash
```
- By hand:
```bash
cd link/desktop/packaging && makepkg -si
```
The package installs:
- the app in `/usr/lib/drivewood-link`
- the `drivewood-link` command
- the menu entry
- `drivewood-link.service`, enabled for every user and started at login in the background
- a udev rule that lets the logged-in user create the virtual input device
- firewall rules for TCP 47800 and UDP 47801

Commands:
```bash
drivewood-link                 # open the window
```
```bash
drivewood-link --background    # run without a window (what the service does)
```
```bash
systemctl --user status drivewood-link
```

**On the phone (Android)**
1. Copy `app-debug.apk` to the phone, open it, and allow "install unknown apps" once. With the phone on USB (USB debugging on), you can also run `adb install -r app-debug.apk`. The app hides the status bar; swipe down from the top to see it.
2. Open DriveWood Link, create an account (tick the consent box) or sign in, and name the phone. No confirmation email is needed.
3. To let your computers control the phone: Account → **Open Accessibility settings** → turn on "DriveWood Link remote control". Each session still asks you first.
4. To send from any app: Share → DriveWood Link → pick a device.

**Look and feel (both apps)**
- **Sea-glass theme:** background `#0f1513`, cards `#161f1c` / `#1d2925`, text `#e6ebe7`, muted text `#8fa199`, teal accent `#4fd1b5`, sand `#d8c9a3` for "online elsewhere". The colours are defined at the top of `ui.py` (desktop) and in `Ui.kt` (phone).
- **Animations:** rows slide and fade in one after another, buttons shrink a little when pressed, the "nearby" dot pulses, and the refresh icon spins while loading. On the desktop, tabs slide and text boxes glow teal when focused.
- **Refresh:** the ⟳ button at the top right of Devices (desktop) or the Refresh button (phone) checks in with the server and reloads the device list.
- **Phone layout:** the status bar is hidden and everything sits a little lower on the screen.

**First use on the computer**
1. Open DriveWood Link from the Super menu, then sign in with the same account.
2. Name the computer. It now appears on your other devices.
3. To send, drop files on a device, or use **Files** / **Text** on its row.
4. To take control, press **Take control** on an online device. That device must accept.
5. Under Account, you can turn on **Share clipboard** (off by default), export your data, or read the Terms and Privacy Policy. There are also three account buttons:
   - **Sign out:** logs out but keeps this device in your list (offline). Signing in again reuses it.
   - **Remove this device:** asks first, then deletes *this* device from your account (on the phone it removes the phone, on a computer that computer). It also wipes the device's identity key and signs it out. Your account and other devices aren't affected.
   - **Delete my account:** deletes the account, all devices and history permanently.

**Already tested**
- On the main PC: two devices exchanged text, and a 30 MB file arrived byte-for-byte identical.
- A device from another account and a device with a wrong certificate were both refused.
- Sign-up without consent was refused by the server. Sign-up with consent created the profile.
- The Android app builds.
- In the Drivewood VM: the package installs offline (it only needs python, python-gobject, gtk4, openssl, grim, wl-clipboard and libnotify, all already on the system).
  - The app opens. Sign-up shows the unticked consent box, and Create stays greyed out until it's ticked.
  - The Terms and Privacy Policy open formatted.
  - `/dev/uinput` gets user access from the udev rule.
- Email confirmation was switched off on 2026-11-14, so there's no confirmation email and no broken localhost link any more.
- On a real Android phone (installed with `adb install -r`): sign-in, naming the phone, the hidden status bar, the sea-glass theme, the refresh button and the Account tab with Remove this device all work. The phone and the VM both registered and check in every minute, and each shows the other as "online, on another network".
- In the VM: the floating window, sign-in inside it, the refresh spinner, row animations, and the Remove this device confirmation (cancelled).
- Bug found and fixed: hiding the phone's status bar before the window existed crashed the app (`getWindowInsetsController() on a null object`). The fix is to touch `window.decorView` first.

**Still needs real devices**
- A real phone on the same Wi-Fi as a real Drivewood computer, for phone ↔ computer transfers and controlling the phone.
- A VM behind QEMU's network can't be reached by a phone.

**Signing up**
New users must tick "I agree to the Terms of Use and the Privacy Policy" (unticked by default, with an age confirmation) before the account is created. The server checks this too. Each accepted version is saved with the date, and the app asks again when the documents change.
The documents are in `Drivewood/legal/TERMS.md` and `Drivewood/legal/PRIVACY.md`. Fill in the `[developer name]`, `[contact email]`, `[country]`, `[Supabase region]` and date placeholders before release.

**Accounts and privacy**
- Accounts use Supabase Auth on the "DriveWood" project. Passwords are never stored in app tables.
- Supabase stores only `profiles`, `devices` and `transfers` (history, no file contents), each protected by row-level security.
- File contents and the screen stream go directly between devices, encrypted, and never through the internet.

**Troubleshooting**
- If a device doesn't show up, check that both are on the same Wi-Fi and that the router doesn't isolate clients.
- If a transfer fails, make sure ports 47800/47801 are open, and that the phone isn't in battery saver (it pauses the app).
- If control is refused, accept the request on the other device. On a phone, re-enable the accessibility service.

**Remove**
```bash
sudo pacman -R drivewood-link
```
On the phone, uninstall the app. To take a device off your list first, use **Account → Remove this device** on it. Sign out alone keeps it in the list.

### Stage 5: build Drivewood on a clean Arch VM (built, being tested)

**How the new build works (all files in `Drivewood/build/`)**
| File | What it does |
|---|---|
| `install-base.sh` | Run from the Arch live ISO as root. Erases the disk (`DISK=/dev/sda`) and creates an MBR with a 1 GiB FAT32 `/boot` (Limine can't read ext4) and an ext4 `/`. Installs every Drivewood package with `pacstrap`. Sets the time zone (`TZONE`, default Asia/Jerusalem), locale, hostname `drivewood`, zram, the user you name (wheel, sudo without the lecture), locks root, adds the plymouth hook, installs Limine BIOS (no menu, quiet, "Drivewood" branding), and sets up greetd autologin → `start-hyprland`. Asks the user to type their password at the end. |
| `install-desktop.sh` | Run right after, still from the ISO. Unpacks `stage.tar.gz` onto `/mnt`, copies the user configs, builds and installs the DriveWood Link package as the user (in `/var/tmp`, because `arch-chroot` empties `/tmp`), enables the sky timer for all users, and sets the `drivewood` boot animation. |
| `make_stage.sh` | Builds `stage/` + `stage.tar.gz` from the sources below, laid out like the installed system. Run it after every change. |
| `port_shell.py` | Makes `desktop/shell/` from `files/dshell/`, replacing every Omarchy command, path and name (stops if anything is left). |
| `port_fastfetch.py` | Same for the fastfetch config. |
| `update-vm.sh` | Updates a running Drivewood VM with the newest `stage.tar.gz` (one sudo prompt), copies the user configs, reloads Hyprland and restarts the shell. |
| `check.sh`, `probe*.sh` | Health report and package probes sent back through the bridge. |

**What the installed system contains**
- `/usr/bin/drivewood-*`: `wallpaper` (set/next/restore/current with swaybg, state in `~/.local/state/drivewood/background`), `sky` (+ user timer), `palette` (writes `palette.json` and `border.lua` in `~/.local/state/drivewood/`), `settings`, `workspace`, `screenshot`, `landscape`, `tidepool`.
- `/usr/share/drivewood/`: `shell/` (the bar, Super menu and Apps window, started with `qs -n -p /usr/share/drivewood/shell`), `backgrounds/`, `logo.png` (recoloured: sky letters, sea-blue lake, sand shore, no orange), `about.txt`, `hidden-apps` (apps hidden from the menus; users can add to `~/.config/drivewood/hidden-apps`), `apps/`, `settings/drivewood_settings.py`.
- `/usr/share/plymouth/themes/drivewood/`: the DRIVEWOOD rain animation.
- `/usr/lib/os-release`: `NAME=Drivewood`, `ID=drivewood`, `VERSION_ID=1.0`.
- `~/.config/hypr/hyprland.lua`: Drivewood's own Hyprland 0.57 **Lua** config (`hl.config`, `hl.bind`, `hl.window_rule`, `hl.on("hyprland.start")`). It loads `~/.local/state/drivewood/border.lua` (border follows the wallpaper), `~/.config/hypr/drivewood-settings.lua` (written by Settings) and finally `~/.config/hypr/custom.lua` (the user's own changes, never overwritten).
- `hyprlock.conf` (the lock screen doubles as the sign-in screen after boot), `hypridle.conf` (written by Settings → Power), `foot.ini` (needs `[colors-dark]` in foot 1.28), `mako`, GTK dark + Papirus-Dark icons, `starship.toml`, the bash greeting, and fastfetch.
- Keys: tap Super = menu, SUPER+ALT+SPACE = all apps, SUPER+RETURN terminal, SUPER+B browser, SUPER+E files, SUPER+I Settings, SUPER+L lock, **SUPER+W close** (SUPER+Q also closes), SUPER+V float, SUPER+F full screen, SUPER+ALT+L Link, SUPER+ALT+D Landscape, SUPER+ALT+T Tidepool, Print / Shift+Print screenshots.
- To switch workspace from a script: `hyprctl dispatch "hl.dsp.focus({ workspace = 2 })"` (the old `hyprctl dispatch workspace 2` form is gone in Lua mode).

**Drivewood Settings** (`drivewood-settings [page]`, for example `drivewood-settings network`): 14 pages.
- **Display:** resolution, refresh rate, scale per screen.
- **Input:** key repeat rate/delay, pointer speed, natural scrolling, tap to click.
- **Keybindings:** a searchable list of every shortcut.
- **Language:** up to four keyboard layouts and the switch key; system language (in a terminal).
- **Network:** Wi-Fi list/connect, Bluetooth power, connect and pair.
- **Sound:** volume, mute, output and input devices.
- **Appearance:** wallpaper grid, "choose a picture", sky follows the clock, gaps, corners, dimming, animations.
- **Apps:** search and install/remove Arch packages, plus Drivewood picks.
- **Update**, **Power** (lock/screen-off timers, sleep, restart, shut down), **Users** (computer name, password), **Date & time** (time zone search, automatic time), **Link**, **About**.

Settings are saved in `~/.config/drivewood/settings.json`. Anything that needs admin rights opens a terminal for the user's own password.

**Tested on the new VM**
- The DRIVEWOOD animation plays at boot with no menu or messages, then the lock screen acts as the sign-in.
- The bar, the Super menu (with Link), the terminal greeting and sky-blue prompt, the night sky picked from the clock, wallpaper colours, the Link background service and `/dev/uinput` access all work. `hyprctl configerrors` is empty and 12 GB of the 20 GB disk is free.
- Settings opens (about 10 seconds the first time in the VM, which draws in software). The sidebar, page switching and the Appearance wallpaper list work.

- Second pass: Display (shows the screen, resolution and scale), Keybindings (clean, searchable list), Network ("no Wi-Fi in a VM" plus Bluetooth), Sound (the VM has no sound card), and About (new logo, Drivewood 1.0, kernel, CPU, memory, disk, Hyprland 0.57.2) all work. Picking the midday sky in Appearance changed the wallpaper and the bar colours followed. SUPER+I opens Settings. SUPER+ALT+L opens DriveWood Link as a floating sea-glass window.
- Android Studio: `files/studio.sh` (now creates `~/.local/share/applications` first) installed it into `~/.local/opt/android-studio` (3.6 GB, checksum OK). The menu entry was added with `build/studio-entry.sh`. After that the disk is 9.5 GB used of 19 GB.
- Fixed during testing: the first Settings page loads on open, the wallpapers show as a grid, the Wi-Fi switch no longer re-triggers a scan, and the computer name is read from `/etc/hostname` (Arch has no `hostname` command).

**Still to do in stage 5**
- A full test pass by the user, then the final "done".

The original plan:
Same result as the first VM, but built cleanly:
- Internal names become `drivewood` (no `driftwood` or `omarchy` folders, ids or commands).
- Hyprland + Quickshell + the dshell, the theme, sky and palette scripts, Plymouth animation, Limine settings, fastfetch, apps, Android Studio, DriveWood Link.
- **All settings is rebuilt from scratch** as a Drivewood Settings app. The plan is in `files/os/settings-spec.md` (14 pages using plain Arch tools, no Omarchy menu underneath).
- A clean `/etc/os-release` (ID=drivewood, own URLs).
- Hostname `drivewood`. The first VM's hostname still contains "omarchy" and shows in the terminal title.
- Use the newest copies of everything in `files/` and `link/` (they include all the fixes in section 4, steps 13–21).
- DriveWood Link: install the package, put `drivewood-link-windows.lua` in the Drivewood Hyprland config, and keep **Link** in the Super menu favourites.
- The Shoreline app list needs its own small replacement for Omarchy's `hidden-entries.sh` (see 5.4).

### Updates and releases (GitHub)
- **Public repo:** https://github.com/guyka2212/drivewood-os (GPL-3.0). The whole project folder is the repo; build output (`build/stage*`, `dist/`, ISOs, APKs) is left out by `.gitignore` and published as release files instead. `.gitattributes` keeps Linux line endings so the scripts run on Drivewood.
- **Version:** `build/VERSION` (now `1.1.3`). `make_stage.sh` copies it to `/usr/share/drivewood/version` on installed systems.
- **Checking:** `drivewood-update-check` (user timer `drivewood-update-check.timer`: 2 minutes after login, then every 6 hours) asks the GitHub API for the latest release. If its tag (for example `v1.0.1`) is newer and it has a `drivewood-update-<version>.tar.gz`, it writes `~/.local/state/drivewood/update.json`. The bar then shows a small bouncing **down arrow** next to the CPU/memory bars.
- **Updating:** clicking the arrow runs `drivewood-update` in a terminal. It:
  1. shows the release notes and asks to confirm
  2. downloads the update and checks its SHA-256
  3. keeps the screen awake for the whole update (`systemd-inhibit --what=idle`, which hypridle respects) and asks for the user's password once; if the password prompt times out it offers to ask again (1.1.3)
  4. updates Arch packages (`pacman -Syu` plus anything new in `packages.txt`)
  5. installs Drivewood's system files and refreshes the boot animation
  6. hands over to the **new** `drivewood-update --finish` it just installed, which rebuilds DriveWood Link, installs or updates **Zen Browser** when the pinned version changed, makes Zen the default browser (only if the default was empty or Chromium), copies only Drivewood's own desktop files (`hyprland.lua`, `hyprlock.conf`, `foot.ini`, mako, fastfetch, starship) and reloads the desktop. It writes `~/.local/state/drivewood/finished`.
  7. Updates started from 1.0.0 run the old updater, which doesn't hand over. It ends by running the new `drivewood-update-check` in its terminal, which sees `finished` is not the new version and runs `drivewood-update --finish` there.
- **Zen Browser** replaces Chromium (1.1.2). Zen isn't in Arch's repos, so `build/zen/` is a small Drivewood package (`drivewood-zen`) that downloads the official `zen.linux-x86_64.tar.xz` from github.com/zen-browser/desktop, pinned to one version and checked against its SHA-256. To move to a newer Zen, change `pkgver` and `sha256sums` in `build/zen/PKGBUILD` (the SHA-256 is on the Zen release page, or `gh api repos/zen-browser/desktop/releases/latest`) and make a Drivewood release. Zen's own updater is turned off (`policies.json`). Updated systems keep Chromium installed (with its bookmarks) until the user removes it in Settings → Apps; new installs only have Zen.
- **Nothing of the user's is removed or changed:** Documents, Pictures, Downloads, apps, `custom.lua`, Settings choices (`drivewood-settings.lua`, `settings.json`), `hypridle.conf` and the Link sign-in all stay.
- **Making a release:**
  1. Raise `build/VERSION`.
  2. Run `bash build/make_release.sh`, which writes `dist/drivewood-update-<version>.tar.gz` + `.sha256`.
  3. **Ask the owner to write the release notes.** No release is published before they're written.
  4. Publish:
  ```bash
  gh release create v<version> dist/drivewood-update-<version>.tar.gz dist/drivewood-update-<version>.tar.gz.sha256 --title "Drivewood <version>" --notes-file RELEASE_NOTES.md
  ```
  Once the ISO exists, attach it to the release too.

### Stage 6: `drivewood-installer.iso`
- Built with archiso from the stage 5 package list (`build/packages.txt`) and configs. The installer asks for a username (no fixed name any more).
- Boot screen branding: `build/iso/splash.png` (640×480, the Drivewood logo on dark navy) replaces Arch's boot-menu splash, and every "Arch Linux" in the boot menus (BIOS and UEFI) is renamed to "Drivewood" by `make-iso.sh`.
- Goes into the **project folder**, `C:\Users\User\Documents\Drivewood\drivewood-installer.iso`, after the final "done". It's kept out of git and attached to a GitHub release once the owner has written the release notes.
