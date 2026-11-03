# Köldbärarledningarna

Skyddsrören för bergvärmepumpens kollektorslangar som data i modellen: två rör Ø110 från energibrunnen i trädgården in
under källaren och upp genom bottenplattan i teknikrummet. Kollektorslangarna dras in i rören efteråt och går vidare
till värmepumpens anslutningar för köldbärare (`../teknikrum.py`, TK-VP KB-in och KB-ut), så rören har bara böjar om
högst 15°.

```
cd verktyg/modellering
./mod kollektor kontroll     # böjarna, rören i varandra, genomföringarna och krockarna mot husets delar och de andra
                             # installationerna
./mod golvvarme ritning      # ritningen VG-01.3 (köldbärarledningarna, i golvvärmens serie)
```

## Filerna

| Fil | Innehåll |
|---|---|
| [`ledningar.py`](ledningar.py) | Rörens väg (`ledningar`), måtten och lägena, böjarnas vinklar, kontrollen, genomföringarna och utdraget för ritningen |
| [`kollektor.py`](kollektor.py) | Geometrin under `Hus/Installationer/Köldbärare`: rören svepta längs vägen med böjar |

## Dragningen

- Rören kommer lodrätt upp genom bottenplattan i teknikrummet vid användarens markering (`UPP`), c/c 140, mellan
  armeringsnätets järn (`../strak.mellan_jarnen`), och slutar 100 mm över golvet.
- Under plattan svänger de till vågrätt med sex böjar om 15° (`S_BOJ` mellan böjarna) och går söderut under plattans
  cellplast och makadam och under avloppet (`Z_VAG`), under kantbalken vid V7 och ut i trädgården, under dräneringen
  runt grunden (`../dranering`), där de förskjuts i sidled med två böjar om 15° mot energibrunnen (`BRUNN`,
  ungefärligt läge), frostfritt.
- Golvvärmen i bottenplattan håller sig fri från rören (`../golvvarme/system.py`).

Rörens läge ändras med `UPP`, `BRUNN`, `Z_VAG` och `Y_SIDA` i `ledningar.py`.

## Kontrollen

`./mod kollektor kontroll`: böjar över 15°, rören i varandra, genomföringarna ur husets geometri och krockarna ur
modellens geometri mot husets delar och de andra installationerna (fel).
