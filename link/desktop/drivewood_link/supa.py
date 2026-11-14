"""Minimal Supabase client (Auth + REST) using only the standard library."""
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config


class SupaError(Exception):
    pass


def _request(method, url, body=None, headers=None, timeout=15):
    data = None if body is None else json.dumps(body).encode()
    h = {"apikey": config.SUPABASE_KEY, "Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            d = json.loads(raw)
            msg = d.get("msg") or d.get("message") or d.get("error_description") or d.get("error") or str(d)
        except ValueError:
            msg = raw.decode(errors="replace")[:200] or e.reason
        err = SupaError(msg)
        err.status = e.code
        raise err from None
    except urllib.error.URLError as e:
        raise SupaError(f"No connection to the account server ({e.reason})") from None


class Supa:
    """Holds the signed-in session and refreshes it when needed."""

    def __init__(self):
        self.session = config.load("session.json")
        self.lock = threading.Lock()

    # --- account -------------------------------------------------------
    @property
    def user_id(self):
        return (self.session or {}).get("user", {}).get("id")

    @property
    def signed_in(self):
        return bool(self.session and self.session.get("refresh_token"))

    def _store(self, s):
        s["expires_at"] = int(time.time()) + int(s.get("expires_in", 3600)) - 60
        self.session = s
        config.save("session.json", s)

    def sign_up(self, email, password, username, age_confirmed, accepted_legal):
        """Returns True when signed in right away, False when the email must be confirmed first."""
        d = _request("POST", f"{config.SUPABASE_URL}/auth/v1/signup", {
            "email": email, "password": password,
            "data": {
                "username": username.lower(),
                "age_confirmed": "true" if age_confirmed else "false",
                "accepted_legal": "true" if accepted_legal else "false",
                "terms_version": config.TERMS_VERSION,
                "privacy_version": config.PRIVACY_VERSION,
            }})
        if d and d.get("access_token"):
            self._store(d)
            return True
        return False

    def sign_in(self, email, password):
        d = _request("POST", f"{config.SUPABASE_URL}/auth/v1/token?grant_type=password",
                     {"email": email, "password": password})
        self._store(d)

    def sign_out(self):
        if self.session:
            try:
                _request("POST", f"{config.SUPABASE_URL}/auth/v1/logout", {},
                         {"Authorization": f"Bearer {self.session['access_token']}"})
            except SupaError:
                pass
        self.session = None
        config.forget("session.json")

    def token(self):
        with self.lock:
            if not self.session:
                raise SupaError("Not signed in")
            if time.time() >= self.session.get("expires_at", 0):
                d = _request("POST", f"{config.SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
                             {"refresh_token": self.session["refresh_token"]})
                self._store(d)
            return self.session["access_token"]

    # --- data ------------------------------------------------------------
    def rest(self, method, path, body=None, prefer=None):
        h = {"Authorization": f"Bearer {self.token()}"}
        if prefer:
            h["Prefer"] = prefer
        return _request(method, f"{config.SUPABASE_URL}/rest/v1/{path}", body, h)

    def rpc(self, name, args=None):
        return self.rest("POST", f"rpc/{name}", args or {})

    @staticmethod
    def verify_token(token):
        """Ask Supabase who owns an access token (used to check devices that connect to us)."""
        d = _request("GET", f"{config.SUPABASE_URL}/auth/v1/user", None, {"Authorization": f"Bearer {token}"})
        return d.get("id")
