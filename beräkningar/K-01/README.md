# K-01 rev C – Nock- och dalbalkar

Dimensionering av de fem nock- och dalbalkarna (nockbalk 1, 3, 5 och dalbalk 2, 4) som stål–trä-komposit enligt EKS 12 och SS-EN 1990/1991/1993/1995.

| Fil | Innehåll |
|---|---|
| `indata.toml` | All indata: geometri, material, skruv, lim, laster (snö, egenvikt, vind), temperaturfall, balkar med spann, stöd och plåtlägen |
| `analys.py` | FE för balk med partiell samverkan (SS-EN 1995-1-1 9.1.3), elementvisa tvärsnitt med och utan plåt, lastfall och modeller (förankrade stöd, lyftande stöd, fritt upplagda fält), stolpe med dubbeltriangel |
| `berakning.py` | Huvudskript: kör analyserna, dimensionerar skruvzoner, kontrollerar stål, limträ, stöd och stolpe, skriver hålbilder och `resultat.json`, bygger PDF |
| `figurer.py` | Tvärsnitt, skruvbild i plan, temperaturprincip och översikt per balk (M, V, skruvzoner) |
| `mall.typ` | Typst-mall för dokumentet |
| `halbild_*.csv` | Hålbild per plåtbit för laserskärning (genereras av `berakning.py`) |

Kör: `python berakning.py` → `nock_och_dalbalkar_K-01.pdf`.
