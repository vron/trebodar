#!/usr/bin/env bash
# Inomhusbilderna I01–I30 i 2K (2 048 × 1 152) och slutlig kvalitet till renderingar/inne/ och kameraplanen; med
# --ute i stället de andra vyerna (ute och detalj, trebodar.vyer.VYER) till renderingar/ute/. Bilderna
# versionshanteras inte; ./publicera.sh lägger ut dem på webbplatsen. Argumenten går vidare till `./mod rendera`,
# t.ex. bara några bilder (./rendera.sh I05 I07), en annan kvalitet (./rendera.sh --kvalitet normal) eller ett annat
# dagsljus (./rendera.sh --ljus 12 21 13:00 mulet).
set -euo pipefail
har="$(cd "$(dirname "$0")" && pwd)"
serie=inne
if [[ "${1:-}" == "--ute" ]]; then serie=ute; shift; fi
cd "$har/../verktyg/modellering"
./mod kameraplan --ut "$har/kameraplan.pdf" || echo "kameraplanen ritades inte (kräver STEP-filen: ./mod bygg)"
./mod rendera --serie "$serie" --kvalitet slutlig --ut "$har/$serie" "$@"
