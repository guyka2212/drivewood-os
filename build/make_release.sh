#!/bin/bash
# Build the files for a GitHub release (the update that installed systems download).
#   bash build/make_release.sh            -> dist/drivewood-update-<VERSION>.tar.gz + .sha256
# Publishing is a separate step, ONLY after the release notes are written by the owner:
#   gh release create v<VERSION> dist/drivewood-update-<VERSION>.tar.gz* --title "Drivewood <VERSION>" --notes-file RELEASE_NOTES.md
set -e
cd "$(dirname "$0")"
V=$(cat VERSION)
bash make_stage.sh
rm -rf ../dist/tmp; mkdir -p ../dist/tmp
cp stage.tar.gz packages.txt ../dist/tmp/
cp ../link/drivewood-link-desktop.tar.gz ../dist/tmp/link.tar.gz
tar czf ../dist/drivewood-update-$V.tar.gz -C ../dist/tmp .
rm -rf ../dist/tmp
( cd ../dist && sha256sum drivewood-update-$V.tar.gz > drivewood-update-$V.tar.gz.sha256 && ls -la drivewood-update-$V.tar.gz* )
