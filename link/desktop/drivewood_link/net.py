"""Wire protocol, device identity (TLS certificate) and LAN discovery.

Protocol (same on Android): every message is a 4-byte big-endian length, a UTF-8 JSON
header, and, when the header has "size" > 0, exactly that many raw bytes after it.
"""
import datetime
import hashlib
import json
import socket
import ssl
import struct
import threading
import time

from . import config

MAX_HEADER = 1 << 20


# --- framing -------------------------------------------------------------
def recv_exact(sock, n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(n - len(buf), 1 << 20))
        if not chunk:
            raise ConnectionError("connection closed")
        buf += chunk
    return bytes(buf)


def send_msg(sock, header, payload=b""):
    if payload:
        header = dict(header, size=len(payload))
    raw = json.dumps(header).encode()
    sock.sendall(struct.pack(">I", len(raw)) + raw + payload)


def recv_header(sock):
    (n,) = struct.unpack(">I", recv_exact(sock, 4))
    if n > MAX_HEADER:
        raise ConnectionError("header too large")
    return json.loads(recv_exact(sock, n))


def recv_msg(sock, max_payload=64 << 20):
    """Header plus payload held in memory (for small payloads such as screen frames)."""
    h = recv_header(sock)
    size = int(h.get("size", 0))
    if size > max_payload:
        raise ConnectionError("payload too large")
    return h, (recv_exact(sock, size) if size else b"")


# --- identity ------------------------------------------------------------
class Identity:
    """A self-signed certificate per device. Its SHA-256 is published in Supabase so
    other devices of the same account can check they reached the real device."""

    def __init__(self):
        d = config.config_dir()
        self.cert, self.key = d / "cert.pem", d / "key.pem"
        if not (self.cert.exists() and self.key.exists()):
            self._generate()
        der = ssl.PEM_cert_to_DER_cert(self.cert.read_text())
        self.fingerprint = hashlib.sha256(der).hexdigest()

    def _generate(self):
        import shutil
        import subprocess
        if shutil.which("openssl"):
            subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:prime256v1",
                            "-nodes", "-keyout", str(self.key), "-out", str(self.cert), "-days", "3650",
                            "-subj", "/CN=DriveWood Link device"], check=True, capture_output=True)
            try:
                self.key.chmod(0o600)
            except OSError:
                pass
            return
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.x509.oid import NameOID

        key = ec.generate_private_key(ec.SECP256R1())
        name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "DriveWood Link device")])
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
                .public_key(key.public_key()).serial_number(x509.random_serial_number())
                .not_valid_before(now - datetime.timedelta(days=1))
                .not_valid_after(now + datetime.timedelta(days=3650))
                .sign(key, hashes.SHA256()))
        self.key.write_bytes(key.private_bytes(serialization.Encoding.PEM,
                                               serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
        self.cert.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        try:
            self.key.chmod(0o600)
        except OSError:
            pass

    def server_context(self):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(self.cert, self.key)
        return ctx


def client_connect(addr, port, expected_fingerprint, timeout=8):
    """TLS connection that only succeeds if the server's certificate matches the
    fingerprint the device registered in Supabase (certificate pinning)."""
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # replaced by the pin check below
    raw = socket.create_connection((addr, port), timeout=timeout)
    s = ctx.wrap_socket(raw)
    der = s.getpeercert(binary_form=True)
    if not expected_fingerprint or hashlib.sha256(der).hexdigest() != expected_fingerprint:
        s.close()
        raise ConnectionError("device identity check failed")
    s.settimeout(None)
    return s


# --- discovery -----------------------------------------------------------
def local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class Discovery:
    """Announces this device on the LAN every few seconds and remembers who else is there.
    Announcements only carry a random device id; who owns it is checked against Supabase."""

    def __init__(self, device_id, on_change=None):
        self.device_id = device_id
        self.on_change = on_change
        self.seen = {}  # device id -> (address, port, time)
        self.stop = threading.Event()

    def start(self):
        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._announce, daemon=True).start()

    def _announce(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps({"app": config.APP_ID, "v": config.PROTOCOL,
                          "device": self.device_id, "port": config.TCP_PORT}).encode()
        while not self.stop.is_set():
            for target in ("255.255.255.255", "127.0.0.1"):
                try:
                    s.sendto(msg, (target, config.UDP_PORT))
                except OSError:
                    pass
            self.stop.wait(3)

    def _listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        s.bind(("", config.UDP_PORT))
        while not self.stop.is_set():
            try:
                data, (addr, _) = s.recvfrom(2048)
                m = json.loads(data)
            except (OSError, ValueError):
                continue
            if m.get("app") != config.APP_ID or m.get("device") == self.device_id:
                continue
            dev, port = str(m.get("device")), int(m.get("port", config.TCP_PORT))
            new = dev not in self.seen or self.seen[dev][:2] != (addr, port)
            self.seen[dev] = (addr, port, time.time())
            if new and self.on_change:
                self.on_change()

    def online(self, device_id):
        e = self.seen.get(device_id)
        return bool(e and time.time() - e[2] < 12)

    def address(self, device_id):
        e = self.seen.get(device_id)
        return (e[0], e[1]) if e else None
