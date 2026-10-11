# K-06 rev A – Bottenplatta och källarväggar

Källarens väggar av Sundolitt Kub 350-150 (cellplast 100 + betongkärna 150 + cellplast 100, SINTEF TG 2216) mot jord, byggskedet innan mellanbjälklaget har gjutits (ordningsföljd, V3/V20 med fri överkant, betongens hållfasthet och härdningstid vid återfyllning) och bottenplattan på cellplast med kantbalkar i L-element (L300 eller L400), balkar under innerväggarna och plintar under rören. Bottenplattan, väggarnas kärna, rören och mellanbjälklaget (K-05) räknas i en gemensam FE-modell.

| Fil | Innehåll |
|---|---|
| `indata.py` | Mått, jord, fyllning per vägg, packningstryck (Ingold), Kub och armering, cellplast, S300 vid yttre hörn |
| `vaggar.py` | Väggarna: lodrät strimla med jord- och packningstryck och toppmoment, fasaden med öppningar, vertikal last, fogar, LD4_2, byggskedet (brottlinjeteori för V3/V20), hållfasthet och mognadsålder |
| `modell06.py` | Den samverkande FE-modellen: K-05:s mellanbjälklag, bottenplattan, väggarnas kärna och rören som fjädrar, laster, kärnans krympning |
| `snitt06.py` | Balkmoment och tvärkraft längs balkarna, cellplastens kraft innanför stansningssnitten, väggarnas last per meter |
| `berakning06.py` | Lastfall och omhyllande för L300 och L400, kort och lång styvhet; plintarnas storlek; skriver `res06_<utf>_<styvhet>.pkl` |
| `kontroll06.py` | Kontroller: cellplast, platta, balkar, plintar, mellanbjälklaget mot K-05:s armering, rörlaster, sättningar, plattan på mark; skriver `kontroll06.json` |
| `berakning.py` | Huvudskript: kör `berakning06.py` (om resultaten saknas), `kontroll06.py`, väggarna, byggskedet och glidning; skriver `resultat.json` |
| `figurer06.py` | Figurer: källaren, jordtryck, härdning, väggens sektion, tryck och sättning, bottenplattan, lokala detaljer |
| `rapport.py`, `rapport/mall.typ`, `rapport/projekt.json` | Bygger PDF:en |
| `validering/natkonvergens.py` | Bottenplattans nät 200 mm mot 140 mm |

Modulerna i `../K-05` används direkt (nät, laster, FE, EC2), så K-05 ska finnas bredvid och vara körd: K-06 läser K-05:s `resultat.json` och `falt.npz`.

## Köra

```
python berakning06.py          # L300 och L400 (omplint: räkna om plintarnas storlek)
python berakning.py            # kontroller, väggar, byggskede och resultat.json
python validering/natkonvergens.py
python rapport.py              # rapport/K-06_grund.pdf
```

`python berakning.py` kör själv `berakning06.py` om `res06_*.pkl` saknas. Figurer, `*.pkl`, `resultat.json`, `kontroll06.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

## Viktiga antaganden

- Sprängt berg med dränerad makadam, inget vattentryck. Fyllning 2,0 m mot de slutna fasaderna (V1 1,8 m), 1,8–0,8 m mot V14, 0,80 m mot fasaden med öppningarna, 1,7 m bakom V3 och V20 (plattan på mark, fylls före mellanbjälklaget). Vilojordtryck $K_0 = 1 - \sin 40°$, 2,5 kN/m² på marken, och packningstryck 19 kPa (lätt vibroplatta inom 1 m från väggen).
- Väggarna: betongkärna C30/37 (Sundolitts B30), B500B, lodrät strimla mellan bottenplattan och bjälklaget; lodräta järn Ø10 s200 på insidan. V3 bär byggskedet vågrätt med 2 Ø10 s300.
- Återfyllning när $f_{ck}(t)$ ≥ 20 MPa (SS-EN 1992-1-1 3.1.2 och mognadsålder enligt bilaga B).
- Cellplast: $f_d = k_r f_{ck} / 1{,}3$, $E_k$ korttid och $0{,}4 E_k$ långtid. S100 under plattan, S200 under balkar och plintar, S300 vid de yttre hörnen.
- Kärnan: kryptal 2,0, krympning 0,30 mm/m (påtvingad, faktor 1,0).
