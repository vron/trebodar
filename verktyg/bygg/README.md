# Bygget

`./bygg` (i repots rot, kör `bygg.py` med `uv`) bygger allt som genereras ur källorna, i beroendeordning, och hoppar över det som är aktuellt. Samma skript körs lokalt och i GitHub Actions ([`.github/workflows/bygg.yml`](../../.github/workflows/bygg.yml)).

```sh
./bygg                  # allt som är inaktuellt
./bygg K-05 R-05        # de stegen och det de bygger på
./bygg --lista          # stegen och om de är aktuella
./bygg --om K-01        # bygg om även när steget är aktuellt
./bygg --snabb          # bara de snabba stegen (GitHub Actions)
./bygg --markera U-03   # ange att stegets resultat är aktuella utan att köra det
```

Pythonmiljöerna (`beräkningar/.venv`, `verktyg/modellering/.venv`, `verktyg/modellanalys/.venv`) skapas och uppdateras med `uv` när de saknas eller kravfilerna ändras. Typsnittet Carlito ska vara installerat eller ligga i `beräkningar/.fonts`.

## Stegen

| Steg | Kör | Utdata |
|---|---|---|
| `modell` | `./mod bygg --format step` | `modeller/trebodar/ut/trebodar.step` |
| `webb` | `./mod webb` | `docs/` (webbvisaren) |
| `kameraplan` | `./mod kameraplan` | `renderingar/kameraplan.pdf` |
| `granskning` | `kontroll_laster.py` | `verktyg/modellanalys/granskning/ytterväggens_läge.png` |
| F-01, AV-01, K-01, K-02, K-03, U-02 | beräkningen och rapporten (se mappens README) | rapporten i `rapporter/` |
| **K-05, K-06, U-01, U-03** (tunga) | beräkningen, valideringen och rapporten | resultaten, `räknat.json` och rapporten i `rapporter/` (incheckade) |
| R-01, R-03, R-04, R-05, R-06, AR-01, AR-02 | `ritningar.py` | ritningsserien i `ritningar/` |

Efter stegen skriver `./bygg` (utan valda steg) `docs/handlingar/`: en sida med länkar till rapporterna, ritningarna och kameraplanen, med kopior bredvid. GitHub Pages publicerar hela `docs/`: modellen på https://vron.github.io/trebodar/ och handlingarna på https://vron.github.io/trebodar/handlingar/.

Beroendena står i `STEG` i `bygg.py`. Läser ett steg en ny mapp eller ett nytt resultat: lägg till det i stegets `kallor` eller `bygger_pa`.

## Aktuellt

Ett steg är aktuellt när dess kontrollsumma är oförändrad sedan det byggdes och dess utdata finns. Summan räknas över alla filer i stegets mappar som git inte ignorerar (utom `.md` och stegets incheckade resultat), dess kommandon och summorna för stegen det bygger på, och är densamma på alla datorer. Snabba steg sparar summan i `.bygg/` (versionshanteras inte).

## Tunga steg

K-05 (cirka 20 min), K-06, U-01 (många tidsstegade fall) och U-03 (cirka 1,5 h med 12 processer) tar för lång tid för GitHub Actions, och rapporterna för K-05, K-06 och U-03 ritas ur stora mellanresultat (FE-fält, `*.npz`, `*.pkl`) som inte versionshanteras. De räknas lokalt. Det som checkas in:

- `räknat.json`: kontrollsumman för källorna som resultaten räknades med;
- resultaten som andra steg läser (K-05 och K-06: `resultat.json`; K-05 också valideringarnas `konvergens.json` och `vaggande.json`);
- rapporten i `rapporter/`.

`./bygg --snabb` (GitHub Actions) kör bara de snabba stegen och stoppar om ett tungt steg inte är aktuellt, alltså om dess källor (eller något det bygger på) har ändrats utan att det har räknats om. Kör då `./bygg <nr>` lokalt och checka in resultaten och `räknat.json` med ändringen. Påverkar ändringen inte resultaten (t.ex. en kommentar), räcker `./bygg --markera <nr>`.

## Det som versionshanteras

Genererade filer versionshanteras inte (`.gitignore` i roten och i beräkningarnas mappar). Undantagen:

| Fil | Varför |
|---|---|
| De tunga stegens rapporter och resultat (ovan) | Tar för lång tid att räkna i GitHub Actions |
| `ritningar/200 Situationsplan.pdf`, `ritningar/201 Planritning.pdf` | Bygglovsritningar utan källa här |
| `modeller/referens/` (STEP och `*.bbrep`) | Onshape-modellen, fryst underlag |
| `modeller/balkar/*.step`, `modeller/balkplattor/*.step`, `*.dxf` | Tillverkningsfilerna för K-01 rev C (text, ändras sällan); genereras med cadquery, som inte finns i miljöerna |
| `beräkningar/K-01/halbild_*.csv` | Hålbilderna för laserskärningen (text), läses av balkplåtarna |
| `beräkningar/U-03/klimat_era5.csv.gz` | Klimatdata, underlag |
