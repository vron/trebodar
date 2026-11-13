# Bygget

`./bygg` (i repots rot, kör `bygg.py` med `uv`) bygger allt som genereras ur källorna, i beroendeordning, och hoppar över det som är aktuellt. Samma skript körs lokalt och i GitHub Actions ([`.github/workflows/bygg.yml`](../../.github/workflows/bygg.yml)).

```sh
./bygg                  # allt som är inaktuellt
./bygg K-05 R-05        # de stegen och det de bygger på
./bygg --lista          # stegen och om de är aktuella
./bygg --om K-01        # bygg om även när steget är aktuellt
./bygg --snabb          # bara de snabba stegen (GitHub Actions)
./bygg --markera U-03   # ange att stegets resultat är aktuella utan att köra det
./bygg --jobb 4         # högst fyra steg samtidigt (standard: hälften av kärnorna)
```

Stegen körs parallellt: ett steg startar när stegen det bygger på är klara (beroendena i `STEG`), så att hela bygget
tar ungefär så lång tid som den längsta kedjan (lokalt under en halv minut för de snabba stegen). När flera steg körs
har deras utdata stegets namn först på raden, och ett steg som misslyckas stoppar bygget när de pågående är klara.

Pythonmiljöerna (`beräkningar/.venv`, `verktyg/modellering/.venv`, `verktyg/modellanalys/.venv`) skapas och uppdateras med `uv` när de saknas, kravfilerna ändras eller `MILJO_VERSION` höjs, före stegen. Paketens bytekod kompileras då i förväg, så att Python inte kompilerar dem vid varje start där den inte får spara bytekoden (`PYTHONDONTWRITEBYTECODE`, som i Claude Code); stegen själva får spara den (`__pycache__` ignoreras av git). Modellanalysens steg körs genom `./ma` (ma-tjänsten, se [`verktyg/modellanalys`](../modellanalys/)), så att modellen läses en gång. Typsnittet Carlito ska vara installerat eller ligga i `beräkningar/.fonts`.

## Stegen

| Steg | Kör | Utdata |
|---|---|---|
| `modell` | `./mod bygg --format step` | `modeller/trebodar/ut/trebodar.step` och modellanalysens cache för den |
| `webb` | `./mod webb` | `docs/modell/` (webbvisaren) |
| `kameraplan` | `./mod kameraplan` | `renderingar/kameraplan.pdf`, `docs/renderingar/` (renderingarna på planerna) |
| `granskning` | `kontroll_laster.py` och `kontroll_balkplattor.py` (stoppar bygget om balkplåtarnas skärfiler inte följer K-01:s hålbilder) | `verktyg/modellanalys/granskning/ytterväggens_läge.png` |
| F-01, AV-01, K-01, K-02, K-03, U-02 | beräkningen och rapporten (se mappens README) | rapporten i `rapporter/` |
| TP-01 | `bygg.py` (läser också IN-01:s indata: specialprodukterna per fas) | tidsplanen i `rapporter/` |
| IN-01 | `./mod inkop utdrag` (modellens specialprodukter) och `bygg.py` (faserna ur TP-01) | inköpslistan i `rapporter/` |
| K-04 | `./mod barverk` (modellens bärverk) och `berakning.py` (balkmodellen, några sekunder) | rapporten i `rapporter/` |
| **K-05, K-06, U-01, U-03** (tunga) | beräkningen, valideringen och rapporten | resultaten, `räknat.json` och rapporten i `rapporter/` (incheckade) |
| **U-04** (tungt, manuellt) | `./mod ljusplan` (renderingen i Blender) | ljusplanerna, `räknat.json` och rapporten i `rapporter/` (incheckade) |
| R-01, R-03, R-04, R-05, R-06, AR-01, AR-02 | `ritningar.py` | ritningsserien i `ritningar/` |
| `R-02` | `./mod stomme ritning` (modellens bärverk, samma utdrag som K-04) | R-02 i `ritningar/` |
| `gjutning` | `./mod gjutning ritning` (installationernas data och modellens snitt) | AR-03 och AR-04 i `ritningar/` |
| E-01, E-02, VS-01, VS-02, VS-03, VV-01, VL-01 | `./mod <installation> ritning` (installationernas data och modellens snitt) | installationsritningen i `ritningar/` |

Efter stegen skriver `./bygg` (utan valda steg) webbplatsens startsida, `docs/index.html` ([`startsida.py`](startsida.py) med mallen [`startsida.html`](startsida.html)), och kopierar bygglovet, rapporterna, ritningarna och kameraplanen till `docs/handlingar/`, med alla handlingarna samlade för utskrift i en pdf med A4-sidorna och en med A3-sidorna i förteckningens ordning, med ett bokmärke per handling (`docs/handlingar/samlade/`, [`samlade.py`](samlade.py) med pymupdf via `uv run --with`). Startsidan byggs ur det som redan är byggt:

