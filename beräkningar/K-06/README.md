# K-06 rev A – Bottenplatta och källarväggar

Källarens väggar av Sundolitt Kub 350-150 (cellplast 100 + betongkärna 150 + cellplast 100, SINTEF TG 2216) mot jord, byggskedet innan mellanbjälklaget har gjutits (ordningsföljd, V3/V20 med fri överkant, betongens hållfasthet och härdningstid vid återfyllning) och bottenplattan, 100 mm betong på 300 mm cellplast med kantbalkar i L-element L400 (300 mm höga med plattan), balkar under innerväggarna och plintar under rören. Bottenplattan, väggarnas kärna, rören och mellanbjälklaget (K-05) räknas i en gemensam FE-modell.

| Fil | Innehåll |
|---|---|
| `indata.py` | Mått, jord, fyllning per vägg, packningstryck (Ingold), Kub och armering, cellplast, L-element med fot av S300 |
| `innervaggar.py` | Innerväggarna gjutna i ett med bjälklaget: K-05:s modell med vridfjädrar längs innerväggarna, toppmoment och normalkraft, plattans moment och rörlasterna med och utan inspänning; skriver `innervaggar.json` |
| `vaggar.py` | Väggarna: lodrät strimla med jord- och packningstryck och toppmoment, fasaden med öppningar, vertikal last, fogar, LD4_2, byggskedet (brottlinjeteori för V3/V20), hållfasthet och mognadsålder |
| `modell06.py` | Den samverkande FE-modellen: K-05:s mellanbjälklag, bottenplattan, väggarnas kärna och rören som fjädrar, laster, kärnans krympning |
| `snitt06.py` | Balkmoment och tvärkraft längs balkarna, cellplastens kraft innanför stansningssnitten, väggarnas last per meter |
| `berakning06.py` | Lastfall och omhyllande för utförandet (`indata.UTFORANDEN`, L400), kort och lång styvhet; plintarnas storlek; skriver `res06_L400_<styvhet>.pkl` |
| `kontroll06.py` | Kontroller: cellplast, platta, balkar, plintar, mellanbjälklaget mot K-05:s armering, rörlaster, sättningar, plattan på mark; skriver `kontroll06.json` |
| `berakning.py` | Huvudskript: kör `berakning06.py` (om resultaten saknas), `kontroll06.py`, väggarna, byggskedet och glidning; skriver `resultat.json` |
| `figurer06.py` | Figurer: källaren, jordtryck, härdning, väggens sektion, tryck och sättning, bottenplattan, lokala detaljer |
| `rapport.py`, `rapport/mall.typ`, `rapport/projekt.json` | Bygger PDF:en |
| `validering/natkonvergens.py` | Bottenplattans nät 200 mm mot 140 mm |

Modulerna i `../K-05` används direkt (nät, laster, FE, EC2), så K-05 ska finnas bredvid och vara körd: K-06 läser K-05:s `resultat.json` och `falt.npz`.

## Köra

```
python berakning06.py          # L400 (omplint: räkna om plintarnas storlek)
python berakning.py            # kontroller, väggar, byggskede och resultat.json
python validering/natkonvergens.py
python rapport.py              # rapport/K-06_grund.pdf
```

`python berakning.py` kör själv `berakning06.py` om `res06_*.pkl` saknas. Figurer, `*.pkl`, `kontroll06.json` och PDF skapas i mappen och versionshanteras inte. Ritningarna R-04 (bottenplattan) och R-05 (källarstommen) och U-01 läser `indata.py` och `resultat.json`. K-06 är ett tungt steg i bygget: det räknas lokalt (`./bygg K-06`), och `resultat.json`, `räknat.json` (källornas kontrollsumma) och rapporten i `rapporter/` checkas in (se [`verktyg/bygg`](../../verktyg/bygg/)).

## Viktiga antaganden

- Sprängt berg med dränerad makadam, inget vattentryck. Fyllning 2,0 m mot de slutna fasaderna (V1 1,8 m), 1,8–0,8 m mot V14, 0,80 m mot fasaden med öppningarna, 1,75 m bakom V3 och V20 (fyllning och makadam upp till cellplasten under plattan på mark, 350 mm; fylls före mellanbjälklaget). Vilojordtryck $K_0 = 1 - \sin 40°$, 2,5 kN/m² på marken, och packningstryck 19 kPa (lätt vibroplatta inom 1 m från väggen).
- Väggarna: betongkärna C30/37 (Sundolitts B30), B500B, lodrät strimla mellan bottenplattan och bjälklaget; lodräta järn på insidan, den glesaste som räcker per vägg: Ø10 s200 där packningstrycket kräver det, annars Ø10 s300 (TG 2216). V3 bär byggskedet vågrätt med 2 Ø10 s300.
- Innerväggarna gjuts som ytterväggarna, det översta halva skiftet med bjälklaget, med lodräta järn Ø10 s300 i kärnans mitt i hela höjden. Inspänningen räknas med vridfjädrar 4EI/h i K-05:s modell (`innervaggar.py`).
- Återfyllning när $f_{ck}(t)$ ≥ 21 MPa, kravet avrundat uppåt till helt MPa (SS-EN 1992-1-1 3.1.2 och mognadsålder enligt bilaga B).
- Cellplast: $f_d = k_r f_{ck} / 1{,}3$, $E_k$ korttid och $0{,}4 E_k$ långtid. Källaren: S200 i det undre skiktet (100 mm i hela ytan innanför L-elementens fot, under plattan, innerväggarnas balkar och plintarna), S100 i det övre skiktet under plattan och S300 i L-elementen (foten under kantbalken; ytterkanten i väggens ytterliv) och i det undre skiktet i hörnet där balkarna under V4–V6 och V15 möts. Plattan på mark på plan 1: S100, och S300 i de två fria hörnen. Zonerna står i `indata.py` (`EPS_ZON`, `EPS_MARK_ZON`), och trycket kontrolleras per kvalitet.
- Kärnan: kryptal 2,0, krympning 0,30 mm/m (påtvingad, faktor 1,0).
