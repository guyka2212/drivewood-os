#!/bin/bash
# Pack what the ISO needs: installers, stage, Link sources, banner.
cd "$(dirname "$0")"; bash make_stage.sh >/dev/null
rm -rf /tmp/dwpay; mkdir -p /tmp/dwpay/build /tmp/dwpay/link
cp install-base.sh install-desktop.sh drivewood-install stage.tar.gz packages.txt VERSION /tmp/dwpay/build/
cp ../link/drivewood-link-desktop.tar.gz /tmp/dwpay/link/
cp ../files/screensaver.txt /tmp/dwpay/banner.txt
tar czf iso-payload.tar.gz -C /tmp/dwpay . && ls -la iso-payload.tar.gz
