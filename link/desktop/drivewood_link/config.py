"""Settings and small helpers for files under ~/.config/drivewood-link."""
import json
import os
import pathlib

SUPABASE_URL = "https://vknultzvokyblinqsxxs.supabase.co"
# Publishable key: safe to ship in the app, all data is protected by row-level security.
SUPABASE_KEY = "sb_publishable_VOv_rXsKlq2eGob72IKvaQ_QhajzIjQ"

TERMS_VERSION = "1.0"
PRIVACY_VERSION = "1.0"

# Ports can be moved for testing two copies on one machine.
TCP_PORT = int(os.environ.get("DWLINK_PORT", "47800"))
UDP_PORT = int(os.environ.get("DWLINK_UDP_PORT", "47801"))
APP_ID = "dwlink"
PROTOCOL = 1


def home() -> pathlib.Path:
    return pathlib.Path(os.environ.get("DWLINK_HOME") or pathlib.Path.home())


def config_dir() -> pathlib.Path:
    if os.environ.get("DWLINK_HOME"):
        d = home() / "config"
    else:
        d = pathlib.Path(os.environ.get("XDG_CONFIG_HOME") or home() / ".config") / "drivewood-link"
    d.mkdir(parents=True, exist_ok=True)
    return d


def downloads_dir() -> pathlib.Path:
    d = home() / "Downloads" / "DriveWood Link"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(name: str, default=None):
    p = config_dir() / name
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save(name: str, data) -> None:
    p = config_dir() / name
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, p)


def forget(name: str) -> None:
    try:
        (config_dir() / name).unlink()
    except FileNotFoundError:
        pass
