#!/usr/bin/env python3
"""Drivewood Settings: the system settings app (GTK 4), built from scratch.

Settings that belong to the desktop are saved in ~/.config/drivewood/settings.json and
written to ~/.config/hypr/drivewood-settings.lua, which Hyprland loads. Anything that needs
administrator rights opens a terminal where you type your own password.
"""
import glob
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

HOME = pathlib.Path.home()
CONF = HOME / ".config/drivewood/settings.json"
HYPR = HOME / ".config/hypr/drivewood-settings.lua"
IDLE = HOME / ".config/hypr/hypridle.conf"
STATE = HOME / ".local/state/drivewood"

DEFAULTS = {
    "gaps": True, "rounding": 10, "animations": True, "dim_inactive": True,
    "repeat_rate": 30, "repeat_delay": 600, "sensitivity": 0.0,
    "natural_scroll": True, "tap_to_click": True,
    "kb_layout": "us", "kb_switch": "grp:alt_shift_toggle",
    "lock_minutes": 5, "screen_off_minutes": 6,
    "monitors": {},
}

LAYOUTS = [("us", "English (US)"), ("il", "Hebrew"), ("gb", "English (UK)"), ("de", "German"), ("fr", "French"),
           ("es", "Spanish"), ("it", "Italian"), ("ru", "Russian"), ("ara", "Arabic"), ("pt", "Portuguese"),
           ("nl", "Dutch"), ("pl", "Polish"), ("tr", "Turkish"), ("ua", "Ukrainian"), ("jp", "Japanese")]
SWITCH_KEYS = [("grp:alt_shift_toggle", "Alt + Shift"), ("grp:win_space_toggle", "Super + Space"),
               ("grp:ctrl_shift_toggle", "Ctrl + Shift"), ("grp:caps_toggle", "Caps Lock")]


