# K-05 rev A – Mellanbjälklag och källarpelare

Kontroll av det platsgjutna mellanbjälklaget, 150 mm, och källarens stålrör, VKR 80×80×4, enligt EKS 12 och SS-EN 1992-1-1 / 1993-1-1. Plattan räknas med finita element med verklig geometri, Lecaväggar, rör, plattan på mark och alla laster från trästommen på plan 1 (K-01, ytterväggar, tak på takfotsväggar, trappa).

| Fil | Innehåll |
|---|---|
| `bild/geometri.json` | Geometri: plattans kontur och trapphål, Lecaväggar och upplagslinjer, rör, platta på mark, fria kanter, stolparnas lägen på plan 1 och linjelasten från dalbalk 2 |
| `bild/geometri.py` | Uppmätning av väggar och rör ur Onshape-skärmbilderna `kallare.png` och `plan1.png`. Uppdaterar bara de uppmätta posterna i `geometri.json` |
| `laster.py` | Alla laster: utbredda laster (F-01), punktlaster LN/LD/LA ur K-01 och gaveltakstolarna, ytterväggar qY1–qY12, qD2, trappan qT, vindlyft. Indata överst i filen |
| `platta.py` | FE för plattor (DKT-element): nät med lokal förfining, stöd (linje, rör som fjäder, bädd), laster, moment, reaktioner, Wood–Armer |
| `ec2.py` | Material och kontroller enligt SS-EN 1992-1-1 med EKS; rörens knäckning |
| `analys.py` | Långtidsnedböjning med sprickbildning och krympning element för element |
| `modell.py` | Bygger FE-modellen ur `geometri.json` och `laster.py`. Laster över Lecaväggar läggs på väggens upplagslinje |
| `omhyllande.py` | Omhyllande moment, tvärkraft och rörlaster för alla kombinationer, nyttig last i mönster, mjuka och styva rör, styva rör med fjädrande Lecaväggar, vindlyft |
| `tvarkraft.py` | Tvärkraft genom kontrollsnitt ur FE-modellen |
| `kontroll.py` | Handberäkning (belastningsytor, strimlor) och jämförelse med SINTEF 522.871 tabell 24a |
| `berakning.py` | Huvudskript: alla kontroller, tilläggsjärn, utförande vid varje rör, reaktioner på väggarna; skriver `resultat.json` |
| `figurer.py` | Figurer: geometri, laster, tvärsnitt, armering, moment, nedböjning |
| `golvvarme.py` | Bilaga A: golvvärme, stationär värmeledning i ett tvärsnitt |
| `ta_bort.py` | Prövar vad som händer om rör tas bort (`python ta_bort.py 2,6,13`) |
| `rapport.py`, `rapport/mall.typ` | Bygger PDF:en |
| `validering/` | FE-modellen mot Navier, Timoshenko (platta på pelarnät) och en strimla med sprickbildning; känslighet för sättning av rören (`sattning.py`); lastvägen över Lecaväggarnas två skikt (`ytterskikt.py`), nätkonvergens (`konvergens.py`) och väggarna som fjädrar (`vaggande.py`); kör dem före `rapport.py` |

## Köra

```
pip install -r requirements.txt
python laster.py          # lastsammanställning
python validering/ytterskikt.py   # behövs av berakning.py (zonen vid LD4_2)
python berakning.py       # cirka 8 min
python validering/ytterskikt.py   # igen, för zonernas namn
python validering/konvergens.py
python validering/vaggande.py    # cirka 10 min
python rapport.py         # rapport/K-05_mellanbjalklag.pdf
```

Typsnittet Carlito ska finnas i `/usr/share/fonts` (Debian/Ubuntu: `fonts-crosextra-carlito`). Figurer, `resultat.json`, `*.npz` och PDF skapas i mappen och versionshanteras inte. Den utgivna rapporten ligger i [`rapporter/`](../../rapporter/).

## Viktiga antaganden

- Betong C25/30, B500B. Nät Ø10 s150 i underkant (täckskikt 20 mm) och Ø8 s150 i överkant (täckskikt 25 mm).
- Ytterväggarnas upplagslinje ligger 75 mm in från väggens insida; plattan går till 30 mm från Lecans ytterliv.
- Laster från plan 1: K-01:s stödreaktioner; gavlarnas nockbalksändar via takstolar till hörnen; takfotsväggar bär halva takbalken plus 0,2 m utsprång; ytterväggar 0,6 kN/m²; trappan hänger på hålets kortsida.
- Lätta mellanväggar 0,7 kN/m² som nyttig last i brottgräns och permanent last i bruksgräns.
- Momenttoppar utjämnas över 250 mm; stödmoment i överkant × 1,2 när zonerna avgränsas och tilläggsjärnen dimensioneras för 1,5 × FE (stela upplagslinjer ger nätberoende toppar vid väggändar).
- Genomstansning: hela lasten på varje rör och stolpe på eget snitt 2d, β 1,15 (1,4 vid trapphålet), ρ ur överkantsarmeringen, för rören också FE-modellens lokala tvärkraft; minst 5 % marginal och ≤ 100 % med armeringen 10 mm för lågt. Nettokraften ur jämvikt redovisas bara som information. P7 har topplåt 160×160×25 S355.
- Rören räknas med verklig axialstyvhet, som styva och som styva med Lecaväggarna som fjädrar (E = 2 000 MPa); det ogynnsammaste resultatet används. Rören vid trapphålet står 100 mm från hålkanten.
