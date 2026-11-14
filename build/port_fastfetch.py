import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(HERE, "..", "files", "os", "fastfetch.jsonc"), encoding="utf-8"))
d["logo"]["source"] = "/usr/share/drivewood/about.txt"
for m in d["modules"]:
    if not isinstance(m, dict) or m.get("type") != "command":
        continue
    t = m["text"]
    if "omarchy-version" in t:
        m["text"] = '. /etc/os-release; echo "Drivewood $VERSION_ID"'
    elif "omarchy-theme-current" in t:
        m["text"] = t.replace("theme=$(omarchy-theme-current); ", "theme=Drivewood; ")
    elif "about.days" in t:
        m["text"] = 'days=$(( ($(date +%s) - $(stat -c %W /var/log)) / 86400 )); echo "$days days"'
    elif "durationDaysHours" in t:
        m["text"] = "uptime -p | sed 's/^up //'"
    elif "omarchy-version-pkgs" in t:
        m["text"] = r"awk '/\[ALPM\] (upgraded|installed)/{l=$1} END{print substr(l,2,10)}' /var/log/pacman.log"
    elif "uname -r" in t:
        m["text"] = 'echo "Linux $(uname -r) Drivewood"'
s = json.dumps(d, ensure_ascii=False, indent=2)
bad = [l for l in s.splitlines() if "omarchy" in l.lower()]
assert not bad, bad
out = os.path.join(HERE, "desktop", "config", "fastfetch", "config.jsonc")
open(out, "w", encoding="utf-8", newline="\n").write(s)
print("fastfetch ok")