# ---------------------------------------------------------------- helpers
def sh(cmd, timeout=10):
    try:
        r = subprocess.run(cmd if isinstance(cmd, list) else ["bash", "-c", cmd],
                           capture_output=True, text=True, timeout=timeout)
        return r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def detached(cmd):
    subprocess.Popen(["bash", "-c", cmd], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def in_terminal(cmd, title="Drivewood"):
    """Run an administrator command in a terminal, so the user types their own password."""
    script = f"{cmd}; echo; read -rp 'Done. Press Enter to close.'"
    detached(f"foot --title {shlex.quote(title)} bash -c {shlex.quote(script)}")


def bg(fn, done=None):
    def run():
        try:
            r = fn()
        except Exception as e:  # shown in the page
            r = e
        if done:
            GLib.idle_add(done, r)
    threading.Thread(target=run, daemon=True).start()


def load():
    try:
        d = json.loads(CONF.read_text())
    except (OSError, ValueError):
        d = {}
    return {**DEFAULTS, **d}


def save(s):
    CONF.parent.mkdir(parents=True, exist_ok=True)
    CONF.write_text(json.dumps(s, indent=2))
    write_hypr(s)
    write_idle(s)


def lua(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_hypr(s):
    gi_, go = (6, 12) if s["gaps"] else (0, 0)
    lines = [
        "-- written by Drivewood Settings (changes here are overwritten; use custom.lua for your own)",
        "hl.config({",
        f"  general = {{ gaps_in = {gi_}, gaps_out = {go} }},",
        f"  decoration = {{ rounding = {int(s['rounding'])}, dim_inactive = {lua(s['dim_inactive'])} }},",
        f"  animations = {{ enabled = {lua(s['animations'])} }},",
        "  input = {",
        f"    kb_layout = {lua(s['kb_layout'])}, kb_options = {lua(s['kb_switch'] if ',' in s['kb_layout'] else '')},",
        f"    repeat_rate = {int(s['repeat_rate'])}, repeat_delay = {int(s['repeat_delay'])},",
        f"    sensitivity = {float(s['sensitivity'])},",
        f"    touchpad = {{ natural_scroll = {lua(s['natural_scroll'])}, tap_to_click = {lua(s['tap_to_click'])} }},",
        "  },",
        "})",
    ]
    for name, m in s.get("monitors", {}).items():
        lines.append(f"hl.monitor({{ output = {lua(name)}, mode = {lua(m.get('mode', 'preferred'))}, "
                     f"position = \"auto\", scale = {lua(m.get('scale', 'auto'))} }})")
    HYPR.parent.mkdir(parents=True, exist_ok=True)
    HYPR.write_text("\n".join(lines) + "\n")
    sh(["hyprctl", "reload"])


def write_idle(s):
    lock, off = int(s["lock_minutes"]) * 60, int(s["screen_off_minutes"]) * 60
    text = f"""# written by Drivewood Settings
general {{
    lock_cmd = pidof hyprlock || hyprlock
    before_sleep_cmd = loginctl lock-session
    after_sleep_cmd = hyprctl dispatch 'hl.dsp.dpms({{action = "on"}})'
}}
"""
    if lock > 0:
        text += f"listener {{\n    timeout = {lock}\n    on-timeout = loginctl lock-session\n}}\n"
    if off > 0:
        text += (f"listener {{\n    timeout = {off}\n    on-timeout = hyprctl dispatch 'hl.dsp.dpms({{action = \"off\"}})'\n"
                 f"    on-resume = hyprctl dispatch 'hl.dsp.dpms({{action = \"on\"}})'\n}}\n")
    if not IDLE.exists() or IDLE.read_text() != text:
        IDLE.write_text(text)
        detached("pkill -x hypridle; sleep 0.3; hypridle")


def palette():
    try:
        p = json.loads((STATE / "palette.json").read_text())
        return p.get("accent", "#8fb4e6"), p.get("bg", "#0f1118")
    except (OSError, ValueError):
        return "#8fb4e6", "#0f1118"


def css():
    accent, bgc = palette()
    return f"""
    window {{ background: {bgc}; color: #e6e9f0; }}
    .sidebar {{ background: alpha(white, 0.03); }}
    .sidebar row {{ padding: 9px 14px; border-radius: 10px; margin: 2px 8px; color: #c8ccd8; }}
    .sidebar row:selected {{ background: alpha({accent}, 0.2); color: {accent}; }}
    .page-title {{ font-size: 22px; font-weight: 700; }}
    .muted {{ color: #9aa0b4; }}
    .card {{ background: alpha(white, 0.04); border-radius: 14px; padding: 14px; }}
    .section {{ font-weight: 700; color: {accent}; margin-top: 8px; }}
    button {{ border-radius: 10px; background: alpha(white, 0.07); color: #e6e9f0; border: none; box-shadow: none;
              transition: background 160ms ease, transform 120ms ease; }}
    button:hover {{ background: alpha(white, 0.12); }}
    button:active {{ transform: scale(0.97); }}
    button.accent {{ background: {accent}; color: #0f1118; font-weight: 700; }}
    button.danger {{ color: #ff8f8f; }}
    entry, spinbutton, dropdown button {{ border-radius: 10px; background: alpha(white, 0.06); color: #e6e9f0; }}
    switch:checked {{ background: {accent}; }}
    scale highlight {{ background: {accent}; }}
    .wall {{ border-radius: 10px; border: 2px solid transparent; }}
    .wall:hover {{ border-color: alpha({accent}, 0.6); }}
    """


def label(text, *classes, wrap=True, xalign=0.0, selectable=False):
    w = Gtk.Label(label=text, wrap=wrap, xalign=xalign, selectable=selectable)
    for c in classes:
        w.add_css_class(c)
    return w


def vbox(spacing=10, margin=0):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=spacing)
    for side in ("top", "bottom", "start", "end"):
        getattr(b, f"set_margin_{side}")(margin)
    return b


def hbox(spacing=10):
    return Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing)


def row(title, widget, subtitle=None):
    r = hbox(12)
    r.add_css_class("card")
    text = vbox(2)
    text.set_hexpand(True)
    text.append(label(title))
    if subtitle:
        text.append(label(subtitle, "muted"))
    r.append(text)
    widget.set_valign(Gtk.Align.CENTER)
    r.append(widget)
    return r


def button(text, fn, *classes):
    b = Gtk.Button(label=text)
    for c in classes:
        b.add_css_class(c)
    b.connect("clicked", lambda *_: fn())
    return b


def switch(active, fn):
    s = Gtk.Switch(active=active)
    s.connect("notify::active", lambda w, _p: fn(w.get_active()))
    return s


def dropdown(options, current, fn):
    """options: [(value, label)]"""
    d = Gtk.DropDown.new_from_strings([o[1] for o in options])
    vals = [o[0] for o in options]
    if current in vals:
        d.set_selected(vals.index(current))
    d.connect("notify::selected", lambda w, _p: fn(vals[w.get_selected()]))
    return d


def clear(box):
    while (c := box.get_first_child()) is not None:
        box.remove(c)


