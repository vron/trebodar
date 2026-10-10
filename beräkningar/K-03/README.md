# K-03 rev A – Takbalkar, takstolar och stolpar

Takets bärande delar utom nock- och dalbalkarna (K-01): takbalkarna 45×170 c/c 600 med takfönster och upplag mot balkarna, de sju takstolarna och alla stolpar under nock- och dalbalkar och takstolar ner till bjälklaget, med huvudstolpen LN1_3 (stolpen med dubbeltriangel under nockbalk 1). Enligt EKS 12 och SS-EN 1995-1-1. Väggarnas reglar, hammarband och avväxlingar och den horisontella stabiliseringen redovisas i K-04.

| Fil | Innehåll |
|---|---|
| `indata.toml` | Material, laster (F-01), takbalkstyper, upplag, takfönster, takstolar (vilket stöd i K-01 de bär), spikplåtar, toppklossar och stolpar med krav där modellen inte räcker. Huvudstolpens krafter ur K-01 |
| `geometri.json` | Geometrin: takbalkar, takfönster, takstolar, stolpar och väggar, koordinater som i K-05. K-03:s egen källfil, kontrollerad mot modellen med `verktyg/modellanalys/kontroll_k03.py` |
| `berakning.py` | Huvudskript: takbalkar per typ, hak och upplag, takfönster, takstolar, stolpar, brister i modellen, `resultat.json`, PDF |
| `figurer03.py` | Översikt i plan, takbalkens upplag, takstolen L2M och huvudstolpen |
| `mall.typ` | Typst-mall för dokumentet |

Stolparnas laster läses ur K-05 (`../K-05/laster.py`), som bygger på K-01:s stödreaktioner. Takstolarnas last i toppen är samma stödreaktioner. Huvudstolpens $N_d$ och $M_d$ står i `indata.toml` och kommer från K-01, där stolpens böjstyvhet ingår. Ändras huvudstolpen ska K-01 räknas om med samma tvärsnitt.

## Köra

```
python berakning.py
```

Resultat: `K-03_takbalkar_takstolar_stolpar.pdf`. Figurer (`fig_*.svg`), `resultat.json` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

Typsnittet Carlito läses från systemet eller från `beräkningar/.fonts`.
