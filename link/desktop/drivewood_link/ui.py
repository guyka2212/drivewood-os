"""DriveWood Link window (GTK 4)."""
import json
import os
import pathlib
import re
import subprocess
import sys
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa: E402

from . import config  # noqa: E402
from .core import LinkCore  # noqa: E402
from .supa import SupaError  # noqa: E402

LEGAL = pathlib.Path(__file__).with_name("legal")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USER_RE = re.compile(r"^[a-z0-9_]{3,24}$")


# Sea-glass theme: deep pine background, sea-glass teal accent, pale sand for "away".
BG, CARD, CARD2 = "#0f1513", "#161f1c", "#1d2925"
TEXT, MUTED = "#e6ebe7", "#8fa199"
ACCENT, ON_ACCENT, SAND = "#4fd1b5", "#06201a", "#d8c9a3"


def css():
    return f"""
    window {{ background: {BG}; color: {TEXT}; }}
    .title {{ font-size: 22px; font-weight: 700; }}
    .muted {{ color: {MUTED}; }}
    .error {{ color: #ff8f8f; }}
    entry {{ background: {CARD2}; color: {TEXT}; border: 1px solid transparent; border-radius: 12px; min-height: 38px;
             box-shadow: none; transition: border-color 200ms ease, box-shadow 200ms ease; }}
    entry:focus-within {{ border-color: {ACCENT}; box-shadow: 0 0 0 3px alpha({ACCENT}, 0.18); }}
    button {{ background: {CARD2}; color: {TEXT}; border: none; border-radius: 12px; box-shadow: none;
              transition: background 180ms ease, transform 120ms ease, opacity 180ms ease; }}
    button:hover {{ background: shade({CARD2}, 1.3); }}
    button:active {{ transform: scale(0.96); }}
    button:disabled {{ opacity: 0.4; }}
    button.accent {{ background: {ACCENT}; color: {ON_ACCENT}; font-weight: 700; }}
    button.accent:hover {{ background: shade({ACCENT}, 1.08); }}
    button.accent:disabled {{ background: alpha({ACCENT}, 0.22); color: alpha({TEXT}, 0.45); opacity: 1; }}
    button.destructive-action {{ color: #ff8f8f; }}
    stackswitcher button {{ min-width: 92px; }}
    stackswitcher button:checked {{ background: {ACCENT}; color: {ON_ACCENT}; font-weight: 700; }}
    .devrow {{ background: {CARD}; border-radius: 14px; padding: 4px; transition: background 200ms ease; }}
    .devrow:hover {{ background: {CARD2}; }}
    .dot-on {{ color: {ACCENT}; animation: pulse 1.6s ease-in-out infinite; }}
    .dot-away {{ color: {SAND}; }}
    .dot-off {{ color: #46524d; }}
    @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} 100% {{ opacity: 1; }} }}
    .spinning {{ animation: spin 0.8s linear infinite; }}
    @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
    checkbutton check {{ border-radius: 6px; background: {CARD2}; }}
    checkbutton check:checked {{ background: {ACCENT}; color: {ON_ACCENT}; }}
    progressbar progress {{ background: {ACCENT}; border-radius: 6px; }}
    progressbar trough {{ background: {CARD2}; border-radius: 6px; }}
    link, button.link {{ color: {ACCENT}; }}
    textview, textview text {{ background: {CARD}; color: {TEXT}; }}
    .banner {{ background: {ACCENT}; color: {ON_ACCENT}; padding: 8px 14px; border-radius: 12px; font-weight: 700; }}
    """


def reveal(widget, delay_ms=0):
    """Wrap a widget so it slides and fades in after `delay_ms` (staggered list entrance)."""
    r = Gtk.Revealer(transition_type=Gtk.RevealerTransitionType.SLIDE_DOWN, transition_duration=260, reveal_child=False)
    r.set_child(widget)
    GLib.timeout_add(max(1, delay_ms), lambda: (r.set_reveal_child(True), False)[1])
    return r


def clear(container):
    while (c := container.get_first_child()) is not None:
        container.remove(c)


