"""DriveWood Link engine: account + devices, the TLS server, sending, and take control.
No GUI code here; the window talks to it through the `ui` callbacks."""
import hashlib
import os
import pathlib
import socket
import threading
import time

from . import config
from .net import Discovery, Identity, client_connect, local_ip, recv_exact, recv_header, recv_msg, send_msg
from .supa import Supa, SupaError

CHUNK = 1 << 20


class ConsoleUI:
    """Fallback callbacks (used by tests and when no window is open)."""

    def ask_control(self, device_name):
        return False

    def control_started(self, device_name, stop):
        print(f"[link] being controlled by {device_name}")

    def control_ended(self):
        print("[link] control ended")

    def received_text(self, device_name, text):
        print(f"[link] text from {device_name}: {text}")

    def received_file(self, device_name, path):
        print(f"[link] file from {device_name}: {path}")

    def progress(self, label, done, total):
        pass

    def changed(self):
        pass


class LinkCore:
    def __init__(self, ui=None):
        self.ui = ui or ConsoleUI()
        self.supa = Supa()
        self.identity = Identity()
        self.device = config.load("device.json")  # {"id", "name"}
        self.devices = []  # my devices from Supabase
        self.discovery = None
        self.token_cache = {}  # access token -> (user id, time)
        self.server = None
        self.clipboard_sync = bool((config.load("prefs.json", {}) or {}).get("clipboard", False))
        self.controlled = None  # active incoming control session socket

    # --- account / device -------------------------------------------------
    def legal_ok(self):
        p = self.supa.rest("GET", f"profiles?id=eq.{self.supa.user_id}&select=username,terms_version,privacy_version")
        if not p:
            return False
        self.username = p[0]["username"]
        return p[0]["terms_version"] == config.TERMS_VERSION and p[0]["privacy_version"] == config.PRIVACY_VERSION

    def accept_legal(self):
        self.supa.rpc("accept_legal", {"terms": config.TERMS_VERSION, "privacy": config.PRIVACY_VERSION})

    def register_device(self, name):
        name = name.strip()[:40] or socket.gethostname()
        row = {"name": name, "kind": "computer", "cert_sha256": self.identity.fingerprint,
               "lan_addr": local_ip(), "last_seen": "now()"}
        if self.device:
            r = self.supa.rest("PATCH", f"devices?id=eq.{self.device['id']}", row, prefer="return=representation")
            if r:
                self.device = {"id": r[0]["id"], "name": r[0]["name"]}
                config.save("device.json", self.device)
                return
        r = self.supa.rest("POST", "devices", row, prefer="return=representation")
        self.device = {"id": r[0]["id"], "name": r[0]["name"]}
        config.save("device.json", self.device)

    def heartbeat(self):
        if self.device:
            self.supa.rest("PATCH", f"devices?id=eq.{self.device['id']}",
                           {"lan_addr": local_ip(), "last_seen": "now()", "cert_sha256": self.identity.fingerprint})

    def refresh_devices(self):
        self.devices = self.supa.rest("GET", "devices?select=id,name,kind,cert_sha256,lan_addr,last_seen&order=name") or []
        return self.devices

    def others(self):
        return [d for d in self.devices if not self.device or d["id"] != self.device["id"]]

    def is_online(self, dev):
        """Nearby: announced itself on this network in the last few seconds (can send)."""
        return bool(self.discovery and self.discovery.online(dev["id"]))

    @staticmethod
    def seen_recently(dev):
        """Signed in and running somewhere: checked in with the account server in the last 2.5 minutes."""
        import datetime
        try:
            t = datetime.datetime.fromisoformat(str(dev.get("last_seen")).replace(" ", "T"))
            return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() < 150
        except ValueError:
            return False

    def history(self):
        return self.supa.rest("GET", "transfers?select=kind,name,size,ok,created_at,from_device,to_device&order=created_at.desc&limit=200") or []

    def log(self, kind, name, size, to_device=None, from_device=None, ok=True):
        try:
            self.supa.rest("POST", "transfers", {"kind": kind, "name": (name or "")[:255], "size": size, "ok": ok,
                                                  "to_device": to_device, "from_device": from_device})
        except SupaError:
            pass

    def export_data(self, path):
        import json
        data = {"profile": self.supa.rest("GET", "profiles?select=*"),
                "devices": self.supa.rest("GET", "devices?select=*"),
                "history": self.supa.rest("GET", "transfers?select=*")}
        pathlib.Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def delete_account(self):
        self.supa.rpc("delete_my_account")
        self.supa.sign_out()
        self._forget_this_device()

    def remove_device(self, device_id):
        self.supa.rest("DELETE", f"devices?id=eq.{device_id}")

    def remove_this_device(self):
        """Remove this computer from the account (other devices stop seeing it), wipe its
        identity key, and sign out. Signing in again registers it as a new device."""
        if self.device:
            self.remove_device(self.device["id"])
        self.supa.sign_out()
        self._forget_this_device()

    def _forget_this_device(self):
        config.forget("device.json")
        for f in ("cert.pem", "key.pem"):
            config.forget(f)
        self.device = None

    def sign_out(self):
        """Sign out but keep this computer in the device list (shown offline); signing in
        again with the same account reuses it."""
        self.supa.sign_out()

    def set_clipboard_sync(self, on):
        self.clipboard_sync = on
        prefs = config.load("prefs.json", {}) or {}
        prefs["clipboard"] = on
        config.save("prefs.json", prefs)

    # --- running ------------------------------------------------------------
    def start(self):
        self.refresh_devices()
        self.discovery = Discovery(self.device["id"], on_change=self.ui.changed)
        self.discovery.start()
        threading.Thread(target=self._serve, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def _heartbeat_loop(self):
        while True:
            try:
                self.heartbeat()
                self.refresh_devices()
                self.ui.changed()
            except SupaError:
                pass
            time.sleep(60)

    def _serve(self):
        ctx = self.identity.server_context()
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("", config.TCP_PORT))
        srv.listen(8)
        self.server = srv
        while True:
            conn, addr = srv.accept()
            threading.Thread(target=self._handle, args=(conn, ctx), daemon=True).start()

    def _owner_of(self, token):
        hit = self.token_cache.get(token)
        if hit and time.time() - hit[1] < 300:
            return hit[0]
        uid = Supa.verify_token(token)
        self.token_cache[token] = (uid, time.time())
        return uid

    def _device(self, device_id):
        for d in self.devices:
            if d["id"] == device_id:
                return d
        self.refresh_devices()
        return next((d for d in self.devices if d["id"] == device_id), None)

    def _handle(self, conn, ctx):
        try:
            conn.settimeout(20)
            s = ctx.wrap_socket(conn, server_side=True)
            hello = recv_header(s)
            if hello.get("t") != "hello":
                return
            # Only devices signed in to the same account may talk to us.
            try:
                owner = self._owner_of(hello.get("token", ""))
            except SupaError:
                owner = None
            dev = self._device(hello.get("device")) if owner == self.supa.user_id else None
            if not dev:
                send_msg(s, {"t": "err", "msg": "not your device"})
                return
            send_msg(s, {"t": "ok", "name": self.device["name"]})
            req = recv_header(s)
            kind = req.get("t")
            if kind == "text":
                send_msg(s, {"t": "done", "ok": True})
                self.ui.received_text(dev["name"], str(req.get("text", "")))
            elif kind == "clip":
                send_msg(s, {"t": "done", "ok": True})
                if self.clipboard_sync:
                    set_clipboard(str(req.get("text", "")))
            elif kind == "file":
                self._receive_file(s, dev, req)
            elif kind == "control":
                s.settimeout(None)
                self._be_controlled(s, dev)
        except (OSError, ConnectionError, ValueError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def _receive_file(self, s, dev, req):
        name = os.path.basename(str(req.get("name", "file"))).strip() or "file"
        name = "".join(c for c in name if c not in '\\/:*?"<>|\0')[:200] or "file"
        size, want = int(req["size"]), str(req.get("sha256", ""))
        out = unique_path(config.downloads_dir() / name)
        part = out.with_name(out.name + ".part")
        h, got = hashlib.sha256(), 0
        s.settimeout(60)
        with open(part, "wb") as f:
            while got < size:
                chunk = s.recv(min(CHUNK, size - got))
                if not chunk:
                    raise ConnectionError("transfer interrupted")
                f.write(chunk)
                h.update(chunk)
                got += len(chunk)
                self.ui.progress(f"Receiving {name}", got, size)
        ok = h.hexdigest() == want
        if ok:
            os.replace(part, out)
        else:
            part.unlink(missing_ok=True)
        send_msg(s, {"t": "done", "ok": ok})
        if ok:
            self.ui.received_file(dev["name"], str(out))

    # --- outgoing -----------------------------------------------------------
    def _open(self, dev):
        addr = self.discovery.address(dev["id"]) if self.discovery else None
        if not addr and dev.get("lan_addr"):
            addr = (dev["lan_addr"], config.TCP_PORT)
        if not addr:
            raise ConnectionError(f"{dev['name']} is not on this network")
        s = client_connect(addr[0], addr[1], dev.get("cert_sha256"))
        send_msg(s, {"t": "hello", "device": self.device["id"], "token": self.supa.token(), "v": config.PROTOCOL})
        r = recv_header(s)
        if r.get("t") != "ok":
            s.close()
            raise ConnectionError(r.get("msg", "refused"))
        return s

    def send_text(self, dev, text, kind="text"):
        s = self._open(dev)
        try:
            send_msg(s, {"t": "text" if kind == "text" else "clip", "text": text})
            ok = recv_header(s).get("ok", False)
        finally:
            s.close()
        if kind == "text":
            self.log("text", text[:60], len(text.encode()), to_device=dev["id"], from_device=self.device["id"], ok=ok)
        return ok

    def send_file(self, dev, path):
        path = pathlib.Path(path)
        size = path.stat().st_size
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK), b""):
                h.update(chunk)
        s = self._open(dev)
        try:
            send_msg(s, {"t": "file", "name": path.name, "size": size, "sha256": h.hexdigest()})
            sent = 0
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(CHUNK), b""):
                    s.sendall(chunk)
                    sent += len(chunk)
                    self.ui.progress(f"Sending {path.name}", sent, size)
            ok = bool(recv_header(s).get("ok"))
        finally:
            s.close()
        self.log("file", path.name, size, to_device=dev["id"], from_device=self.device["id"], ok=ok)
        return ok

    def share_clipboard(self, text):
        for d in self.others():
            if self.is_online(d):
                try:
                    self.send_text(d, text, kind="clip")
                except (OSError, ConnectionError, SupaError):
                    pass

    # --- take control -------------------------------------------------------
    def take_control(self, dev, on_frame, on_end):
        """Start controlling `dev`. Returns a ControlSession, or raises if refused."""
        s = self._open(dev)
        send_msg(s, {"t": "control"})
        r = recv_header(s)
        if r.get("t") != "accept":
            s.close()
            raise ConnectionError(f"{dev['name']} did not accept")
        self.log("control", dev["name"], 0, to_device=dev["id"], from_device=self.device["id"])
        return ControlSession(s, r, on_frame, on_end)

    def _be_controlled(self, s, dev):
        if not self.ui.ask_control(dev["name"]):
            send_msg(s, {"t": "deny"})
            return
        from . import control
        try:
            screen, inp = control.Screen(), control.Input()
        except Exception as e:  # missing grim / uinput access
            send_msg(s, {"t": "deny", "msg": str(e)})
            return
        send_msg(s, {"t": "accept", "w": screen.width, "h": screen.height, "kind": "computer"})
        stop = threading.Event()
        self.controlled = s
        self.ui.control_started(dev["name"], stop.set)

        def reader():
            try:
                while not stop.is_set():
                    h = recv_header(s)
                    if h.get("t") == "bye":
                        break
                    if h.get("t") == "input":
                        inp.handle(h)
            except (OSError, ConnectionError, ValueError):
                pass
            stop.set()

        threading.Thread(target=reader, daemon=True).start()
        try:
            while not stop.is_set():
                t0 = time.time()
                frame = screen.grab()
                if frame:
                    send_msg(s, {"t": "frame"}, frame)
                time.sleep(max(0, 0.08 - (time.time() - t0)))
        except (OSError, ConnectionError):
            pass
        finally:
            stop.set()
            inp.close()
            try:
                send_msg(s, {"t": "bye"})
            except OSError:
                pass
            self.controlled = None
            self.ui.control_ended()


class ControlSession:
    def __init__(self, sock, info, on_frame, on_end):
        self.sock, self.info = sock, info
        self.on_frame, self.on_end = on_frame, on_end
        self.lock = threading.Lock()
        self.closed = False
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        try:
            while True:
                h, data = recv_msg(self.sock)
                if h.get("t") == "frame":
                    self.on_frame(data)
                elif h.get("t") == "bye":
                    break
        except (OSError, ConnectionError, ValueError):
            pass
        self.close()

    def send(self, event):
        if self.closed:
            return
        try:
            with self.lock:
                send_msg(self.sock, dict(event, t="input"))
        except OSError:
            self.close()

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            with self.lock:
                send_msg(self.sock, {"t": "bye"})
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass
        self.on_end()


def unique_path(p: pathlib.Path) -> pathlib.Path:
    if not p.exists():
        return p
    stem, suf, i = p.stem, p.suffix, 2
    while True:
        q = p.with_name(f"{stem} ({i}){suf}")
        if not q.exists():
            return q
        i += 1


def set_clipboard(text):
    import subprocess
    try:
        subprocess.run(["wl-copy"], input=text.encode(), timeout=5)
    except (OSError, subprocess.SubprocessError):
        pass
