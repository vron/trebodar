# IN-01 rev A – Inköpslista

Specialprodukterna: det som väljs, beställs eller tillverkas för sig (vitvaror, fönster och dörrar, kaminen, armaturerna, specialtillverkat stål och limträ …), med vald produkt, status, ansvarig roll och skede. Vanligt material (virke, skivor, isolering, armering, kabel, rör) ingår inte. Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6).

Listan följer husets modell: varje specialprodukt är märkt där den skapas i modellens geometriskript (`produkt="KOD"` på delen eller montaget, för installationernas produkttyper `produkt` i katalogen), och antalet och instansernas id (fönstret 3NV-F4, armaturen KO-L05, plåten 2SV-P01) kommer ur modellen. Här står det som inte är geometri. En produkt som inte är modellerad (borrhålet, badrummets sanitet) anger sin omfattning i stället.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Projektuppgifter, status, roller, skeden och produkterna (`[[produkt]]`: kod, grupp, namn, vald produkt, status, ansvarig, skede, dokument, ärenden, anmärkning) |
| `bygg.py` | Läser `indata.toml` och modellens utdrag, kontrollerar att de stämmer och bygger PDF |
| `mall.typ` | Typst-mall för dokumentet |

## Ändra

- **Status, vald produkt, leverantör, ansvarig:** i produktens `[[produkt]]` i `indata.toml`. Status är någon av `[status]` (att välja, vald, offert, beställd, levererad, monterad); utom vid "att välja" anger `vald` produkten. Ändra `datum` i `[projekt]`.
- **En ny specialprodukt:** märk den i modellen där den skapas och lägg till en `[[produkt]]` med samma kod. `./mod kontroll`, `./mod inkop` och `bygg.py` stoppar när en kod finns på det ena stället men inte på det andra.
- **En vald produkt:** byt också modellens allmänna typ ("ej vald") mot produktens mått; listan anmärker annars att modellen visar en allmän typ.

## Köra

```
./bygg IN-01                                          # i repots rot: utdraget ur modellen och PDF
```

eller för hand:

```
cd ../../verktyg/modellering && ./mod inkop utdrag    # modeller/trebodar/ut/inkop.json
cd - && python bygg.py
```

Resultat: `IN-01_inkopslista.pdf`. Den utgivna listan ligger i [`rapporter/`](../../rapporter/) och på webbplatsen.

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
