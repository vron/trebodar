# U-03 rev A – Takets luftspalt, luftflöde, fukt och mögelrisk

Eget underlag, ingår inte i handlingarna till tekniskt samråd (F-01 avsnitt 6). Luftspalten mellan råsponten och den hårda träfiberskivan går obruten från takfot över nockar och dalar till takfot, som längst 16,3 m. Hela taket räknas som ett nätverk: en remsa per fack (c/c 600) längs y, noder vid nockar, dalar och takfönstrens kanter, takfall mellan noderna och, i vissa fall, omluftning runt takfönstren, kanaler längs nockar och dalar och öppningar i gavlarna. Luftflöde (vind och termisk stigkraft), temperaturer, fukt i råsponten och träfiberskivan och mögelindex (VTT) räknas timme för timme med ERA5-klimat för Resö 2013–2023. Badrummet räknas med högre fukttillskott i sin del av taket.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Takets geometri (fasadliv, gavlar, takfötter, takfönster, gavelöppningar), uppbyggnad, ångbroms, inneklimat och badrum, strömning, vindtryck, fuktdata, mögelmodell, klimatfil och fall |
| `geometri.py` | Nätverket: remsor, noder, takfall, takfönster, omluftning, kanaler längs nockar och dalar, gavelöppningar |
| `modell.py` | Klimat, vindtryck, luftflöde (Newton), värme och fukt per cell, blandning i noderna, VTT |
| `berakning.py` | Huvudskript: alla fall parallellt, sammanställning, figurer, `resultat.json` och PDF |
| `mall.typ` | Typst-mall för dokumentet |
| `klimat_era5.csv.gz` | Timvärden 2013-07 – 2023-12 från ERA5 (Open-Meteo, CC BY 4.0) för 58,80 N, 11,25 E |

Geometrin är tagen ur K-03:s `geometri.json` (nock- och dalbalkar, takbalkarnas ändar, takfönster) och K-05 (fasadliv och gavlar), husets riktning ur AR-02 och badrummet ur planritning 201 rev 02. Beräkningen läser inte modellen.

## Köra

```
pip install -r requirements.txt
python berakning.py            # alla 43 fall parallellt (högst 12 processer, ca 1,5 h), figurer, resultat.json, PDF
python berakning.py rapport    # bara figurer och PDF ur sparade resultat
python berakning.py fall bas   # bara angivna fall
```

Resultat: `U-03_takets_luftspalt.pdf`. Ändra bara i `indata.toml` för att räkna om. Fallens resultat sparas i `resultat/` (`*.npz`). Figurer (`fig_*.svg`), `resultat/`, `resultat.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
