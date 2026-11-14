"""Being controlled on Drivewood (Wayland/Hyprland): screen frames from grim, input
through a virtual absolute mouse + keyboard (/dev/uinput, opened for the logged-in
user by the udev rule shipped with the package)."""
import json
import shutil
import subprocess

ABS_MAX = 32767


class Screen:
    def __init__(self):
        if not shutil.which("grim"):
            raise RuntimeError("grim is not installed")
        self.width, self.height = 1920, 1080
        try:
            mons = json.loads(subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True,
                                             text=True, timeout=5).stdout)
            self.width = max(m["x"] + int(m["width"] / m.get("scale", 1)) for m in mons)
            self.height = max(m["y"] + int(m["height"] / m.get("scale", 1)) for m in mons)
        except (OSError, ValueError, KeyError, subprocess.SubprocessError):
            pass
        # keep the stream light: scale big screens down to about 1280 px wide
        self.scale = min(1.0, 1280 / max(1, self.width))

    def grab(self):
        try:
            r = subprocess.run(["grim", "-t", "jpeg", "-q", "70", "-s", f"{self.scale:.3f}", "-"],
                               capture_output=True, timeout=5)
            return r.stdout if r.returncode == 0 else None
        except subprocess.SubprocessError:
            return None


class _E:
    """Linux input event codes (linux/input-event-codes.h)."""
    EV_SYN, EV_KEY, EV_REL, EV_ABS = 0, 1, 2, 3
    SYN_REPORT = 0
    REL_HWHEEL, REL_WHEEL = 6, 8
    ABS_X, ABS_Y = 0, 1
    BTN_LEFT, BTN_RIGHT, BTN_MIDDLE = 0x110, 0x111, 0x112
    KEY_ESC, KEY_MICMUTE = 1, 248


# uinput ioctls (linux/uinput.h, 64-bit)
UI_SET_EVBIT, UI_SET_KEYBIT, UI_SET_RELBIT, UI_SET_ABSBIT = 0x40045564, 0x40045565, 0x40045566, 0x40045567
UI_DEV_SETUP, UI_ABS_SETUP = 0x405C5503, 0x401C5504
UI_DEV_CREATE, UI_DEV_DESTROY = 0x5501, 0x5502


class Input:
    """Virtual absolute mouse + keyboard written straight to /dev/uinput (no extra libraries)."""

    def __init__(self):
        import fcntl
        import os
        import struct
        import time
        self.os, self.struct, self.e = os, struct, _E
        try:
            self.fd = os.open("/dev/uinput", os.O_WRONLY | os.O_NONBLOCK)
        except OSError as err:
            raise RuntimeError(f"no access to /dev/uinput ({err.strerror})") from None
        e = _E
        for ev in (e.EV_KEY, e.EV_REL, e.EV_ABS, e.EV_SYN):
            fcntl.ioctl(self.fd, UI_SET_EVBIT, ev)
        for k in list(range(e.KEY_ESC, e.KEY_MICMUTE + 1)) + [e.BTN_LEFT, e.BTN_RIGHT, e.BTN_MIDDLE]:
            fcntl.ioctl(self.fd, UI_SET_KEYBIT, k)
        for r in (e.REL_WHEEL, e.REL_HWHEEL):
            fcntl.ioctl(self.fd, UI_SET_RELBIT, r)
        for a in (e.ABS_X, e.ABS_Y):
            fcntl.ioctl(self.fd, UI_SET_ABSBIT, a)
            # struct uinput_abs_setup { u16 code; (pad) ; input_absinfo {value,min,max,fuzz,flat,res} }
            fcntl.ioctl(self.fd, UI_ABS_SETUP, struct.pack("HxxiiiiiI", a, 0, 0, ABS_MAX, 0, 0, 0))
        name = b"DriveWood Link remote input"
        # struct uinput_setup { input_id {bustype, vendor, product, version}; char name[80]; u32 ff_effects_max }
        fcntl.ioctl(self.fd, UI_DEV_SETUP, struct.pack("HHHH80sI", 0x06, 0x1d6b, 0x0104, 1, name, 0))
        fcntl.ioctl(self.fd, UI_DEV_CREATE)
        time.sleep(0.2)  # let the compositor pick up the new device
        self.held = set()

    def write(self, etype, code, value):
        self.os.write(self.fd, self.struct.pack("llHHi", 0, 0, etype, code, value))

    def syn(self):
        self.write(_E.EV_SYN, _E.SYN_REPORT, 0)

    def _xy(self, ev):
        x = max(0.0, min(1.0, float(ev.get("x", 0))))
        y = max(0.0, min(1.0, float(ev.get("y", 0))))
        self.write(_E.EV_ABS, _E.ABS_X, int(x * ABS_MAX))
        self.write(_E.EV_ABS, _E.ABS_Y, int(y * ABS_MAX))

    def handle(self, ev):
        e, k = _E, ev.get("k")
        if k == "move":
            self._xy(ev)
        elif k == "button":
            if "x" in ev:
                self._xy(ev)
            btn = {1: e.BTN_LEFT, 2: e.BTN_MIDDLE, 3: e.BTN_RIGHT}.get(int(ev.get("b", 1)), e.BTN_LEFT)
            self.write(e.EV_KEY, btn, 1 if ev.get("down") else 0)
        elif k == "scroll":
            if ev.get("dy"):
                self.write(e.EV_REL, e.REL_WHEEL, -int(ev["dy"]))
            if ev.get("dx"):
                self.write(e.EV_REL, e.REL_HWHEEL, int(ev["dx"]))
        elif k == "key":
            code = int(ev.get("code", 0))
            if e.KEY_ESC <= code <= e.KEY_MICMUTE:
                down = bool(ev.get("down"))
                self.write(e.EV_KEY, code, 1 if down else 0)
                (self.held.add if down else self.held.discard)(code)
        else:
            return
        self.syn()

    def close(self):
        import fcntl
        try:
            for code in list(self.held):  # never leave a key stuck down
                self.write(_E.EV_KEY, code, 0)
            self.syn()
            fcntl.ioctl(self.fd, UI_DEV_DESTROY)
            self.os.close(self.fd)
        except OSError:
            pass
