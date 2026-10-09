# K-06 rev A – Bottenplatta och källarväggar

Källarens ytterväggar mot jord av isolerade lättklinkerblock, 350 mm, i två system (A: Leca Isoblokk 35 från Leca Norge, B: LECA Isoblock 350 PUR från Benders), och bottenplattan på cellplast med kantbalkar i L-element (L300 eller L400), balkar under innerväggarna och plintar under rören. Bottenplattan, Lecaväggarna, rören och mellanbjälklaget (K-05) räknas i en gemensam FE-modell, så att skillnaden i sättning mellan rör och väggar ingår.

| Fil | Innehåll |
|---|---|
| `indata.py` | Mått, jord och fyllning per vägg, systemen A och B (EKS avdelning H), cellplast (EPS-Sverige), Lecans styvhet, krympning och krypning, zonen med S300 |
| `vaggar.py` | Väggarna mot jord: brottlinjeteori med jordtryck och fyllning längs väggen, vågrätt och lodrätt moment, stålstolpar, vertikal last, reaktioner |
| `modell06.py` | Den samverkande FE-modellen: K-05:s mellanbjälklag, bottenplattan med balkar och plintar på cellplast, väggar och rör som fjädrar, laster, Lecans krympning. Variant där också den yttre vangen bär och lasterna över väggarna står där de står |
| `snitt06.py` | Balkmoment och tvärkraft längs balkarna, cellplastens kraft innanför stansningssnitten, väggarnas last per meter |
| `berakning06.py` | Lastfall och omhyllande för ett utförande och en styvhet (kort/lång); plintarnas storlek; skriver `res06_<utf>_<styvhet>[_ytter].pkl` |
| `kontroll06.py` | Kontroller: cellplast, platta, balkar, plintar, mellanbjälklaget mot K-05:s armering, rörlaster, sättningar, plattan på mark; skriver `kontroll06.json` |
| `berakning.py` | Huvudskript: kör `berakning06.py` (om resultaten saknas) och `kontroll06.py`, väggarna och glidning; skriver `resultat.json` |
| `figurer06.py` | Figurer: källaren, kapacitetskurvor, sektioner A och B, tryck och sättning, bottenplattan, lokala detaljer |
| `rapport.py`, `rapport/mall.typ`, `rapport/projekt.json` | Bygger PDF:en |
| `validering/natkonvergens.py` | Bottenplattans nät 200 mm mot 140 mm |

Modulerna i `../K-05` används direkt (nät, laster, FE, EC2), så K-05 ska finnas bredvid och vara körd: K-06 läser K-05:s `resultat.json`, `falt.npz` och `ytterskikt.json`.

## Köra

```
pip install -r requirements.txt
python berakning06.py          # grundmodellen, L300 och L400, cirka 8 min
python berakning06.py ytter    # varianten med båda vangarna, cirka 4 min
python berakning.py            # kontroller och resultat.json
python validering/natkonvergens.py
python rapport.py              # rapport/K-06_grund.pdf
```

`python berakning.py` kör själv `berakning06.py` om `res06_*.pkl` saknas. Typsnittet Carlito ska finnas i `/usr/share/fonts`. Figurer, `*.pkl`, `resultat.json`, `kontroll06.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

## Viktiga antaganden

- Sprängt berg med dränerad makadam, inget vattentryck. Fyllning 2,0 m mot de slutna fasaderna, 1,8–0,8 m mot V14, 1,41–1,52 m mot V18 (avsatsen), 0,80 m mot fasaden med öppningarna (hel under fönstren, räknas med fri överkant), 1,7 m bakom V3 och V20 (plattan på mark). Vilojordtryck $K_0 = 1 - \sin 40°$, 2,5 kN/m² på marken.
- Murverk: EKS tabell H-1 ($\gamma_M$ = 2,1, kategori I, utförandeklass II), armering $\gamma_M$ = 1,3. System A räknas med samverkande vangar (Sikksakk), system B med vangarna var för sig.
- Cellplast: $f_d = k_r f_{ck} / 1{,}3$, $E_k$ korttid och $0{,}4 E_k$ långtid. S100 under plattan, S200 under balkar och plintar, S300 vid hörnet V2/V20 (L300).
- Lecan: $E = 1\,000 f_k$, kryptal 2,0, krympning 0,40 mm/m (påtvingad, faktor 1,0).
- Resultaten är omhyllande av korttids- och långtidsstyvhet och av grundmodellen och varianten där båda vangarna bär.
