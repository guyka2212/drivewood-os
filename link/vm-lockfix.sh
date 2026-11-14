#!/bin/bash
T=~/.config/omarchy/themes/drivewood
curl -fsS -o "$T/shell.lock.toml" http://10.0.2.2:8000/files/driftwood/shell.lock.toml && echo "lock colours updated"
omarchy-theme-set Drivewood >/dev/null 2>&1; sleep 3; ~/.local/bin/driftwood-sky --force >/dev/null 2>&1; echo done