def bg(fn, done=None, fail=None):
    """Run fn in a thread; report back on the GTK thread."""
    def run():
        try:
            r = fn()
        except Exception as e:  # shown to the user
            if fail:
                GLib.idle_add(fail, str(e))
            return
        if done:
            GLib.idle_add(done, r)
    threading.Thread(target=run, daemon=True).start()


def label(text, *classes, wrap=False, xalign=0.0):
    w = Gtk.Label(label=text, xalign=xalign, wrap=wrap)
    for c in classes:
        w.add_css_class(c)
    return w


def box(vertical=True, spacing=10, margin=0):
    b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL if vertical else Gtk.Orientation.HORIZONTAL, spacing=spacing)
    for side in ("top", "bottom", "start", "end"):
        getattr(b, f"set_margin_{side}")(margin)
    return b


def markdown_blocks(text):
    """Turn the legal Markdown into (kind, text) blocks: h1, h2, item, para.
    Lines of one paragraph are joined, backticks are dropped, table rows become items."""
    out, para = [], []

    def flush():
        if para:
            out.append(("para", " ".join(para)))
            para.clear()
    for raw in text.splitlines():
        line = raw.strip().replace("`", "")
        if not line:
            flush()
        elif line.startswith("# "):
            flush(); out.append(("h1", line[2:]))
        elif line.startswith("## "):
            flush(); out.append(("h2", line[3:]))
        elif line.startswith("|"):
            flush()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if not all(set(c) <= set("-: ") for c in cells):
                out.append(("item", "  •  " + "  —  ".join(cells)))
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            flush(); out.append(("item", "  " + ("•  " + line[2:] if line.startswith("- ") else line)))
        else:
            para.append(line)
    flush()
    return out


def notify(title, body):
    try:
        subprocess.Popen(["notify-send", "-a", "DriveWood Link", title, body])
    except OSError:
        pass


class GtkUI:
    """Callbacks from the engine (network threads) marshalled onto the GTK thread."""

    def __init__(self, win):
        self.win = win

    def ask_control(self, name):
        ev, answer = threading.Event(), [False]

        def ask():
            d = Gtk.AlertDialog(message=f"{name} wants to take control of this computer",
                                detail="They will see your screen and use your mouse and keyboard. "
                                       "You can stop it at any time.",
                                buttons=["Deny", "Allow"], cancel_button=0, default_button=0)
            self.win.present()

            def chosen(dlg, res):
                try:
                    answer[0] = dlg.choose_finish(res) == 1
                except GLib.Error:
                    answer[0] = False
                ev.set()
            d.choose(self.win, None, chosen)
        GLib.idle_add(ask)
        ev.wait(60)
        return answer[0]

    def control_started(self, name, stop):
        GLib.idle_add(self.win.show_banner, name, stop)

    def control_ended(self):
        GLib.idle_add(self.win.hide_banner)

    def received_text(self, name, text):
        GLib.idle_add(self.win.show_text, name, text)

    def received_file(self, name, path):
        notify(f"File from {name}", os.path.basename(path))
        GLib.idle_add(self.win.refresh)

    def progress(self, text, done, total):
        GLib.idle_add(self.win.set_progress, text, done / total if total else 1.0)

    def changed(self):
        GLib.idle_add(self.win.refresh)


class LinkWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="DriveWood Link", default_width=520, default_height=640)
        self.core = LinkCore(GtkUI(self))
        self.started = False
        self.banner = None
        self.connect("close-request", self._hide)
        prov = Gtk.CssProvider()
        prov.load_from_string(css())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), prov,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        # main window: a welcome screen until signed in, then the devices
        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE, transition_duration=300)
        self.set_child(self.stack)
        self.stack.add_named(self._welcome_page(), "welcome")
        self.stack.add_named(self._main_page(), "main")
        # sign in / sign up / terms / device name (the whole app is a small floating window)
        self.auth_stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, vhomogeneous=False)
        self.auth_stack.add_named(self._signin_page(), "signin")
        self.auth_stack.add_named(self._signup_page(), "signup")
        self.auth_stack.add_named(self._legal_page(), "legal")
        self.auth_stack.add_named(self._name_page(), "name")
        self.stack.add_named(self.auth_stack, "auth")
        self.route()

    def _hide(self, *_):
        self.set_visible(False)  # keeps running in the background
        return True

    # --- flow ---------------------------------------------------------------
    def route(self):
        if not self.core.supa.signed_in:
            self.show_auth("signin")
            return

        def check():
            return self.core.legal_ok()

        def done(ok):
            if not ok:
                self.show_auth("legal")
            elif not self.core.device:
                self.show_auth("name")
            else:
                self.go_main()
        bg(check, done, lambda e: self._fatal(e))

    def _fatal(self, msg):
        self.signin_err.set_text(msg)
        self.show_auth("signin")

    def show_auth(self, page):
        """Open the sign-in pop-up on a page (only when the main window is on screen)."""
        self.auth_stack.set_visible_child_name(page)
        self.stack.set_visible_child_name("auth")

    def open(self):
        self.present()
        if self.stack.get_visible_child_name() in ("welcome", "auth"):
            self.route()

    def _welcome_page(self):
        b = box(margin=40)
        b.set_valign(Gtk.Align.CENTER)
        b.set_halign(Gtk.Align.CENTER)
        b.append(label("DriveWood Link", "title", xalign=0.5))
        b.append(label("Send files and take control across your own devices.", "muted", wrap=True, xalign=0.5))
        go = Gtk.Button(label="Sign in")
        go.add_css_class("accent")
        go.connect("clicked", lambda *_: self.show_auth("signin"))
        new = Gtk.Button(label="Create an account")
        new.connect("clicked", lambda *_: self.show_auth("signup"))
        b.append(go)
        b.append(new)
        return b

    def go_main(self):
        self.stack.set_visible_child_name("main")
        GLib.timeout_add(350, lambda: (self.refresh(animate=True), False)[1])
        if not self.started:
            self.started = True
            bg(lambda: (self.core.heartbeat(), self.core.start()), lambda _: self.refresh(),
               lambda e: self.status.set_text(e))
            if self.core.clipboard_sync:
                self._watch_clipboard()
        self.refresh()

    # --- pages ----------------------------------------------------------------
    def _signin_page(self):
        b = box(margin=28)
        b.append(label("DriveWood Link", "title"))
        b.append(label("Send files and take control across your own devices.", "muted", wrap=True))
        self.si_email = Gtk.Entry(placeholder_text="Email")
        self.si_pass = Gtk.PasswordEntry(placeholder_text="Password", show_peek_icon=True)
        self.signin_err = label("", "error", wrap=True)
        go = Gtk.Button(label="Sign in")
        go.add_css_class("accent")
        go.connect("clicked", self._do_signin)
        self.si_pass.connect("activate", self._do_signin)
        new = Gtk.Button(label="Create an account")
        new.connect("clicked", lambda *_: self.show_auth("signup"))
        for w in (self.si_email, self.si_pass, go, self.signin_err, new):
            b.append(w)
        return b

    def _do_signin(self, *_):
        email, pw = self.si_email.get_text().strip(), self.si_pass.get_text()
        self.signin_err.set_text("Signing in…")
        bg(lambda: self.core.supa.sign_in(email, pw), lambda _: self.route(),
           lambda e: self.signin_err.set_text(e))

    def _legal_link(self, text, doc):
        btn = Gtk.LinkButton(label=text, uri="about:blank")
        btn.connect("activate-link", lambda *_: (self.show_doc(doc), True)[1])
        return btn

    def _consent_box(self):
        row = box(vertical=False, spacing=8)
        check = Gtk.CheckButton()  # unticked by default
        row.append(check)
        col = box(spacing=2)
        col.append(label("I am at least 13 (16 in the EEA/UK) and I agree to the", wrap=True))
        links = box(vertical=False, spacing=4)
        links.append(self._legal_link("Terms of Use", "TERMS.md"))
        links.append(label("and the"))
        links.append(self._legal_link("Privacy Policy", "PRIVACY.md"))
        col.append(links)
        row.append(col)
        return row, check

    def _signup_page(self):
        b = box(margin=28)
        b.append(label("Create your account", "title"))
        self.su_email = Gtk.Entry(placeholder_text="Email")
        self.su_user = Gtk.Entry(placeholder_text="Username (a-z, 0-9, _)")
        self.su_pass = Gtk.PasswordEntry(placeholder_text="Password (8+ characters)", show_peek_icon=True)
        consent, self.su_consent = self._consent_box()
        self.su_btn = Gtk.Button(label="Create account", sensitive=False)
        self.su_btn.add_css_class("accent")
        self.su_consent.connect("toggled", lambda c: self.su_btn.set_sensitive(c.get_active()))
        self.su_btn.connect("clicked", self._do_signup)
        self.signup_msg = label("", "error", wrap=True)
        back = Gtk.Button(label="I already have an account")
        back.connect("clicked", lambda *_: self.show_auth("signin"))
        for w in (self.su_email, self.su_user, self.su_pass, consent, self.su_btn, self.signup_msg, back):
            b.append(w)
        return b

    def _do_signup(self, *_):
        email, user, pw = self.su_email.get_text().strip(), self.su_user.get_text().strip().lower(), self.su_pass.get_text()
        if not self.su_consent.get_active():
            return self.signup_msg.set_text("Please accept the Terms of Use and the Privacy Policy.")
        if not EMAIL_RE.match(email):
            return self.signup_msg.set_text("Enter a valid email address.")
        if not USER_RE.match(user):
            return self.signup_msg.set_text("Username: 3–24 characters, a–z, 0–9 or _.")
        if len(pw) < 8:
            return self.signup_msg.set_text("Password must be at least 8 characters.")
        self.signup_msg.set_text("Creating your account…")

        def done(signed_in):
            if signed_in:
                self.route()
            else:
                self.si_email.set_text(email)
                self.signin_err.set_text("Account created. Open the link we emailed you, then sign in.")
                self.show_auth("signin")
        bg(lambda: self.core.supa.sign_up(email, pw, user, True, True), done,
           lambda e: self.signup_msg.set_text(e))

    def _legal_page(self):
        b = box(margin=28)
        b.append(label("Updated Terms and Privacy Policy", "title", wrap=True))
        b.append(label("Please read and accept them to keep using DriveWood Link. If you don't agree, "
                       "you can export your data and delete your account in Account.", "muted", wrap=True))
        consent, check = self._consent_box()
        go = Gtk.Button(label="Accept and continue", sensitive=False)
        go.add_css_class("accent")
        check.connect("toggled", lambda c: go.set_sensitive(c.get_active()))
        msg = label("", "error", wrap=True)
        go.connect("clicked", lambda *_: bg(self.core.accept_legal, lambda _: self.route(), msg.set_text))
        out = Gtk.Button(label="Sign out")
        out.connect("clicked", lambda *_: self._sign_out())
        for w in (consent, go, msg, out):
            b.append(w)
        return b

    def _name_page(self):
        b = box(margin=28)
        b.append(label("Name this computer", "title"))
        b.append(label("Your other devices will see this name.", "muted"))
        self.name_entry = Gtk.Entry(text=GLib.get_host_name()[:40])
        msg = label("", "error", wrap=True)
        go = Gtk.Button(label="Continue")
        go.add_css_class("accent")
        go.connect("clicked", lambda *_: bg(lambda: self.core.register_device(self.name_entry.get_text()),
                                            lambda _: self.go_main(), msg.set_text))
        for w in (self.name_entry, go, msg):
            b.append(w)
        return b

    def _main_page(self):
        outer = box(spacing=0)
        switcher = Gtk.StackSwitcher(halign=Gtk.Align.CENTER, margin_top=12)
        self.tabs = Gtk.Stack(transition_type=Gtk.StackTransitionType.SLIDE_LEFT_RIGHT, transition_duration=220)
        switcher.set_stack(self.tabs)
        outer.append(switcher)
        self.devlist = box(spacing=8)
        dev = box(margin=16)
        head = box(vertical=False, spacing=8)
        self.status = label("", "muted", wrap=True)
        self.status.set_hexpand(True)
        head.append(self.status)
        self.refresh_btn = Gtk.Button(tooltip_text="Refresh")
        self.refresh_icon = Gtk.Image(icon_name="view-refresh-symbolic")
        self.refresh_btn.set_child(self.refresh_icon)
        self.refresh_btn.connect("clicked", lambda *_: self.manual_refresh())
        head.append(self.refresh_btn)
        dev.append(head)
        dev.append(self.devlist)
        self.progress = Gtk.ProgressBar(visible=False, show_text=True)
        dev.append(self.progress)
        sc = Gtk.ScrolledWindow(vexpand=True)
        sc.set_child(dev)
        self.tabs.add_titled(sc, "devices", "Devices")
        self.histlist = box(spacing=6)
        hb = box(margin=16)
        hb.append(self.histlist)
        clear = Gtk.Button(label="Clear history")
        clear.connect("clicked", lambda *_: bg(lambda: self.core.supa.rest("DELETE", f"transfers?owner=eq.{self.core.supa.user_id}"),
                                               lambda _: self.refresh_history()))
        hb.append(clear)
        hs = Gtk.ScrolledWindow(vexpand=True)
        hs.set_child(hb)
        self.tabs.add_titled(hs, "history", "History")
        self.tabs.connect("notify::visible-child-name", lambda *_: self.refresh_history())
        self.tabs.add_titled(self._account_tab(), "account", "Account")
        outer.append(self.tabs)
        return outer

    def _account_tab(self):
        b = box(margin=16)
        self.acct = label("", "muted", wrap=True)
        b.append(self.acct)
        clip = Gtk.CheckButton(label="Share clipboard with my online devices", active=self.core.clipboard_sync)
        clip.connect("toggled", lambda c: (self.core.set_clipboard_sync(c.get_active()),
                                           c.get_active() and self._watch_clipboard()))
        b.append(clip)
        rename = Gtk.Button(label="Rename this computer")
        rename.connect("clicked", lambda *_: self.show_auth("name"))
        export = Gtk.Button(label="Export my data (JSON)")
        export.connect("clicked", self._export)
        docs = box(vertical=False, spacing=6)
        docs.append(self._legal_link("Terms of Use", "TERMS.md"))
        docs.append(self._legal_link("Privacy Policy", "PRIVACY.md"))
        out = Gtk.Button(label="Sign out")
        out.connect("clicked", lambda *_: self._sign_out())
        remove = Gtk.Button(label="Remove this device")
        remove.add_css_class("destructive-action")
        remove.connect("clicked", self._remove_device)
        delete = Gtk.Button(label="Delete my account")
        delete.add_css_class("destructive-action")
        delete.connect("clicked", self._delete)
        for w in (rename, export, docs, out, remove, delete):
            b.append(w)
        sc = Gtk.ScrolledWindow(vexpand=True)
        sc.set_child(b)
        return sc

    # --- devices ------------------------------------------------------------
    def manual_refresh(self):
        """Refresh button: spin the icon while the device list reloads, then animate the rows in."""
        if self.refresh_icon.has_css_class("spinning"):
            return
        self.refresh_icon.add_css_class("spinning")
        self.refresh_btn.set_sensitive(False)

        def done(_=None):
            self.refresh_icon.remove_css_class("spinning")
            self.refresh_btn.set_sensitive(True)
            self.refresh(animate=True)
        bg(lambda: (self.core.heartbeat(), self.core.refresh_devices()), done,
           lambda e: (done(), self._error(e)))

    def refresh(self, animate=False):
        if self.stack.get_visible_child_name() != "main":
            return
        clear(self.devlist)
        me = self.core.device or {}
        self.acct.set_text(f"Signed in as {getattr(self.core, 'username', '')}\nThis computer: {me.get('name', '')}")
        others = self.core.others()
        self.status.set_text("No other devices yet. Install DriveWood Link on your phone or another computer "
                             "and sign in with the same account." if not others else
                             "Drop files on a device to send them.")
        for i, d in enumerate(others):
            row = self._device_row(d)
            self.devlist.append(reveal(row, 40 + i * 70) if animate else row)

    def _device_row(self, d):
        on = self.core.is_online(d)
        elsewhere = not on and self.core.seen_recently(d)
        row = box(vertical=False, spacing=10, margin=10)
        row.add_css_class("devrow")
        dot = label("●", "dot-on" if on else "dot-away" if elsewhere else "dot-off")
        row.append(dot)
        info = box(spacing=0)
        info.set_hexpand(True)
        info.append(label(d["name"]))
        state = " · nearby" if on else " · online, on another network" if elsewhere else " · offline"
        info.append(label(("Phone" if d["kind"] == "phone" else "Computer") + state, "muted", wrap=True))
        if elsewhere:
            row.set_tooltip_text("Signed in and running, but not on this Wi-Fi. Connect both devices to the same network to send or take control.")
        row.append(info)
        for text, fn in (("Files", self._pick_files), ("Text", self._ask_text), ("Take control", self._control)):
            btn = Gtk.Button(label=text, sensitive=on)
            btn.connect("clicked", lambda _b, f=fn, dev=d: f(dev))
            row.append(btn)
        drop = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop.connect("drop", lambda _t, value, _x, _y, dev=d: self._send_paths(dev, [f.get_path() for f in value.get_files()]) or True)
        row.add_controller(drop)
        return row

    def _pick_files(self, dev):
        dlg = Gtk.FileDialog(title=f"Send to {dev['name']}")

        def done(d, res):
            try:
                files = d.open_multiple_finish(res)
            except GLib.Error:
                return
            self._send_paths(dev, [files.get_item(i).get_path() for i in range(files.get_n_items())])
        dlg.open_multiple(self, None, done)

    def _send_paths(self, dev, paths):
        paths = [p for p in paths if p and os.path.isfile(p)]
        if not paths:
            return

        def work():
            return [(os.path.basename(p), self.core.send_file(dev, p)) for p in paths]

        def done(res):
            self.progress.set_visible(False)
            bad = [n for n, ok in res if not ok]
            notify(f"Sent to {dev['name']}" if not bad else "Some files failed",
                   ", ".join(n for n, _ in res) if not bad else ", ".join(bad))
        self.progress.set_visible(True)
        bg(work, done, lambda e: (self.progress.set_visible(False), self._error(e)))

    def _ask_text(self, dev):
        win = Gtk.Window(title=f"Text to {dev['name']}", transient_for=self, modal=True, default_width=420)
        b = box(margin=16)
        view = Gtk.TextView(wrap_mode=Gtk.WrapMode.WORD_CHAR, height_request=140)
        b.append(view)
        send = Gtk.Button(label="Send")
        send.add_css_class("accent")

        def go(*_):
            buf = view.get_buffer()
            text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
            if text.strip():
                bg(lambda: self.core.send_text(dev, text), lambda _: notify("Sent", f"Text to {dev['name']}"), self._error)
            win.close()
        send.connect("clicked", go)
        b.append(send)
        win.set_child(b)
        win.present()

    def _control(self, dev):
        ControlWindow(self, dev).start()

    # --- incoming -------------------------------------------------------------
    def show_text(self, name, text):
        notify(f"Text from {name}", text[:120])
        d = Gtk.AlertDialog(message=f"Text from {name}", detail=text, buttons=["Close", "Copy"])

        def chosen(dlg, res):
            try:
                if dlg.choose_finish(res) == 1:
                    Gdk.Display.get_default().get_clipboard().set(text)
            except GLib.Error:
                pass
        d.choose(self, None, chosen)

    def show_banner(self, name, stop):
        self.hide_banner()
        w = Gtk.Window(title="DriveWood Link remote control", decorated=False, resizable=False)
        row = box(vertical=False, spacing=12, margin=0)
        row.add_css_class("banner")
        row.append(label(f"Being controlled by {name}"))
        btn = Gtk.Button(label="Stop")
        btn.connect("clicked", lambda *_: stop())
        row.append(btn)
        w.set_child(row)
        w.present()
        self.banner = w
        notify("Remote control started", f"{name} is controlling this computer. Use the banner to stop.")

    def hide_banner(self):
        if self.banner:
            self.banner.destroy()
            self.banner = None

    def set_progress(self, text, frac):
        self.progress.set_visible(frac < 1.0)
        self.progress.set_fraction(frac)
        self.progress.set_text(text)

    def refresh_history(self):
        if self.tabs.get_visible_child_name() != "history":
            return
        names = {d["id"]: d["name"] for d in self.core.devices}

        def fill(rows):
            clear(self.histlist)
            if not rows:
                self.histlist.append(label("Nothing sent yet.", "muted"))
            for i, r in enumerate(rows):
                what = {"file": "File", "text": "Text", "clipboard": "Clipboard", "control": "Remote control"}[r["kind"]]
                line = f"{what}: {r.get('name') or ''}"
                sub = f"{names.get(r.get('from_device'), '?')} → {names.get(r.get('to_device'), '?')} · {r['created_at'][:16].replace('T', ' ')}"
                if not r["ok"]:
                    sub += " · failed"
                b = box(spacing=0, margin=8)
                b.add_css_class("devrow")
                b.append(label(line, wrap=True))
                b.append(label(sub, "muted"))
                self.histlist.append(reveal(b, 30 + min(i, 12) * 40))
        bg(self.core.history, fill, self._error)

    # --- account --------------------------------------------------------------
    def _export(self, *_):
        dlg = Gtk.FileDialog(title="Export my data", initial_name="drivewood-link-data.json")

        def done(d, res):
            try:
                f = d.save_finish(res)
            except GLib.Error:
                return
            bg(lambda: self.core.export_data(f.get_path()), lambda _: notify("Exported", f.get_path()), self._error)
        dlg.save(self, None, done)

    def _delete(self, *_):
        d = Gtk.AlertDialog(message="Delete your DriveWood Link account?",
                            detail="Your account, devices and history are deleted permanently. This can't be undone.",
                            buttons=["Cancel", "Delete account"], cancel_button=0, default_button=0)

        def chosen(dlg, res):
            try:
                if dlg.choose_finish(res) == 1:
                    bg(self.core.delete_account, lambda _: self._after_signout(), self._error)
            except GLib.Error:
                pass
        d.choose(self, None, chosen)

    def _remove_device(self, *_):
        name = (self.core.device or {}).get("name", "this computer")
        d = Gtk.AlertDialog(message=f"Remove {name} from your account?",
                            detail="Your other devices will stop seeing it, and it will be signed out. "
                                   "Your account and your other devices are not affected.",
                            buttons=["Cancel", "Remove device"], cancel_button=0, default_button=0)

        def chosen(dlg, res):
            try:
                if dlg.choose_finish(res) == 1:
                    bg(self.core.remove_this_device, lambda _: self._after_signout(), self._error)
            except GLib.Error:
                pass
        d.choose(self, None, chosen)

    def _sign_out(self):
        bg(self.core.sign_out, lambda _: self._after_signout(), self._error)

    def _after_signout(self):
        # restart cleanly so the server and discovery stop with the old session
        os.execv(sys.executable, [sys.executable, "-m", "drivewood_link"])

    # --- helpers --------------------------------------------------------------
    def show_doc(self, name):
        text = (LEGAL / name).read_text(encoding="utf-8")
        win = Gtk.Window(title="Terms of Use" if name.startswith("TERMS") else "Privacy Policy", transient_for=self, default_width=560, default_height=620)
        view = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD, left_margin=16, right_margin=16,
                            top_margin=12, bottom_margin=12)
        buf = view.get_buffer()
        h1 = buf.create_tag("h1", weight=700, scale=1.5, pixels_below_lines=6)
        h2 = buf.create_tag("h2", weight=700, scale=1.15, pixels_above_lines=10, pixels_below_lines=4)
        bold = buf.create_tag("b", weight=700)
        for kind, line in markdown_blocks(text):
            tag = {"h1": h1, "h2": h2}.get(kind)
            if tag:
                buf.insert_with_tags(buf.get_end_iter(), line + "\n", tag)
                continue
            for i, part in enumerate(line.split("**")):  # odd parts were **bold**
                if i % 2:
                    buf.insert_with_tags(buf.get_end_iter(), part, bold)
                else:
                    buf.insert(buf.get_end_iter(), part)
            buf.insert(buf.get_end_iter(), "\n" if kind == "item" else "\n\n")
        sc = Gtk.ScrolledWindow()
        sc.set_child(view)
        win.set_child(sc)
        win.present()

    def _error(self, msg):
        Gtk.AlertDialog(message="DriveWood Link", detail=str(msg)).show(self)

    def _watch_clipboard(self):
        last = {"text": None}

        def loop():
            try:
                p = subprocess.Popen(["wl-paste", "--type", "text", "--watch", "echo"], stdout=subprocess.PIPE, text=True)
            except OSError:
                return
            for _ in p.stdout:
                if not self.core.clipboard_sync:
                    p.terminate()
                    return
                try:
                    text = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True, timeout=5).stdout
                except (OSError, subprocess.SubprocessError):
                    continue
                if text and text != last["text"] and len(text) < 1_000_000:
                    last["text"] = text
                    self.core.share_clipboard(text)
        threading.Thread(target=loop, daemon=True).start()