# ---------------------------------------------------------------- pages
class Page(Gtk.ScrolledWindow):
    title = ""
    icon = ""

    def __init__(self, app):
        super().__init__(hscrollbar_policy=Gtk.PolicyType.NEVER, vexpand=True)
        self.app = app
        self.box = vbox(10, 24)
        self.set_child(self.box)
        self.box.append(label(self.title, "page-title"))
        self.build()

    @property
    def s(self):
        return self.app.settings

    def set(self, key, value):
        self.s[key] = value
        save(self.s)

    def build(self):
        pass

    def refresh(self):
        pass


class Display(Page):
    title, icon = "Display", "video-display-symbolic"

    def build(self):
        self.list = vbox(10)
        self.box.append(self.list)
        self.box.append(label("Changes apply right away and are kept after a restart.", "muted"))

    def refresh(self):
        clear(self.list)
        try:
            mons = json.loads(sh(["hyprctl", "monitors", "-j"]) or "[]")
        except ValueError:
            mons = []
        for m in mons:
            name = m["name"]
            saved = self.s["monitors"].get(name, {})
            modes = sorted(set(m.get("availableModes") or []), key=lambda x: (-int(x.split("x")[0]), x))
            cur = saved.get("mode") or f"{m['width']}x{m['height']}@{m['refreshRate']:.2f}Hz"
            opts = [("preferred", "Best for this screen")] + [(x, x.replace("Hz", " Hz")) for x in modes]
            card = vbox(8)
            card.add_css_class("card")
            card.append(label(f"{name} · {m.get('description') or m.get('model', '')}", "section"))
            card.append(row("Resolution and refresh rate", dropdown(opts, cur if cur in dict(opts) else "preferred",
                                                                   lambda v, n=name: self._mon(n, "mode", v))))
            scales = [("auto", "Automatic"), ("1", "100%"), ("1.25", "125%"), ("1.5", "150%"), ("1.75", "175%"), ("2", "200%")]
            card.append(row("Scale", dropdown(scales, str(saved.get("scale", "auto")), lambda v, n=name: self._mon(n, "scale", v))))
            self.list.append(card)
        if not mons:
            self.list.append(label("No screens found.", "muted"))

    def _mon(self, name, key, value):
        self.s["monitors"].setdefault(name, {})[key] = value
        save(self.s)


class Input(Page):
    title, icon = "Input", "input-keyboard-symbolic"

    def build(self):
        s = self.s
        self.box.append(label("Keyboard", "section"))
        rate = Gtk.SpinButton.new_with_range(10, 80, 1)
        rate.set_value(s["repeat_rate"])
        rate.connect("value-changed", lambda w: self.set("repeat_rate", int(w.get_value())))
        self.box.append(row("Repeat rate", rate, "Characters per second while a key is held"))
        delay = Gtk.SpinButton.new_with_range(150, 1500, 50)
        delay.set_value(s["repeat_delay"])
        delay.connect("value-changed", lambda w: self.set("repeat_delay", int(w.get_value())))
        self.box.append(row("Repeat delay (ms)", delay, "How long to hold a key before it repeats"))
        self.box.append(label("Mouse and touchpad", "section"))
        sens = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, -1, 1, 0.1)
        sens.set_value(s["sensitivity"])
        sens.set_size_request(220, -1)
        sens.connect("value-changed", lambda w: self.set("sensitivity", round(w.get_value(), 1)))
        self.box.append(row("Pointer speed", sens))
        self.box.append(row("Natural scrolling", switch(s["natural_scroll"], lambda v: self.set("natural_scroll", v)),
                            "Content moves with your fingers"))
        self.box.append(row("Tap to click", switch(s["tap_to_click"], lambda v: self.set("tap_to_click", v))))


