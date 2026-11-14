"""Serve files from a directory to the VM (GET) and save anything the VM POSTs to inbox/."""
import http.server, os, sys, time
ROOT = os.path.abspath(sys.argv[1])
INBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inbox")
os.makedirs(INBOX, exist_ok=True)

class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        name = os.path.basename(self.path.strip("/")) or "post"
        with open(os.path.join(INBOX, name + ".txt"), "wb") as f:
            f.write(data)
        self.send_response(200); self.end_headers(); self.wfile.write(b"ok\n")

http.server.ThreadingHTTPServer(("127.0.0.1", 8000), H).serve_forever()
