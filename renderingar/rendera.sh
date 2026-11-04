#!/usr/bin/env bash
# Inomhusbilderna I01–I30 i 2K (2 048 × 1 152) och slutlig kvalitet till renderingar/inne/ och kameraplanen; med
# --ute i stället de andra vyerna (ute och detalj, trebodar.vyer.VYER) till renderingar/ute/. Med --ljusserie B (C, D,
# trebodar.vyer.LJUSSERIER) i seriens ljus till renderingar/B/inne/ och renderingar/B/ute/; utan den i varje vys
# eget ljus (serien A). Bilderna versionshanteras inte; ./publicera.sh lägger ut dem på webbplatsen. Argumenten går
# vidare till `./mod rendera`, t.ex. bara några bilder (./rendera.sh I05 I07), en annan kvalitet
# (./rendera.sh --kvalitet normal) eller ett annat dagsljus (./rendera.sh --ljus 12 21 13:00 mulet).
set -euo pipefail
har="$(cd "$(dirname "$0")" && pwd)"
serie=inne
ljusserie=A
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ute) serie=ute; shift ;;
    --ljusserie) ljusserie="$2"; shift 2 ;;
    *) break ;;
  esac
done
ut="$har/$serie"
[[ "$ljusserie" != A ]] && ut="$har/$ljusserie/$serie"
cd "$har/../verktyg/modellering"
./mod kameraplan --ut "$har/kameraplan.pdf" || echo "kameraplanen ritades inte (kräver STEP-filen: ./mod bygg)"
./mod rendera --serie "$serie" --kvalitet slutlig --ljusserie "$ljusserie" --ut "$ut" "$@"
