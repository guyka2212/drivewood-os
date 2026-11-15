#!/bin/bash
# Test an update on an installed Drivewood VM before the release is published.
#   curl -s 10.0.2.2:8000/build/test-update.sh | bash -s on     # arrow appears, update comes from dist/ on the host
#   curl -s 10.0.2.2:8000/build/test-update.sh | bash -s off    # back to normal (GitHub)
# "on" blocks api.github.com in /etc/hosts so the checker can't replace the test update with the
# real latest release; downloads from github.com itself (Zen) still work.
set -e
SRC=http://10.0.2.2:8000; S="$HOME/.local/state/drivewood"; mkdir -p "$S"
V=$(curl -fsS $SRC/build/VERSION | tr -d '[:space:]')
if [ "$1" = off ]; then
  sudo sed -i '/# drivewood-update-test/d' /etc/hosts
  drivewood-update-check </dev/null || true
  echo "test mode off"; exit 0
fi
grep -q drivewood-update-test /etc/hosts || echo "0.0.0.0 api.github.com # drivewood-update-test" | sudo tee -a /etc/hosts >/dev/null
curl -fsS $SRC/RELEASE_NOTES.md -o /tmp/dw-notes.md
CUR=$(cat /usr/share/drivewood/version) V="$V" SRC="$SRC" python3 - "$S/update.json" <<'PY'
import json, os, sys
v, src = os.environ["V"], os.environ["SRC"]
json.dump({"available": True, "current": os.environ["CUR"], "version": v,
           "notes": open("/tmp/dw-notes.md").read(),
           "url": f"{src}/dist/drivewood-update-{v}.tar.gz",
           "sha256_url": f"{src}/dist/drivewood-update-{v}.tar.gz.sha256"},
          open(sys.argv[1], "w"), indent=2)
PY
echo "test mode on: update $V offered (from the host). Click the arrow in the bar."