class Keys(Page):
    title, icon = "Keybindings", "preferences-desktop-keyboard-shortcuts-symbolic"

    def build(self):
        self.search = Gtk.SearchEntry(placeholder_text="Search shortcuts")
        self.search.connect("search-changed", lambda *_: self.refresh())
        self.box.append(self.search)
        self.list = vbox(6)
        self.box.append(self.list)
        self.box.append(label("Add your own shortcuts in ~/.config/hypr/custom.lua, for example:\n"
                              'hl.bind("SUPER + G", hl.dsp.exec_cmd("gimp"), { description = "GIMP" })', "muted", selectable=True))

    def refresh(self):
        clear(self.list)
        try:
            binds = json.loads(sh(["hyprctl", "binds", "-j"]) or "[]")
        except ValueError:
            binds = []
        mods = {64: "Super", 1: "Shift", 4: "Ctrl", 8: "Alt"}
        q = self.search.get_text().lower()
        seen = set()
        for b in binds:
            desc = b.get("description") or ""
            if not desc or desc in seen:
                continue
            keys = [n for bit, n in mods.items() if b.get("modmask", 0) & bit]
            key = b.get("key", "")
            combo = "Super (tap)" if key.startswith("Super_") else " + ".join(keys + ([key.upper() if len(key) == 1 else key] if key else []))
            if q and q not in (desc + combo).lower():
                continue
            seen.add(desc)
            r = hbox(12)
            r.add_css_class("card")
            d = label(desc)
            d.set_hexpand(True)
            r.append(d)
            r.append(label(combo, "muted", wrap=False))
            self.list.append(r)


class Language(Page):
    title, icon = "Language", "preferences-desktop-locale-symbolic"

    def build(self):
        self.box.append(label("Keyboard layouts", "section"))
        self.box.append(label("Pick up to four. Switch between them with the key below.", "muted"))
        current = self.s["kb_layout"].split(",")
        self.checks = {}
        grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, max_children_per_line=3, column_spacing=6, row_spacing=6)
        for code, name in LAYOUTS:
            c = Gtk.CheckButton(label=name, active=code in current)
            c.connect("toggled", lambda *_: self._layouts())
            self.checks[code] = c
            grid.append(c)
        self.box.append(grid)
        self.box.append(row("Switch layout with", dropdown(SWITCH_KEYS, self.s["kb_switch"], lambda v: self.set("kb_switch", v))))
        self.box.append(label("System language", "section"))
        loc = sh("localectl status | sed -n 's/.*System Locale: LANG=//p'") or "en_US.UTF-8"
        self.box.append(row("Language and formats", button("Change…", lambda: in_terminal(
            "echo 'Available: en_US.UTF-8 he_IL.UTF-8 en_GB.UTF-8 de_DE.UTF-8 fr_FR.UTF-8 es_ES.UTF-8'; "
            "read -rp 'Locale (e.g. en_US.UTF-8): ' L && sudo sed -i \"s/^#$L/$L/\" /etc/locale.gen && sudo locale-gen && "
            "sudo localectl set-locale LANG=$L && echo 'Sign out and in again to apply.'", "Language")), f"Now: {loc}"))

    def _layouts(self):
        chosen = [c for c, _ in LAYOUTS if self.checks[c].get_active()][:4] or ["us"]
        self.set("kb_layout", ",".join(chosen))


