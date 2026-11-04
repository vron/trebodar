#!/usr/bin/env bash
# De renderade bilderna (inne/ och ute/, ./rendera.sh) på webbplatsen: JPEG i fyra storlekar till releasen bilder på
# GitHub, varefter webbplatsen byggs om (`./mod publicera`, se README.md). Argumenten går vidare, t.ex. bara några
# bilder (./publicera.sh I05 I07) eller bara lokalt till docs/renderingar/bilder (./publicera.sh --lokalt).
set -euo pipefail
cd "$(dirname "$0")/../verktyg/modellering"
./mod publicera "$@"
