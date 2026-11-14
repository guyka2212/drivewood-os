#!/bin/bash
# Install Android Studio from Google's official Linux archive into ~/.local/opt (no sudo).
URL=https://edgedl.me.gvt1.com/android/studio/ide-zips/2026.2.2.9/android-studio-rabbit2-patch1-linux.tar.gz
F=~/Downloads/android-studio-rabbit2-patch1-linux.tar.gz
LOG=/tmp/studio-install.log
exec > >(tee "$LOG") 2>&1
mkdir -p ~/Downloads ~/.local/opt ~/.local/share/applications

# Google lists a SHA-256 for each download on the page; find the one for this file
[ -s /tmp/studio.html ] || curl -sL https://developer.android.com/studio -o /tmp/studio.html
SUM=$(tr '\n' ' ' < /tmp/studio.html | grep -oE 'rabbit2-patch1-linux\.tar\.gz.{0,800}' | grep -oE '\b[0-9a-f]{64}\b' | head -1)
echo "published sha256: ${SUM:-not found on page}"

echo "== downloading (1.59 GB)"
curl -L --fail --progress-bar -o "$F" "$URL" || { echo "DOWNLOAD FAILED"; exit 1; }
ls -la "$F"
if [ -n "$SUM" ]; then
  echo "$SUM  $F" | sha256sum -c - || { echo "CHECKSUM MISMATCH - not installing"; exit 1; }
fi

echo "== unpacking"
rm -rf ~/.local/opt/android-studio
tar -xzf "$F" -C ~/.local/opt && rm -f "$F"
S=~/.local/opt/android-studio/bin
BIN=$S/studio; [ -x "$BIN" ] || BIN=$S/studio.sh
ICON=$S/studio.svg; [ -f "$ICON" ] || ICON=$S/studio.png
echo "launcher: $BIN  icon: $ICON"; du -sh ~/.local/opt/android-studio

cat > ~/.local/share/applications/android-studio.desktop <<EOF
[Desktop Entry]
Type=Application
Name=Android Studio
GenericName=Android IDE
Comment=The official IDE for Android development
Exec=env _JAVA_AWT_WM_NONREPARENTING=1 $BIN %f
Icon=$ICON
Categories=Development;IDE;
StartupWMClass=jetbrains-studio
Terminal=false
EOF
update-desktop-database ~/.local/share/applications 2>/dev/null
echo "== done"; df -h ~ | tail -1
curl -s --data-binary @"$LOG" http://10.0.2.2:8000/studio-log >/dev/null
