#!/bin/bash
# Menu entry for Android Studio installed in ~/.local/opt (studio.sh does this too since the fix)
mkdir -p ~/.local/share/applications
S=~/.local/opt/android-studio/bin
cat > ~/.local/share/applications/android-studio.desktop <<DESK
[Desktop Entry]
Type=Application
Name=Android Studio
GenericName=Android IDE
Comment=The official IDE for Android development
Exec=env _JAVA_AWT_WM_NONREPARENTING=1 $S/studio %f
Icon=$S/studio.svg
Categories=Development;IDE;
StartupWMClass=jetbrains-studio
Terminal=false
DESK
update-desktop-database ~/.local/share/applications 2>/dev/null
echo "Android Studio menu entry added"