class ControlWindow(Gtk.Window):
    """Shows the other device's screen and sends our mouse and keyboard to it."""

    def __init__(self, parent, dev):
        super().__init__(title=f"Controlling {dev['name']}", default_width=1100, default_height=700)
        self.parent, self.dev, self.session = parent, dev, None
        self.tex_size = (1, 1)
        self.pic = Gtk.Picture(content_fit=Gtk.ContentFit.CONTAIN, can_shrink=True, focusable=True)
        self.set_child(self.pic)
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", lambda _c, x, y: self._send({"k": "move", **self._norm(x, y)}))
        self.pic.add_controller(motion)
        click = Gtk.GestureClick(button=0)
        click.connect("pressed", lambda g, _n, x, y: self._button(g, True, x, y))
        click.connect("released", lambda g, _n, x, y: self._button(g, False, x, y))
        self.pic.add_controller(click)
        scroll = Gtk.EventControllerScroll(flags=Gtk.EventControllerScrollFlags.BOTH_AXES)
        scroll.connect("scroll", lambda _c, dx, dy: (self._send({"k": "scroll", "dx": round(dx), "dy": round(dy)}), True)[1])
        self.pic.add_controller(scroll)
        keys = Gtk.EventControllerKey()
        keys.connect("key-pressed", lambda _c, kv, code, _s: self._key(kv, code, True))
        keys.connect("key-released", lambda _c, kv, code, _s: self._key(kv, code, False))
        self.add_controller(keys)
        self.connect("close-request", lambda *_: (self.session and self.session.close(), False)[1])

    def start(self):
        self.present()
        self.set_title(f"Asking {self.dev['name']}…")
        bg(lambda: self.parent.core.take_control(self.dev, self._frame, self._ended),
           self._started, lambda e: (self.parent._error(e), self.destroy()))

    def _started(self, session):
        self.session = session
        self.set_title(f"Controlling {self.dev['name']}")
        self.pic.grab_focus()

    def _frame(self, jpeg):
        def show():
            try:
                tex = Gdk.Texture.new_from_bytes(GLib.Bytes.new(jpeg))
            except GLib.Error:
                return
            self.tex_size = (tex.get_width(), tex.get_height())
            self.pic.set_paintable(tex)
        GLib.idle_add(show)

    def _ended(self):
        GLib.idle_add(self.destroy)

    def _norm(self, x, y):
        """Widget coordinates -> 0..1 on the remote screen (accounts for letterboxing)."""
        ww, wh = self.pic.get_width(), self.pic.get_height()
        tw, th = self.tex_size
        s = min(ww / tw, wh / th) if tw and th else 1
        ox, oy = (ww - tw * s) / 2, (wh - th * s) / 2
        return {"x": max(0.0, min(1.0, (x - ox) / (tw * s))), "y": max(0.0, min(1.0, (y - oy) / (th * s)))}

    def _button(self, g, down, x, y):
        self.pic.grab_focus()
        self._send({"k": "button", "b": g.get_current_button(), "down": down, **self._norm(x, y)})

    def _key(self, keyval, code, down):
        ch = Gdk.keyval_to_unicode(keyval)
        self._send({"k": "key", "code": code - 8, "down": down, "char": chr(ch) if ch >= 32 else None,
                    "name": Gdk.keyval_name(keyval)})
        return True

    def _send(self, ev):
        if self.session:
            self.session.send(ev)


class LinkApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.drivewood.Link", flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.win = None

    def do_command_line(self, cmd):
        args = cmd.get_arguments()[1:]
        if self.win is None:
            self.hold()  # stay alive in the background when the window is closed
            self.win = LinkWindow(self)
        if "--background" not in args:
            self.win.open()
        return 0


def main():
    sys.exit(LinkApp().run(sys.argv))
