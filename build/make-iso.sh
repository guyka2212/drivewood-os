#!/bin/bash
# Build drivewood-installer.iso on a Drivewood/Arch machine (asks for the password once), then upload it.
set -e
SRC=http://10.0.2.2:8000; W=/var/tmp/dwiso
sudo bash -e -c "
pacman -S --needed --noconfirm archiso >/dev/null
rm -rf $W; mkdir -p $W/files
cp -r /usr/share/archiso/configs/releng $W/profile
"
cd $W
sudo curl -fsS -o files/project.tar.gz $SRC/build/iso-payload.tar.gz
sudo bash -e -c "
P=$W/profile
sed -i 's/^iso_name=.*/iso_name=\"drivewood-installer\"/; s/^iso_label=.*/iso_label=\"DRIVEWOOD\"/; s/^iso_publisher=.*/iso_publisher=\"Drivewood <https:\/\/github.com\/guyka2212\/drivewood-os>\"/; s/^iso_application=.*/iso_application=\"Drivewood installer\"/; s/^iso_version=.*/iso_version=\"1.0.0\"/' \$P/profiledef.sh
grep -rl 'Arch Linux install medium' \$P | xargs -r sed -i 's/Arch Linux install medium/Drivewood installer/g'
mkdir -p \$P/airootfs/root/drivewood \$P/airootfs/usr/local/bin
tar xzf $W/files/project.tar.gz -C \$P/airootfs/root/drivewood
install -m 755 \$P/airootfs/root/drivewood/build/drivewood-install \$P/airootfs/usr/local/bin/drivewood-install
printf '\n\033[38;2;143;180;230m  Drivewood installer\033[0m  type  \033[1mdrivewood-install\033[0m  to begin.\n\n' > \$P/airootfs/etc/motd
grep -q drivewood-install \$P/profiledef.sh || sed -i 's|^file_permissions=(|file_permissions=(\n  [\"/usr/local/bin/drivewood-install\"]=\"0:0:755\"|' \$P/profiledef.sh
mkarchiso -v -w $W/work -o $W/out \$P 2>&1 | tail -5
rm -rf $W/work
"
ISO=$(ls $W/out/*.iso | head -1); ls -la "$ISO"; sha256sum "$ISO" | sudo tee "$ISO.sha256"
echo "== uploading to the project folder"
curl -fsS -T "$ISO" http://10.0.2.2:8001/drivewood-installer.iso && curl -fsS -T "$ISO.sha256" http://10.0.2.2:8001/drivewood-installer.iso.sha256 && echo "uploaded"
