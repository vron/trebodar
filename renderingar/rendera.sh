#!/usr/bin/env bash
# Inomhusbilderna I01–I30 i 4K (3 840 × 2 160) och slutlig kvalitet till renderingar/inne/ (versionshanteras inte)
# och kameraplanen. Argumenten går vidare till `./mod rendera`, t.ex. bara några bilder (./rendera.sh I05 I07),
# en annan kvalitet (./rendera.sh --kvalitet normal) eller ett annat dagsljus (./rendera.sh --ljus 12 21 13:00 mulet).
set -euo pipefail
har="$(cd "$(dirname "$0")" && pwd)"
cd "$har/../verktyg/modellering"
./mod kameraplan --ut "$har/kameraplan.png" || echo "kameraplanen ritades inte (kräver STEP-filen: ./mod bygg)"
./mod rendera --serie inne --kvalitet slutlig --ut "$har/inne" "$@"
