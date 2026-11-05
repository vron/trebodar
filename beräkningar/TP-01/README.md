# TP-01 rev A – Tidsplan och organisation

Byggets faser och steg från rivningens start (byggstart) till slutbesked, med tider, ansvarig och inblandade för varje steg, och byggets organisation (parterna med roll, uppgift och status). Handling till tekniskt samråd (dagordningens punkt 1, arbetets planering och organisation). Tiderna fram till gjutningen av mellanbjälklaget följer byggherrens etapplan och byggskedet i K-06; de senare är preliminära.

Faserna används också i inköpslistan IN-01: varje specialprodukt anger sin fas och ska finnas på bygget när fasen börjar. TP-01 visar specialprodukterna per fas, och IN-01 visar fasernas datum.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Projektuppgifter, uppehåll, parterna (`[[part]]`), faserna (`[[fas]]`) och stegen (`[[steg]]`: fas, namn, start, slut, ansvarig, förslag, inblandade, anmärkning, milstolpe, klar, preliminärt) |
| `bygg.py` | Läser `indata.toml` och IN-01:s indata, kontrollerar dem, ritar tidsplanerna (`fig_*.svg`) och bygger PDF |
| `mall.typ` | Typst-mall för dokumentet |

## Ändra

- **Ett datum, en ansvarig eller en ny part:** i stegets `[[steg]]` eller partens `[[part]]` i `indata.toml`; `prel = true` för preliminära datum, `forslag = true` när den ansvariga är ett förslag och `ansvarig = ""` när den inte är bestämd. Ändra `datum` i `[projekt]`.
- **En ny fas:** en `[[fas]]` i byggets ordning; IN-01:s produkter kan sedan ange den.
- Inga telefonnummer, e-postadresser eller personnummer: handlingen är publik.

## Köra

```
./bygg TP-01                  # i repots rot; IN-01 byggs om med de nya faserna
```

eller för hand:

```
pip install -r requirements.txt
python bygg.py
```

Resultat: `TP-01_tidsplan.pdf`. Den utgivna handlingen ligger i [`rapporter/`](../../rapporter/) och på webbplatsen.

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
