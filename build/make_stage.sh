#!/bin/bash
# Assemble build/stage (same layout as the installed system) and pack build/stage.tar.gz.
set -e
cd "$(dirname "$0")"; R=..; S=stage
rm -rf $S; mkdir -p $S/usr/bin $S/usr/lib/systemd/user $S/usr/share/drivewood/{shell,backgrounds,apps/tidepool} $S/usr/share/plymouth/themes/drivewood $S/etc/skel/.config
cp desktop/bin/drivewood-* $S/usr/bin/; mv $S/usr/bin/*.service $S/usr/bin/*.timer $S/usr/lib/systemd/user/
cp desktop/shell/*.qml $S/usr/share/drivewood/shell/
cp $R/files/driftwood/backgrounds/*.png $S/usr/share/drivewood/backgrounds/
cp desktop/logo.png $S/usr/share/drivewood/logo.png
cp $R/files/about.txt $S/usr/share/drivewood/about.txt
cp desktop/share-hidden-apps $S/usr/share/drivewood/hidden-apps
cp $R/apps/driftwood/driftwood.py $S/usr/share/drivewood/apps/landscape.py
cp $R/apps/tidepool/index.html $S/usr/share/drivewood/apps/tidepool/index.html
P=$S/usr/share/plymouth/themes/drivewood
cp $R/files/plymouth/driftwood-boot/*.png $P/
sed 's/driftwood/drivewood/g; s/Driftwood/Drivewood/g' $R/files/plymouth/driftwood-boot/driftwood.script > $P/drivewood.script
sed 's#/usr/share/plymouth/themes/driftwood#/usr/share/plymouth/themes/drivewood#g; s/driftwood.script/drivewood.script/' $R/files/plymouth/driftwood-boot/driftwood.plymouth > $P/drivewood.plymouth
cp -r desktop/config/. $S/etc/skel/.config/
mkdir -p $S/usr/lib; cp desktop/os-release $S/usr/lib/os-release
cp desktop/bashrc-drivewood $S/usr/share/drivewood/bashrc
mkdir -p $S/usr/share/drivewood/settings $S/usr/share/applications
cp desktop/settings/drivewood_settings.py $S/usr/share/drivewood/settings/
cp desktop/applications/*.desktop $S/usr/share/applications/
cp VERSION $S/usr/share/drivewood/version
tar czf stage.tar.gz -C $S .
echo "stage: $(find $S -type f | wc -l) files, $(du -sh stage.tar.gz | cut -f1)"
grep -rIl -i "omarchy\|driftwood" $S --include='*.qml' --include='*.lua' --include='*.conf' --include='*.jsonc' --include='*.script' --include='*.plymouth' --include='drivewood-*' 2>/dev/null | sed 's/^/leftover name in: /' || true