class Network(Page):
    title, icon = "Network", "network-wireless-symbolic"

    def build(self):
        self.status = label("", "muted")
        self.box.append(self.status)
        head = hbox()
        head.append(label("Wi-Fi", "section"))
        sp = Gtk.Box(hexpand=True)
        head.append(sp)
        self.wifi_switch = Gtk.Switch()
        self._filling = False
        self.wifi_switch.connect("state-set", self._wifi_toggled)
        head.append(self.wifi_switch)
        head.append(button("Scan", self.refresh))
        self.box.append(head)
        self.wifi = vbox(6)
        self.box.append(self.wifi)
        self.box.append(label("Bluetooth", "section"))
        self.bt = vbox(6)
        self.box.append(self.bt)

    def _wifi_toggled(self, _w, on):
        if not self._filling:  # ignore the switch being updated from the scan result
            sh(["nmcli", "radio", "wifi", "on" if on else "off"])
            self.refresh()
        return False

    def refresh(self):
        self.status.set_text("Checking…")

        def work():
            dev = sh("nmcli -t -f DEVICE,TYPE,STATE,CONNECTION device")
            radio = sh(["nmcli", "radio", "wifi"])
            nets = sh("nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY device wifi list --rescan auto", timeout=20)
            bt_power = "yes" in sh("bluetoothctl show | grep Powered")
            paired = sh("bluetoothctl devices Paired")
            return dev, radio, nets, bt_power, paired
        bg(work, self._fill)

    def _fill(self, r):
        if isinstance(r, Exception):
            self.status.set_text(str(r))
            return
        dev, radio, nets, bt_power, paired = r
        connected = [l.split(":") for l in dev.splitlines() if ":connected:" in l]
        self.status.set_text("Connected: " + ", ".join(f"{c[3]} ({c[1]})" for c in connected) if connected else "Not connected")
        self._filling = True
        self.wifi_switch.set_active(radio == "enabled")
        self._filling = False
        clear(self.wifi)
        seen = set()
        for line in nets.splitlines():
            parts = re.split(r"(?<!\\):", line)
            if len(parts) < 4 or not parts[1] or parts[1] in seen:
                continue
            seen.add(parts[1])
            ssid, sig, sec = parts[1].replace("\\:", ":"), parts[2], parts[3]
            using = parts[0] == "*"
            act = label("Connected", "muted", wrap=False) if using else button("Connect", lambda s=ssid, e=bool(sec and sec != "--"): self._connect(s, e))
            self.wifi.append(row(ssid, act, f"Signal {sig}% · {sec if sec and sec != '--' else 'open'}"))
        if not seen:
            self.wifi.append(label("No Wi-Fi networks found (a VM usually has wired networking only).", "muted"))
        clear(self.bt)
        self.bt.append(row("Bluetooth", switch(bt_power, lambda on: (sh(["bluetoothctl", "power", "on" if on else "off"]), None)[1])))
        for line in paired.splitlines():
            m = re.match(r"Device (\S+) (.+)", line)
            if m:
                mac, name = m.groups()
                self.bt.append(row(name, button("Connect", lambda a=mac: bg(lambda: sh(["bluetoothctl", "connect", a], 20))), mac))
        self.bt.append(button("Pair a new device…", lambda: in_terminal(
            "bluetoothctl power on; bluetoothctl --timeout 15 scan on; bluetoothctl devices; "
            "read -rp 'Device address to pair: ' A && bluetoothctl pair $A && bluetoothctl trust $A && bluetoothctl connect $A", "Bluetooth")))

    def _connect(self, ssid, secured):
        if not secured:
            bg(lambda: sh(["nmcli", "device", "wifi", "connect", ssid], 30), lambda _: self.refresh())
            return
        d = Gtk.Window(title=f"Connect to {ssid}", transient_for=self.app.win, modal=True, default_width=360)
        b = vbox(10, 18)
        pw = Gtk.PasswordEntry(placeholder_text="Wi-Fi password", show_peek_icon=True)
        msg = label("", "muted")
        go = button("Connect", lambda: None, "accent")

        def connect(*_):
            msg.set_text("Connecting…")
            secret = pw.get_text()
            bg(lambda: subprocess.run(["nmcli", "device", "wifi", "connect", ssid, "password", secret],
                                      capture_output=True, text=True, timeout=40),
               lambda r: (d.close(), self.refresh()) if getattr(r, "returncode", 1) == 0 else msg.set_text("Couldn't connect. Check the password."))
        go.connect("clicked", connect)
        pw.connect("activate", connect)
        for w in (pw, go, msg):
            b.append(w)
        d.set_child(b)
        d.present()