- projektets uppgifter och handlingsförteckningen (med status) ur registret i F-01:s `indata.toml`: alla handlingar, avsnitt för avsnitt efter seriernas avsnitt (`[[serie]]`: tekniskt samråd, installationsritningar, arbetsritningar, utredningar, inköp, illustrationer), och bygglovets beslut och handlingar ur `bygglov/handlingar.toml`;
- rapporternas revision och datum och ritningsbladens nummer, titel, skala, revision och datum (bladens JSON);
- bilderna ur renderingarnas förteckning (`docs/renderingar/bilder/renderingar.json`) med vyernas texter (`TEXTER` och `TEKNIK` i `modeller/trebodar/vyer.py`), i grupperna urval (`URVAL` i `startsida.py`), ute, inne och stomme och teknik;
- planerna ur `docs/renderingar/plan.json` (`./mod kameraplan`).

Beskrivningen av huset står i mallen. GitHub Pages publicerar hela `docs/`: startsidan på https://vron.github.io/trebodar/, modellen på https://vron.github.io/trebodar/modell/ och renderingarna på https://vron.github.io/trebodar/renderingar/ (`handlingar/` leder till förteckningen på startsidan). Renderingarnas bilder byggs inte här: de renderas lokalt och publiceras i releasen `bilder` (`renderingar/publicera.sh`, se [`renderingar/README.md`](../../renderingar/README.md)), och GitHub Actions hämtar dem till `docs/renderingar/bilder/` före `./bygg --snabb`, så att startsidan visar dem. Lokalt syns nya bilder på startsidan efter nästa `./bygg`.

Beroendena står i `STEG` i `bygg.py`. Läser ett steg en ny mapp eller ett nytt resultat: lägg till det i stegets `kallor` eller `bygger_pa`.

## Aktuellt

Ett steg är aktuellt när dess kontrollsumma är oförändrad sedan det byggdes och dess utdata finns. Summan räknas över alla filer i stegets mappar som git inte ignorerar (utom `.md` och stegets incheckade resultat), dess kommandon och summorna för stegen det bygger på, och är densamma på alla datorer. Snabba steg sparar summan i `.bygg/` (versionshanteras inte).

## Tunga steg

K-05 (cirka 2 min), K-06 (under en halv minut), U-01 (cirka 2 min) och U-03 (cirka 15 min) räknas lokalt: U-01 och U-03 räknar sina fall i parallella processer, och tillsammans tar stegen för lång tid för GitHub Actions (fyra kärnor). Rapporterna för K-05, K-06 och U-03 ritas ur stora mellanresultat (FE-fält, `*.npz`, `*.pkl`) som inte versionshanteras. Det som checkas in:

- `räknat.json`: kontrollsumman för källorna som resultaten räknades med;
- resultaten som andra steg läser (K-05 och K-06: `resultat.json`; K-05 också valideringarnas `konvergens.json` och `vaggande.json`);
- rapporten i `rapporter/`.

U-04, ljusplanerna, är ett manuellt tungt steg: det renderas i Blender ur hela modellen (med tillverkarnas
fotometrifiler i `lokalt/el/`, som inte versionshanteras), så det skulle bli inaktuellt vid varje ändring i modellen.
Det görs därför bara när det väljs, `./bygg U-04` (cirka en minut), inte i `./bygg` utan steg, och `./bygg --snabb`
stoppar inte när det är inaktuellt (`--lista` visar det); som renderingarna görs det om när belysningen har ändrats.
Checka då in rapporten och `räknat.json`.

`./bygg --snabb` (GitHub Actions) kör bara de snabba stegen och stoppar om ett tungt steg inte är aktuellt, alltså om dess källor (eller något det bygger på) har ändrats utan att det har räknats om. Kör då `./bygg <nr>` lokalt och checka in resultaten och `räknat.json` med ändringen. Påverkar ändringen inte resultaten (t.ex. en kommentar), räcker `./bygg --markera <nr>`.

## Det som versionshanteras

Genererade filer versionshanteras inte (`.gitignore` i roten och i beräkningarnas mappar). Undantagen:

| Fil | Varför |
|---|---|
| De tunga stegens rapporter och resultat (ovan) | Tar för lång tid att räkna i GitHub Actions |
| `ritningar/200 Situationsplan.pdf`, `ritningar/201 Planritning.pdf` | Bygglovsritningar utan källa här |
| `bygglov/` | Bygglovet från kommunen: beslutet och handlingarna som tillhör det |
| `modeller/balkar/*.step`, `modeller/balkplattor/*.step`, `*.dxf` | Tillverkningsfilerna för K-01 rev D (text, ändras sällan); genereras med cadquery, som inte finns i miljöerna |
| `beräkningar/K-01/halbild_*.csv` | Hålbilderna för laserskärningen (text), läses av balkplåtarna |
| `beräkningar/U-03/klimat_era5.csv.gz` | Klimatdata, underlag |
