"""Make the Drivewood shell (build/desktop/shell) from the first VM's shell (files/dshell):
every Omarchy command, path and name is replaced with Drivewood's own."""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "files", "dshell")
DST = os.path.join(HERE, "desktop", "shell")
os.makedirs(DST, exist_ok=True)

COMMON = [
    ('"driftwood-bar"', '"drivewood-bar"'),
    ('"driftwood-shoreline"', '"drivewood-shoreline"'),
    ('"driftwood-tide"', '"drivewood-tide"'),
    ('// Driftwood', '// Drivewood'),
]
PER_FILE = {
    "shell.qml": [('target: "driftwood"', 'target: "drivewood"')],
    "Theme.qml": [
        ('// apps the system marks as hidden (the same list Omarchy\'s launcher uses)',
         '// apps hidden from the menus: /usr/share/drivewood/hidden-apps plus ~/.config/drivewood/hidden-apps'),
        ('command: ["bash", "-c", "\\"${OMARCHY_PATH:-/usr/share/omarchy}/shell/services/hidden-entries.sh\\" \\"${XDG_CURRENT_DESKTOP:-Hyprland}\\""]',
         'command: ["bash", "-c", "cat /usr/share/drivewood/hidden-apps \\"$HOME/.config/drivewood/hidden-apps\\" 2>/dev/null; true"]'),
        ('(see driftwood-palette)', '(see drivewood-palette)'),
        ('"/.local/state/driftwood/palette.json"', '"/.local/state/drivewood/palette.json"'),
        ('"/.local/state/omarchy/current/background"', '"/.local/state/drivewood/background"'),
        ('paletteRun.command = [Quickshell.env("HOME") + "/.local/bin/driftwood-palette", p]',
         'paletteRun.command = ["drivewood-palette", p]'),
        ('run("omarchy-launch-tui " + words.map(quote).join(" "))',
         'run("foot -e " + words.map(quote).join(" "))'),
        ('run("uwsm-app -- gtk-launch " + quote(entry.id + ".desktop"))',
         'run("gtk-launch " + quote(entry.id + ".desktop"))'),
    ],
    "Tide.qml": [
        ('cmd: "omarchy-launch-browser"', 'cmd: "zen-browser"'),
        ('cmd: "uwsm-app -- nautilus --new-window"', 'cmd: "nautilus --new-window"'),
        ('cmd: "xdg-terminal-exec " + home + "/driftwood/driftwood.py"', 'cmd: "drivewood-landscape"'),
        ('cmd: "uwsm-app -- gtk-launch android-studio.desktop"', 'cmd: "gtk-launch android-studio.desktop"'),
        ('cmd: "omarchy-theme-bg-next"', 'cmd: "drivewood-wallpaper next"'),
        ('cmd: home + "/.local/bin/driftwood-sky --force"', 'cmd: "drivewood-sky --force"'),
        ('cmd: "all-settings"', 'cmd: "drivewood-settings"'),
        ('hint: "the full system menu"', 'hint: "Drivewood Settings"'),
        ('cmd: "omarchy-system-lock"', 'cmd: "loginctl lock-session"'),
    ],
    "Bar.qml": [
        ('Theme.run("hyprctl dispatch " + Theme.quote("o.workspaces.focus(" + (index + 1) + ", \\"" + bar.monitorName + "\\")"))',
         'Theme.run("drivewood-workspace " + (index + 1))'),
    ],
}

ARROW = open(os.path.join(HERE, "desktop", "shell-update-arrow.qml"), encoding="utf-8").read()
PER_FILE["Bar.qml"].append(("      spacing: 14\n\n      Repeater {", "      spacing: 14\n\n" + ARROW + "      Repeater {"))

for name in sorted(os.listdir(SRC)):
    if not name.endswith(".qml"):
        continue
    t = open(os.path.join(SRC, name), encoding="utf-8").read()
    for old, new in COMMON + PER_FILE.get(name, []):
        if old in t:
            t = t.replace(old, new)
        elif any(old == o for o, _ in PER_FILE.get(name, [])):
            raise SystemExit(f"{name}: pattern not found: {old[:70]}")
    left = [w for w in ("omarchy", "uwsm", "driftwood-palette", "/.local/bin/") if w in t]
    if left:
        raise SystemExit(f"{name}: still mentions {left}")
    open(os.path.join(DST, name), "w", encoding="utf-8", newline="\n").write(t)
    print("ported", name)