class Sound(Page):
    title, icon = "Sound", "audio-volume-high-symbolic"

    def build(self):
        self.list = vbox(10)
        self.box.append(self.list)

    def refresh(self):
        clear(self.list)
        vol = sh("wpctl get-volume @DEFAULT_AUDIO_SINK@")
        m = re.search(r"([\d.]+)", vol)
        level = float(m.group(1)) if m else 0
        sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        sc.set_value(level * 100)
        sc.set_size_request(260, -1)
        sc.connect("value-changed", lambda w: sh(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{int(w.get_value())}%"]))
        self.list.append(row("Volume", sc))
        self.list.append(row("Mute", switch("MUTED" in vol, lambda on: sh(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "1" if on else "0"]))))
        status = sh("wpctl status")
        for kind, header in (("Output", "Sinks:"), ("Input", "Sources:")):
            devices = []
            if header in status:
                section = status.split(header, 1)[1].split("\n\n", 1)[0]
                for line in section.splitlines():
                    mm = re.search(r"(\*)?\s*(\d+)\.\s+(.+?)(\s+\[vol:.*)?$", line)
                    if mm:
                        devices.append((mm.group(2), mm.group(3).strip(), bool(mm.group(1))))
            self.list.append(label(f"{kind} device", "section"))
            for dev_id, name, default in devices:
                w = label("In use", "muted", wrap=False) if default else button("Use", lambda i=dev_id: (sh(["wpctl", "set-default", i]), self.refresh()))
                self.list.append(row(name, w))
            if not devices:
                self.list.append(label("None found.", "muted"))


class Appearance(Page):
    title, icon = "Appearance", "preferences-desktop-wallpaper-symbolic"

    def build(self):
        self.box.append(label("Wallpaper", "section"))
        self.grid = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.NONE, min_children_per_line=2, max_children_per_line=4,
                                homogeneous=True, column_spacing=8, row_spacing=8)
        self.box.append(self.grid)
        actions = hbox()
        actions.append(button("Choose a picture…", self._pick))
        actions.append(button("Open wallpaper folder", lambda: detached(f"mkdir -p ~/Pictures/Wallpapers; nautilus ~/Pictures/Wallpapers")))
        self.box.append(actions)
        sky_on = sh(["systemctl", "--user", "is-enabled", "drivewood-sky.timer"]) == "enabled"
        self.box.append(row("Sky follows the clock", switch(sky_on, self._sky),
                            "Dawn, midday, dusk and night skies change with the time of day"))
        self.box.append(label("Windows", "section"))
        self.box.append(row("Gaps between windows", switch(self.s["gaps"], lambda v: self.set("gaps", v))))
        corners = [(0, "Square"), (6, "Slightly rounded"), (10, "Rounded"), (16, "Very rounded")]
        self.box.append(row("Corners", dropdown(corners, self.s["rounding"], lambda v: self.set("rounding", v))))
        self.box.append(row("Dim windows you aren't using", switch(self.s["dim_inactive"], lambda v: self.set("dim_inactive", v))))
        self.box.append(row("Animations", switch(self.s["animations"], lambda v: self.set("animations", v))))
        self.box.append(label("Colours follow the wallpaper automatically.", "muted"))

    def refresh(self):
        clear(self.grid)
        files = sorted(glob.glob("/usr/share/drivewood/backgrounds/*")) + sorted(
            f for f in glob.glob(str(HOME / "Pictures/Wallpapers/*")) if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")))
        for f in files:
            pic = Gtk.Picture.new_for_filename(f)
            pic.set_content_fit(Gtk.ContentFit.COVER)
            pic.set_can_shrink(True)
            b = Gtk.Button()
            b.set_size_request(200, 120)
            b.add_css_class("wall")
            b.set_child(pic)
            b.connect("clicked", lambda *_, p=f: detached(f"drivewood-wallpaper set {shlex.quote(p)}"))
            self.grid.append(b)

    def _pick(self):
        dlg = Gtk.FileDialog(title="Choose a wallpaper")

        def done(d, res):
            try:
                f = d.open_finish(res)
            except GLib.Error:
                return
            dest = HOME / "Pictures/Wallpapers"
            dest.mkdir(parents=True, exist_ok=True)
            target = dest / os.path.basename(f.get_path())
            if str(target) != f.get_path():
                target.write_bytes(pathlib.Path(f.get_path()).read_bytes())
            detached(f"drivewood-wallpaper set {shlex.quote(str(target))}")
            self.refresh()
        dlg.open(self.app.win, None, done)

    def _sky(self, on):
        sh(["systemctl", "--user", "enable" if on else "disable", "--now", "drivewood-sky.timer"])
        if on:
            detached("drivewood-sky --force")


class Apps(Page):
    title, icon = "Apps", "system-software-install-symbolic"

    def build(self):
        self.box.append(label("Search Arch's official packages. Installing or removing opens a terminal for your password.", "muted"))
        self.search = Gtk.SearchEntry(placeholder_text="Search apps, e.g. gimp, vlc, libreoffice")
        self.search.connect("activate", lambda *_: self._search())
        self.box.append(self.search)
        picks = hbox(6)
        for name, pkg in (("VLC", "vlc"), ("GIMP", "gimp"), ("LibreOffice", "libreoffice-fresh"), ("OBS", "obs-studio"), ("Steam", "steam")):
            picks.append(button(name, lambda p=pkg: in_terminal(f"sudo pacman -S --needed {p}", "Install")))
        self.box.append(label("Drivewood picks", "section"))
        self.box.append(picks)
        self.results = vbox(6)
        self.box.append(self.results)

    def _search(self):
        q = self.search.get_text().strip()
        if not q:
            return
        clear(self.results)
        self.results.append(label("Searching…", "muted"))

        def done(out):
            clear(self.results)
            lines = str(out).splitlines()
            shown = 0
            for i in range(0, len(lines) - 1, 2):
                m = re.match(r"(\S+)/(\S+) (\S+)( \[installed.*\])?", lines[i])
                if not m:
                    continue
                repo, name, ver, inst = m.groups()
                act = button("Remove", lambda n=name: in_terminal(f"sudo pacman -Rns {n}", "Remove"), "danger") if inst else \
                    button("Install", lambda n=name: in_terminal(f"sudo pacman -S --needed {n}", "Install"), "accent")
                self.results.append(row(name, act, lines[i + 1].strip()))
                shown += 1
                if shown >= 30:
                    break
            if not shown:
                self.results.append(label("Nothing found.", "muted"))
        bg(lambda: sh(["pacman", "-Ss", q], 20), done)


class Update(Page):
    title, icon = "Update", "software-update-available-symbolic"

    def build(self):
        last = sh("awk '/\\[ALPM\\] (upgraded|installed)/{l=$1\" \"$2} END{print substr(l,2,16)}' /var/log/pacman.log")
        self.box.append(row("Update everything", button("Update now", lambda: in_terminal("sudo pacman -Syu", "Update"), "accent"),
                            f"Last change: {last.replace('T', ' ') or 'unknown'}"))
        self.box.append(row("DriveWood Link", button("Check", lambda: in_terminal("pacman -Q drivewood-link", "Link")),
                            "Link updates arrive with Drivewood updates"))
        self.box.append(label("Updates come straight from Arch Linux. Restart after a kernel update.", "muted"))


class Power(Page):
    title, icon = "Power", "system-shutdown-symbolic"

    def build(self):
        opts = [(0, "Never"), (2, "2 minutes"), (5, "5 minutes"), (10, "10 minutes"), (30, "30 minutes")]
        self.box.append(row("Lock the screen after", dropdown(opts, self.s["lock_minutes"], lambda v: self.set("lock_minutes", v))))
        opts2 = [(0, "Never"), (3, "3 minutes"), (6, "6 minutes"), (15, "15 minutes"), (60, "1 hour")]
        self.box.append(row("Turn the screen off after", dropdown(opts2, self.s["screen_off_minutes"], lambda v: self.set("screen_off_minutes", v))))
        bat = sh("cat /sys/class/power_supply/BAT*/capacity 2>/dev/null | head -1")
        if bat:
            self.box.append(row("Battery", label(f"{bat}%", "muted", wrap=False)))
        acts = hbox()
        acts.append(button("Lock", lambda: detached("loginctl lock-session")))
        acts.append(button("Sleep", lambda: detached("systemctl suspend")))
        acts.append(button("Restart", lambda: detached("systemctl reboot")))
        acts.append(button("Shut down", lambda: detached("systemctl poweroff"), "danger"))
        self.box.append(acts)


class Users(Page):
    title, icon = "Users", "system-users-symbolic"

    def build(self):
        user = os.environ.get("USER", "")
        self.box.append(row("User name", label(user, "muted", wrap=False)))
        self.box.append(row("Computer name", button(pathlib.Path("/etc/hostname").read_text().strip() or "drivewood", lambda: in_terminal(
            "read -rp 'New computer name: ' N && sudo hostnamectl set-hostname \"$N\"", "Computer name")), "Click to rename"))
        self.box.append(row("Password", button("Change password…", lambda: in_terminal("passwd", "Password")),
                            "Also your sudo password"))


class DateTime(Page):
    title, icon = "Date & time", "preferences-system-time-symbolic"

    def build(self):
        info = sh("timedatectl show")
        tz = re.search(r"Timezone=(.+)", info)
        ntp = "NTP=yes" in info
        self.box.append(row("Time zone", button(tz.group(1) if tz else "UTC", self._tz), "Click to change"))
        self.box.append(row("Set the time automatically", switch(ntp, lambda on: in_terminal(
            f"sudo timedatectl set-ntp {'true' if on else 'false'}", "Time"))))
        self.box.append(row("Now", label(sh("date '+%A %-d %B %Y, %H:%M'"), "muted", wrap=False)))

    def _tz(self):
        zones = sh(["timedatectl", "list-timezones"], 10).splitlines()
        d = Gtk.Window(title="Time zone", transient_for=self.app.win, modal=True, default_width=380, default_height=480)
        b = vbox(8, 14)
        search = Gtk.SearchEntry(placeholder_text="Search, e.g. Jerusalem, London")
        lst = Gtk.ListBox()
        sc = Gtk.ScrolledWindow(vexpand=True)
        sc.set_child(lst)

        def fill(*_):
            clear(lst)
            q = search.get_text().lower()
            for z in [z for z in zones if q in z.lower()][:80]:
                btn = Gtk.Button(label=z)
                btn.connect("clicked", lambda *_, zz=z: (in_terminal(f"sudo timedatectl set-timezone {zz}", "Time zone"), d.close()))
                lst.append(btn)
        search.connect("search-changed", fill)
        fill()
        b.append(search)
        b.append(sc)
        d.set_child(b)
        d.present()


class Link(Page):
    title, icon = "Link", "network-transmit-receive-symbolic"

    def build(self):
        self.box.append(label("DriveWood Link sends files and text to your own devices and lets this computer take control of them.", "muted"))
        self.box.append(row("DriveWood Link", button("Open", lambda: detached("drivewood-link"), "accent")))
        running = sh(["systemctl", "--user", "is-active", "drivewood-link.service"]) == "active"
        self.box.append(row("Run in the background", switch(running, lambda on: sh(
            ["systemctl", "--user", "enable" if on else "disable", "--now", "drivewood-link.service"])),
            "Receive files and control requests when the window is closed"))


class About(Page):
    title, icon = "About", "help-about-symbolic"

    def build(self):
        logo = Gtk.Picture.new_for_filename("/usr/share/drivewood/logo.png")
        logo.set_size_request(-1, 90)
        logo.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.box.append(logo)
        osr = dict(re.findall(r'^(\w+)="?([^"\n]*)"?', pathlib.Path("/etc/os-release").read_text(), re.M))
        mem = sh("free -h | awk '/Mem:/{print $2}'")
        cpu = sh("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2").strip()
        disk = sh("df -h / | awk 'NR==2{print $3\" used of \"$2}'")
        for k, v in (("System", f"{osr.get('PRETTY_NAME', 'Drivewood')} {osr.get('VERSION_ID', '')}"),
                     ("Kernel", sh(["uname", "-r"])), ("Processor", cpu), ("Memory", mem), ("Disk", disk),
                     ("Desktop", "Hyprland " + (sh("hyprctl version -j | python3 -c 'import json,sys;print(json.load(sys.stdin)[\"version\"])'") or "")),
                     ("Computer name", pathlib.Path("/etc/hostname").read_text().strip())):
            self.box.append(row(k, label(v, "muted", wrap=False, selectable=True)))


PAGES = [Display, Input, Keys, Language, Network, Sound, Appearance, Apps, Update, Power, Users, DateTime, Link, About]
ALIASES = {p.__name__.lower(): p.__name__ for p in PAGES} | {"date": "DateTime", "time": "DateTime", "wifi": "Network",
                                                             "bluetooth": "Network", "wallpaper": "Appearance", "keyboard": "Input"}


class SettingsApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.drivewood.Settings", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.settings = load()
        self.win = None

    def do_command_line(self, cmd):
        args = cmd.get_arguments()[1:]
        if self.win is None:
            self._build()
        if args:
            name = ALIASES.get(args[0].lower())
            if name:
                self.stack.set_visible_child_name(name)
        self.win.present()
        return 0

    def _build(self):
        prov = Gtk.CssProvider()
        prov.load_from_string(css())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self.win = Gtk.ApplicationWindow(application=self, title="Drivewood Settings", default_width=900, default_height=640)
        root = hbox(0)
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=180, hexpand=True)
        side = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        side.add_css_class("sidebar")
        side.set_size_request(210, -1)
        self.pages = {}
        for P in PAGES:
            page = P(self)
            self.pages[P.__name__] = page
            self.stack.add_named(page, P.__name__)
            r = hbox(10)
            r.append(Gtk.Image(icon_name=P.icon))
            r.append(label(P.title, wrap=False))
            row_ = Gtk.ListBoxRow()
            row_.set_child(r)
            row_.page = P.__name__
            side.append(row_)
        side.connect("row-selected", lambda _l, r: r and self.stack.set_visible_child_name(r.page))
        self.stack.connect("notify::visible-child-name", lambda *_: self._shown(side))
        sc = Gtk.ScrolledWindow(hscrollbar_policy=Gtk.PolicyType.NEVER)
        sc.set_child(side)
        root.append(sc)
        root.append(self.stack)
        self.win.set_child(root)
        side.select_row(side.get_row_at_index(0))
        self.pages[PAGES[0].__name__].refresh()  # the first page is already visible, so fill it now
        save(self.settings)  # make sure Hyprland and hypridle use the saved values

    def _shown(self, side):
        name = self.stack.get_visible_child_name()
        self.pages[name].refresh()
        for i, P in enumerate(PAGES):
            if P.__name__ == name and side.get_selected_row() is not side.get_row_at_index(i):
                side.select_row(side.get_row_at_index(i))


def main():
    sys.exit(SettingsApp().run(sys.argv))


if __name__ == "__main__":
    main()
