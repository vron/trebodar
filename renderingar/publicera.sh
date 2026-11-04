#!/usr/bin/env bash
# De renderade bilderna (inne/ och ute/, ./rendera.sh) på webbplatsen: JPEG i fyra storlekar till releasen bilder på
# GitHub, varefter webbplatsen byggs om (`./mod publicera`, se README.md). Argumenten går vidare, t.ex. bara några
# bilder (./publicera.sh I05 I07) eller bara lokalt till docs/renderingar/bilder (./publicera.sh --lokalt). Med
# --variant velfac först: variantens bilder (renderingar/velfac/) till dess startsida (docs/velfac/).
set -euo pipefail
cd "$(dirname "$0")/../verktyg/modellering"
if [[ "${1:-}" == --variant ]]; then
  v="$2"; shift 2
  exec ./mod --variant "$v" publicera "$@"
fi
./mod publicera "$@"
